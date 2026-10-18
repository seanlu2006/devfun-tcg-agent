#!/usr/bin/env python3
"""Owner-hosted 執行器：在自己的電腦上跑 agent，跟平台一問一答地打比賽。

TCG Playground S3 是 owner-hosted（executionMode＝remote），不是上傳 bundle：
  加入（附牌組）→ 每秒詢問 pending-actions → 用 harness/strategy.py 的 act() 決定 → 送出 action
  → 一場打完（Settled/Aborted）→ 還沒到 --max-matches 就再加入 → …

⚠️ 牌組在「第一次加入」時就整季鎖定，之後不能換。第一次真的加入前要確定牌組。
⚠️ 對戰進行中不要直接關掉：沒回應會超時判輸。按一次 Ctrl-C ＝「打完這場就停」；連按兩次才會立刻離開。

用法：
  python3 tools/run_agent.py --deck decks/xxx.json --max-matches 3      第一次加入（會鎖定牌組）
  python3 tools/run_agent.py --max-matches 10                           之後再打（牌組已鎖定，不用再給）
  python3 tools/run_agent.py --base http://127.0.0.1:8765/api/arena ...  連本機模擬伺服器（tests/mock_arena.py）
  python3 tools/run_agent.py --max-matches 40 --ab <commit 或分支>        A/B：目前版本（A）和指定版本（B）一場一場輪流上場

為什麼要 A/B：平台按實力配對，不同時段碰到的對手強度差很多（2026-10-19 檢討：對手分數中位數 351→520），
所以「這批勝率 vs 上一批勝率」不能比。同一時段輪流上場，兩邊碰到的對手才一樣，結果用 tools/ab_report.py 看。
"""
import argparse
import hashlib
import importlib.util
import subprocess
import json
import signal
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import arena_client as ac  # noqa: E402
from validate_deck import expand, validate  # noqa: E402

RUN_DIR = ROOT / "data" / "runs"
DEADLINE_MARGIN_MS = 1500   # 離截止不到 1.5 秒就不想了，直接送保底動作
STOP_ERRORS = {"engine_match_allowance_exhausted", "competition_closed"}
TRANSIENT_ERRORS = {"arena_transaction_busy", "engine_submission_version_busy"}
# 對戰中的詢問／送出動作：一個決策點只有約 48 秒，連線卡住不能等到 60 秒（2026-10-18 第 23 批：
# 439086cb 第 17 步沒送出去，被判超時輸）。逾時會回 status 0，照暫時性錯誤重試
REQUEST_TIMEOUT = 10


def version_info(deck):
    """這次執行用的版本：git commit、策略檔雜湊、牌組雜湊。每場都記下來，檢討時才能按版本分組
    （Codex 審查：以前多個版本的對戰混在一起，分不出哪個修正有效）。"""
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                             text=True, timeout=10).stdout.strip() or "unknown"
        dirty = subprocess.run(["git", "status", "--porcelain", "harness/strategy.py"], cwd=ROOT,
                               capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        sha, dirty = "unknown", ""
    strategy_hash = hashlib.sha256((ROOT / "harness" / "strategy.py").read_bytes()).hexdigest()[:10]
    deck_hash = hashlib.sha256(json.dumps(deck or []).encode()).hexdigest()[:10]
    return {"git": sha + ("+未commit" if dirty else ""), "strategy": strategy_hash, "deck": deck_hash}


def load_strategy(path=None, name="strategy"):
    spec = importlib.util.spec_from_file_location(name, path or ROOT / "harness" / "strategy.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_ab_strategy(ref):
    """把某個 commit／分支的 harness/strategy.py 取出來載入（B 組）。回傳 (module, 版本資訊)。"""
    sha = subprocess.run(["git", "rev-parse", "--short", ref], cwd=ROOT, capture_output=True, text=True,
                         timeout=10).stdout.strip()
    source = subprocess.run(["git", "show", f"{ref}:harness/strategy.py"], cwd=ROOT, capture_output=True,
                            timeout=10).stdout
    if not sha or not source:
        sys.exit(f"--ab {ref}：找不到這個版本的 harness/strategy.py")
    # 放在 repo 根目錄下一層：strategy.py 用「自己所在資料夾/../assets/catalog.json」找卡牌資料
    path = ROOT / ".ab_strategies" / f"strategy_{sha}.py"
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(source)
    module = load_strategy(path, f"strategy_{sha}")
    if not module.CARDS:
        sys.exit(f"--ab {ref}：B 組讀不到卡牌資料（catalog），不能上場")
    return module, {"git": sha, "strategy": hashlib.sha256(source).hexdigest()[:10]}


def is_transient(status, code):
    return status == 0 or status >= 500 or code in TRANSIENT_ERRORS


class Runner:
    def __init__(self, args):
        self.args = args
        self.key = ac.load_credentials()["apiKey"]
        self.strategy = load_strategy()
        self.state = ac.load_state()
        self.state.setdefault("matches", [])
        self.matches_done = 0
        self.stop_after_match = False
        RUN_DIR.mkdir(parents=True, exist_ok=True)
        self.log_path = RUN_DIR / f"run_{time.strftime('%Y%m%d_%H%M%S')}.jsonl"
        self.obs_path = self.log_path.with_name(self.log_path.stem + "_obs.jsonl")
        self.version = version_info(self.state.get("deck"))
        # A/B：每場第一次出現時決定用哪一組，A、B 輪流（self.arms[matchId] = "A" 或 "B"）
        self.arms, self.ab = {}, None
        if args.ab:
            module, info = load_ab_strategy(args.ab)
            self.ab = {"A": (self.strategy, dict(self.version, arm="A")),
                       "B": (module, dict(self.version, **info, arm="B"))}
        # 檢討工具要知道哪一邊是我們：記 agentId 到狀態檔，之後就不用再去讀金鑰檔
        agent_id = ac.load_credentials().get("agentId")
        if agent_id and self.state.get("agentId") != agent_id:
            self.state["agentId"] = agent_id
            ac.save_state(self.state)

    def arm(self, match_id):
        """這場用哪一組（沒開 A/B 就是 None）。輪流分配，兩組場數最多差 1。"""
        if not self.ab:
            return None
        if match_id not in self.arms:
            self.arms[match_id] = "AB"[len(self.arms) % 2]
        return self.arms[match_id]

    def strategy_for(self, match_id):
        arm = self.arm(match_id)
        return self.ab[arm][0] if arm else self.strategy

    def version_for(self, match_id):
        arm = self.arm(match_id)
        return self.ab[arm][1] if arm else self.version

    def log(self, **event):
        event["t"] = time.strftime("%H:%M:%S")
        with self.log_path.open("a") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def call(self, method, path, body=None, timeout=60):
        return ac.request(method, path, body, key=self.key, timeout=timeout)

    # ---------------------------------------------------------------- 加入
    def join(self):
        body = {"competitionId": ac.COMPETITION_ID}
        if self.state.get("deck_locked") and self.state.get("deck"):
            # 官方說明檔說重新加入不用再帶牌組，但伺服器實際上每次都要（2026-10-17 實測 422）→ 帶已鎖定的同一副
            body["joinPayload"] = self.state["deck"]
        elif not self.state.get("deck_locked"):
            if not self.args.deck:
                sys.exit("還沒加入過這一季：第一次要用 --deck 指定牌組（會整季鎖定）")
            deck = json.loads(Path(self.args.deck).read_text())
            errors, _ = validate(deck)
            if errors:
                sys.exit("牌組不合法：" + "；".join(errors))
            body["joinPayload"] = expand(deck)
        for attempt in range(12):
            status, data = self.call("POST", "/tcg/join", body)
            code = data.get("error") or data.get("code")
            # 暫時性錯誤：409 arena_transaction_busy（資料庫忙碌）、5xx、斷線／逾時（status 0）→ 等一下再試
            if is_transient(status, code):
                time.sleep(min(2 * (attempt + 1), 15))
                continue
            break
        if is_transient(status, code):
            print(f"加入一直失敗（{data}），先停下來；網路恢復後重新執行即可")
            return False

        if status == 409 and code == "payload_locked":
            self.state["deck_locked"] = True       # 之前已經鎖定了：不帶牌組再加入一次
            ac.save_state(self.state)
            return self.join()
        if code in STOP_ERRORS:
            print(f"停止：{code}（{data.get('message', '')}）")
            return False
        if status >= 300:
            sys.exit(f"加入失敗（HTTP {status}）：{data}")

        if "joinPayload" in body and not self.state.get("deck_locked"):
            self.state.update(deck_locked=True, deck=body["joinPayload"], deck_name=Path(self.args.deck).stem)
            ac.save_state(self.state)
            print(f"已用牌組 {Path(self.args.deck).stem} 加入，這一季的牌組已鎖定。")
        print(f"加入：{data.get('status')}" + (f"，對戰 {data.get('matchId')}" if data.get("matchId") else "，排隊中…"))
        if data.get("matchId"):
            print(f"  觀戰：https://arena.dev.fun/tcg-playground/match/{data.get('matchId')}")
        self.log(event="join", status=data.get("status"), matchId=data.get("matchId"), version=self.version)
        return True

    # ---------------------------------------------------------------- 回答一個決策點
    def answer(self, pending):
        legal = pending.get("legalActions") or []
        strategy = self.strategy_for(pending["matchId"])
        context = {"observation": pending.get("obs") or {}, "legalActions": legal}
        started = time.time()
        deadline = pending.get("deadline") or 0
        if deadline and deadline - time.time() * 1000 < DEADLINE_MARGIN_MS:
            action = strategy.safe_default(legal)
        else:
            action = strategy.act(context)
        status, data = self.post_action(pending, action)
        if status == 422:  # 不合法：重讀這個決策點、送保底動作一次
            action = strategy.safe_default(legal)
            status, data = self.post_action(pending, action)
        select = (context["observation"].get("select") or {})
        self.log(event="action", matchId=pending["matchId"], seq=pending["seq"], action=action,
                 select=[select.get("type"), select.get("context")], legal=len(legal),
                 ms=round((time.time() - started) * 1000), http=status, matchStatus=data.get("matchStatus"))
        # 完整盤面（含自己的手牌）另存一份：公開紀錄會把手牌遮掉，這是之後改策略唯一看得到手牌的資料
        with self.obs_path.open("a") as f:
            f.write(json.dumps({"matchId": pending["matchId"], "seq": pending["seq"], "action": action,
                                "legalActions": legal, "obs": context["observation"]}, ensure_ascii=False) + "\n")
        return data.get("matchStatus")

    def post_action(self, pending, action):
        """送出動作；遇到暫時性錯誤就用「同一個 (matchId, seq, action)」重送（伺服器對同一組是冪等的），
        但不能拖過截止時間。"""
        body = {"matchId": pending["matchId"], "seq": pending["seq"], "action": action}
        for attempt in range(4):
            status, data = self.call("POST", "/tcg/action", body, timeout=REQUEST_TIMEOUT)
            if not is_transient(status, data.get("error") or data.get("code")):
                return status, data
            deadline = pending.get("deadline") or 0
            if deadline and deadline - time.time() * 1000 < 1000:
                break
            time.sleep(0.5 * (attempt + 1))
        return status, data

    def finish_match(self, match_id, match_status):
        self.matches_done += 1
        self.state["matches"].append({"matchId": match_id, "status": match_status,
                                      "at": time.strftime("%Y-%m-%d %H:%M:%S"),
                                      "version": self.version_for(match_id)})
        ac.save_state(self.state)
        print(f"第 {self.matches_done} 場結束（{match_status}）：{match_id}")
        self.log(event="match_end", matchId=match_id, status=match_status, arm=self.arm(match_id))

    # ---------------------------------------------------------------- 主迴圈
    def should_stop(self):
        return self.stop_after_match or self.matches_done >= self.args.max_matches

    def match_status(self, match_id):
        _, data = self.call("GET", f"/tcg/battle/{match_id}")
        return data.get("status")

    def run(self):
        if not self.join():
            return
        tracked, finished = set(), set()   # 看過的進行中對戰／已經算過的對戰
        last_join = time.time()
        while True:
            status, data = self.call("GET", f"/tcg/pending-actions?competitionId={ac.COMPETITION_ID}",
                                     timeout=REQUEST_TIMEOUT)
            if status == 0 or status >= 300:
                print(f"  詢問失敗（HTTP {status}）：{data}，2 秒後重試")
                time.sleep(2)
                continue
            pending = data.get("pending") or []
            active = {m if isinstance(m, str) else m.get("matchId") for m in data.get("activeMatches") or []}
            active |= {p["matchId"] for p in pending}

            ended = []
            for p in sorted(pending, key=lambda p: p.get("deadline") or 0):
                result = self.answer(p)
                if result in ("Settled", "Aborted") and p["matchId"] not in finished:
                    ended.append((p["matchId"], result))
            # 在對手那一步結束的對戰：我們收不到結束回應，只會看到它從清單消失 → 主動查結果
            for match_id in tracked - active - finished - {m for m, _ in ended}:
                result = self.match_status(match_id)
                if result in ("Settled", "Aborted"):
                    ended.append((match_id, result))
            for match_id, result in ended:
                finished.add(match_id)
                self.finish_match(match_id, result)
            tracked = (tracked | active) - finished

            if ended or (not active and time.time() - last_join > 3):
                if self.should_stop() and not active - finished:
                    print(f"已打完 {self.matches_done} 場，停止（沒有再加入）。")
                    return
                if not self.should_stop():
                    if not self.join():   # 排隊中重複加入不會失去位置（官方說明）
                        return
                    last_join = time.time()
            if not pending:
                time.sleep(self.args.poll)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--deck", help="第一次加入用的牌組（會整季鎖定）")
    parser.add_argument("--max-matches", type=int, default=3, help="打幾場就停（預設 3）")
    parser.add_argument("--poll", type=float, default=1.0, help="詢問間隔秒數（預設 1）")
    parser.add_argument("--base", help="改連別的伺服器（例如本機模擬伺服器）")
    parser.add_argument("--state", help="改用別的狀態檔（測試用，避免動到真正的 .arena-tcg-state）")
    parser.add_argument("--credentials", help="改用別的金鑰檔（測試用）")
    parser.add_argument("--ab", help="A/B 測試：這個 commit／分支當 B 組，跟目前版本（A 組）一場一場輪流上場")
    parser.add_argument("--log-dir", help="記錄檔改寫到別的資料夾（測試用，避免混進真實對戰紀錄）")
    args = parser.parse_args()
    if args.base:
        ac.BASE = args.base.rstrip("/")
    if args.state:
        ac.STATE = Path(args.state)
    if args.credentials:
        ac.CREDENTIALS = Path(args.credentials)
    if args.log_dir:
        global RUN_DIR
        RUN_DIR = Path(args.log_dir)
    runner = Runner(args)

    def on_sigint(signum, frame):
        if runner.stop_after_match:
            print("\n立刻離開（進行中的對戰可能會超時判輸）")
            sys.exit(1)
        runner.stop_after_match = True
        print("\n收到 Ctrl-C：打完這一場就停（再按一次會立刻離開）")
    signal.signal(signal.SIGINT, on_sigint)

    print(f"記錄檔：{runner.log_path}｜版本 {runner.version}"
          + (f"｜A/B：B 組 {runner.ab['B'][1]}" if runner.ab else ""))
    runner.run()


if __name__ == "__main__":
    main()
