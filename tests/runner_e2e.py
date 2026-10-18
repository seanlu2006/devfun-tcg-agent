#!/usr/bin/env python3
"""執行器端到端測試：對本機模擬伺服器跑 tools/run_agent.py，不碰真正的比賽、不動真正的狀態檔。

檢查：
  1. 設定 --max-matches 2 → 剛好打完 2 場就停，不會加入第 3 場
  2. 「在對手那一步結束」的那場也有被算進去（雙數場）
  3. 送出的每個動作都合法、沒有被伺服器拒絕
  4. 狀態檔記下牌組已鎖定；第二次執行不帶 --deck 也能加入（不會被 payload_locked 卡住）
  5. --ab：兩場分別記成 A 組、B 組，B 組記的是指定的舊版 commit；狀態檔記下 agentId
用法：python3 tests/runner_e2e.py
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
import mock_arena  # noqa: E402


def run_agent(base, tmp, extra):
    cmd = [sys.executable, "-I", str(ROOT / "tools" / "run_agent.py"), "--base", base, "--poll", "0.05",
           "--state", str(tmp / "state.json"), "--credentials", str(tmp / "cred.json"),
           "--log-dir", str(tmp / "runs")] + extra
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)


def main():
    failures = []
    arena, server = mock_arena.start()
    base = f"http://127.0.0.1:{server.server_address[1]}/api/arena"
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        (tmp / "cred.json").write_text(json.dumps({"apiKey": "mock-key", "agentId": "mock-agent"}))

        first = run_agent(base, tmp, ["--deck", str(ROOT / "decks" / "starter_dark.json"), "--max-matches", "2"])
        print(first.stdout.strip())
        if first.returncode != 0:
            failures.append(f"第一次執行失敗：{first.stderr.strip()[-500:]}")
        if arena.match_no != 2:
            failures.append(f"應該剛好開 2 場，實際開了 {arena.match_no} 場")
        if any(arena.status[f"mock-match-{i}"] != "Settled" for i in (1, 2)):
            failures.append(f"兩場都應該打完：{arena.status}")
        expected_actions = 2 * len(arena.script)
        if len(arena.actions) != expected_actions:
            failures.append(f"應該送出 {expected_actions} 個動作，實際 {len(arena.actions)}")
        state = json.loads((tmp / "state.json").read_text())
        if not state.get("deck_locked") or len(state.get("matches", [])) != 2:
            failures.append(f"狀態檔不對：deck_locked={state.get('deck_locked')}、matches={len(state.get('matches', []))}")

        second = run_agent(base, tmp, ["--max-matches", "1"])
        print(second.stdout.strip())
        if second.returncode != 0 or arena.match_no != 3:
            failures.append(f"第二次執行（不帶 --deck）應該能加入並打 1 場：rc={second.returncode}、場數={arena.match_no}、"
                            f"{second.stderr.strip()[-300:]}")

        third = run_agent(base, tmp, ["--max-matches", "2", "--ab", "98977b2"])
        print(third.stdout.strip())
        state = json.loads((tmp / "state.json").read_text())
        arms = [(m.get("version") or {}).get("arm") for m in state["matches"][-2:]]
        b_git = [(m.get("version") or {}).get("git") for m in state["matches"][-2:] if (m.get("version") or {}).get("arm") == "B"]
        if third.returncode != 0 or sorted(arms) != ["A", "B"] or b_git != ["98977b2"]:
            failures.append(f"--ab 應該一場 A、一場 B（B＝98977b2）：rc={third.returncode}、arms={arms}、B={b_git}、"
                            f"{third.stderr.strip()[-300:]}")
        if state.get("agentId") != "mock-agent":
            failures.append(f"狀態檔應該記下 agentId：{state.get('agentId')}")
    server.shutdown()

    if failures:
        print("FAIL")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print(f"PASS（模擬伺服器共收到 {arena.joins} 次加入、{len(arena.actions)} 個動作，全部合法）")


if __name__ == "__main__":
    main()
