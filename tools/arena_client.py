#!/usr/bin/env python3
"""dev.fun Arena 帳號相關操作。由 Sean 自己在終端機執行（會建立帳號、讀寫 API key）。

  python3 tools/arena_client.py register [handle "name" "quote"]
                                                      註冊 agent，key 存進 .arena-credentials，印出 X 驗證連結
                                                      （沒給參數會逐題詢問，需要互動式終端機）
  python3 tools/arena_client.py claim                 再印一次 X 驗證連結、看驗證狀態
  python3 tools/arena_client.py submit [bundle.zip]   上傳 dist/bundle.zip，等它變成 Active
  python3 tools/arena_client.py status                看每個版本的戰績、整季剩幾場、目前排名
  python3 tools/arena_client.py stop                  暫停最新版本（省場數；進行中的那場會先打完）

API key 只會出現一次、遺失無法找回：它只存在 .arena-credentials（已列入 .gitignore、權限 600），
本程式不會把完整的 key 印到螢幕上。欄位名稱以官方 introspection 為準（data/raw/introspection.json）。
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

BASE = "https://arena.dev.fun/api/arena"
COMPETITION_ID = "cmv7zk0ln217r1411n5brb9xq"  # [TCG] Playground S3（換季時要改）
ROOT = Path(__file__).resolve().parent.parent
CREDENTIALS = ROOT / ".arena-credentials"
STATE = ROOT / ".arena-tcg-state"

TERMINAL_STATUSES = {"Active", "Failed", "Cancelled", "TimedOut", "Completed", "Succeeded"}
TRANSIENT_ERRORS = {"engine_submission_version_busy"}  # 官方說明：等幾秒、用同一個 bundle 重試


def request(method, path, body=None, key=None, content_type="application/json"):
    headers = {"User-Agent": "devfun-tcg-agent"}
    if key:
        headers["x-arena-api-key"] = key
    if method == "POST" and body is None:
        body = {}  # 伺服器（Fastify）拒絕「宣告 JSON 卻沒有 body」的請求
    if body is not None:
        headers["Content-Type"] = content_type
        if content_type == "application/json":
            body = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as err:
        text = err.read().decode(errors="replace")
        try:
            return err.code, json.loads(text)
        except ValueError:
            return err.code, {"raw": text}


def load_credentials():
    if not CREDENTIALS.exists():
        sys.exit("找不到 .arena-credentials，先執行 register")
    return json.loads(CREDENTIALS.read_text())


def write_secret(path, text):
    """一建立就是 600 權限，不會有「先寫入、再改權限」的空窗。"""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(text)


def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"competition_id": COMPETITION_ID, "submissions": []}


def save_state(state):
    tmp = STATE.with_name(STATE.name + ".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    tmp.replace(STATE)  # 先寫暫存檔再改名，避免寫到一半壞掉


def register(args):
    """register <handle> <name> <quote>；沒給參數就逐題詢問（需要互動式終端機）。"""
    if CREDENTIALS.exists():
        sys.exit("已經註冊過了（.arena-credentials 存在）。一人只能有一個 agent，不要重複註冊。")
    if len(args) >= 3:
        handle, name, quote = args[0], args[1], " ".join(args[2:])
    else:
        try:
            handle = input("handle（排行榜上的代號，英數）：").strip()
            name = input("display name（顯示名稱）：").strip()
            quote = input("quote（一句簡介）：").strip()
        except EOFError:
            sys.exit('這裡不能互動輸入，請把三個值寫在後面：register <handle> "<name>" "<quote>"')
    if not (handle and name and quote):
        sys.exit("handle、name、quote 都不能是空的")
    status, data = request("POST", "/auth/register", {"handle": handle, "name": name, "quote": quote})
    if status >= 300 or "apiKey" not in data:
        sys.exit(f"註冊失敗（HTTP {status}）：{data}")
    write_secret(CREDENTIALS, json.dumps({"apiKey": data["apiKey"], "agentId": data["agentId"]}))
    print(f"註冊成功：agentId {data['agentId']}，key 前綴 {data.get('apiKeyPrefix', data['apiKey'][:12])}…")
    print(f"完整的 key 存在 {CREDENTIALS}（這是唯一一份，請另外備份到密碼管理器）。")
    claim()


def claim():
    cred = load_credentials()
    status, data = request("GET", "/auth/claim/status", key=cred["apiKey"])
    if status >= 300:
        sys.exit(f"查詢驗證狀態失敗（HTTP {status}）：{data}")
    if data.get("claimed") or data.get("xVerifiedAt"):
        print(f"已經用 X 驗證過了（@{data.get('xHandle')}）。")
        return
    url = data.get("claimUrl")
    if not url:
        status, init = request("POST", "/auth/claim/init", key=cred["apiKey"])
        url = init.get("claimUrl")
        if not url:
            sys.exit(f"拿不到驗證連結（HTTP {status}）：{init}")
    print(f"還沒驗證。用瀏覽器打開這個連結、連上你的 X 帳號：\n  {url}")
    print("沒驗證也能打，但不會上排行榜、也領不到獎金。")


def multipart(fields, file_field, file_path):
    boundary = uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; '
                  f'filename="{file_path.name}"\r\nContent-Type: application/zip\r\n\r\n').encode())
    parts.append(file_path.read_bytes() + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def submit(bundle_path):
    if not bundle_path.exists():
        sys.exit(f"找不到 {bundle_path}，先跑 tools/build_bundle.py")
    cred = load_credentials()
    # introspection：必填欄位是 competitionId 與 file（官方 md 寫 bundle，兩者衝突時以 introspection 為準）
    body, ctype = multipart({"competitionId": COMPETITION_ID, "template": "engine-agent"}, "file", bundle_path)
    for attempt in range(4):
        status, data = request("POST", "/submissions", body, key=cred["apiKey"], content_type=ctype)
        transient = status >= 500 or data.get("errorCode") in TRANSIENT_ERRORS or data.get("code") in TRANSIENT_ERRORS
        if not transient:
            break
        print(f"  暫時性錯誤（HTTP {status}），{5 * (attempt + 1)} 秒後用同一個 bundle 重試…")
        time.sleep(5 * (attempt + 1))
    if status >= 300 or not data.get("id"):
        sys.exit(f"上傳被拒（HTTP {status}）：{data}\n錯誤代碼的意思見官方 tcg-playground.md 的 Submission rejected 段。")

    sub_id = data["id"]
    state = load_state()
    state["submissions"].append({"id": sub_id, "bundle": str(bundle_path), "at": time.strftime("%Y-%m-%d %H:%M:%S")})
    save_state(state)
    print(f"已上傳，submission {sub_id}，等待平台驗證…")
    for _ in range(60):  # 最多等約 5 分鐘
        time.sleep(5)
        _, info = request("GET", f"/submissions/{sub_id}", key=cred["apiKey"])
        st = info.get("status")
        print("  狀態：", st)
        if st in TERMINAL_STATUSES:
            if st != "Active":
                print("沒有變成 Active：", info.get("errorCode"), info.get("error"))
            break


def find_on_leaderboard(agent_id):
    offset = 0
    while True:
        status, board = request("GET", f"/competition/leaderboard?competitionId={COMPETITION_ID}&limit=100&offset={offset}")
        if status >= 300:
            return None, f"讀排行榜失敗（HTTP {status}）：{board}"
        rows = board.get("data") or []
        for row in rows:
            if (row.get("agent") or {}).get("id") == agent_id:
                return row, None
        offset += len(rows)
        if not rows or offset >= board.get("total", 0):
            return None, None


def status():
    cred = load_credentials()
    state = load_state()
    latest_allowance = None
    for sub in state["submissions"]:
        _, info = request("GET", f"/submissions/{sub['id']}", key=cred["apiKey"])
        engine = info.get("engine") or {}
        rating = engine.get("rating") or {}
        latest_allowance = engine.get("allowance") or latest_allowance
        print(f"{sub['id']}｜{info.get('status')}｜這個版本 {rating.get('matchesPlayed')} 場、"
              f"{rating.get('wins')} 勝 {rating.get('losses')} 敗｜{(engine.get('activity') or {}).get('state')}")
    if latest_allowance:
        print(f"整季場數：上限 {latest_allowance['limit']}，已用 {latest_allowance['used']}，剩 {latest_allowance['remaining']}")
    row, err = find_on_leaderboard(cred["agentId"])
    if err:
        print(err)
    elif row:
        print(f"排行榜：第 {row.get('rank')} 名，分數 {row.get('totalScore')}")
    else:
        print("還不在排行榜上（要 X 驗證、而且打滿 5 場）")


def stop():
    """暫停最新一個版本（省場數）。官方：要等 activeMatchCount 為 0 才能停，進行中的那場會先打完。"""
    cred = load_credentials()
    state = load_state()
    if not state["submissions"]:
        sys.exit("還沒有上傳過任何版本")
    sub_id = state["submissions"][-1]["id"]
    for _ in range(60):  # 最多等約 5 分鐘讓進行中的對戰結束
        status, data = request("POST", f"/submissions/{sub_id}/stop", key=cred["apiKey"])
        if status < 300:
            print(f"已暫停 {sub_id}。剩下的場數會留給下一個版本。")
            return
        if "in_use" not in json.dumps(data):
            sys.exit(f"暫停失敗（HTTP {status}）：{data}")
        print("  還有對戰在進行，等它打完…")
        time.sleep(5)
    sys.exit("等太久了，晚點再執行一次 stop")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "register":
        register(sys.argv[2:])
    elif cmd == "claim":
        claim()
    elif cmd == "submit":
        submit(Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "dist" / "bundle.zip")
    elif cmd == "status":
        status()
    elif cmd == "stop":
        stop()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
