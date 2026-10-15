#!/usr/bin/env python3
"""dev.fun Arena 帳號相關操作。由 Sean 自己在終端機執行（會建立帳號、讀寫 API key）。

  python3 tools/arena_client.py register              註冊 agent，key 存進 .arena-credentials，印出 X 驗證連結
  python3 tools/arena_client.py claim                 再印一次 X 驗證連結、看驗證狀態
  python3 tools/arena_client.py submit [bundle.zip]   上傳 dist/bundle.zip，等它變成 Active
  python3 tools/arena_client.py status                看所有版本的狀態、已用掉的場數、目前排名

API key 只會出現一次、遺失無法找回：它只存在 .arena-credentials（已列入 .gitignore、權限 600），
本程式不會把完整的 key 印到螢幕上。
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


def request(method, path, body=None, key=None, content_type="application/json"):
    headers = {"User-Agent": "devfun-tcg-agent", "Content-Type": content_type}
    if key:
        headers["x-arena-api-key"] = key
    if body is not None and content_type == "application/json":
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


def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"competition_id": COMPETITION_ID, "submissions": []}


def save_state(state):
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    tmp.replace(STATE)  # 先寫暫存檔再改名，避免寫到一半壞掉


def register():
    if CREDENTIALS.exists():
        sys.exit("已經註冊過了（.arena-credentials 存在）。一人只能有一個 agent，不要重複註冊。")
    handle = input("handle（排行榜上的代號，英數）：").strip()
    name = input("display name（顯示名稱）：").strip()
    quote = input("quote（一句簡介）：").strip()
    status, data = request("POST", "/auth/register", {"handle": handle, "name": name, "quote": quote})
    if status >= 300 or "apiKey" not in data:
        sys.exit(f"註冊失敗（HTTP {status}）：{data}")
    CREDENTIALS.write_text(json.dumps({"apiKey": data["apiKey"], "agentId": data["agentId"]}))
    os.chmod(CREDENTIALS, 0o600)
    print(f"註冊成功：agentId {data['agentId']}，key 前綴 {data.get('apiKeyPrefix', data['apiKey'][:12])}…")
    print(f"完整的 key 存在 {CREDENTIALS}（這是唯一一份，請另外備份到密碼管理器）。")
    claim()


def claim():
    cred = load_credentials()
    status, data = request("GET", "/auth/claim/status", key=cred["apiKey"])
    if data.get("claimed") or data.get("xVerifiedAt"):
        print(f"已經用 X 驗證過了（@{data.get('xHandle')}）。")
        return
    url = data.get("claimUrl")
    if not url:
        _, init = request("POST", "/auth/claim/init", key=cred["apiKey"])
        url = init.get("claimUrl")
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
    cred = load_credentials()
    body, ctype = multipart({"competitionId": COMPETITION_ID, "template": "engine-agent"}, "bundle", bundle_path)
    status, data = request("POST", "/submissions", body, key=cred["apiKey"], content_type=ctype)
    if status >= 300:
        sys.exit(f"上傳被拒（HTTP {status}）：{data}\n錯誤代碼的意思見 docs/protocol.md 與官方 tcg-playground.md。")
    sub_id = data.get("id") or data.get("submissionId") or (data.get("submission") or {}).get("id")
    state = load_state()
    state["submissions"].append({"id": sub_id, "bundle": str(bundle_path), "at": time.strftime("%Y-%m-%d %H:%M:%S")})
    save_state(state)
    print(f"已上傳，submission {sub_id}，等待平台驗證…")
    for _ in range(60):  # 最多等約 5 分鐘
        time.sleep(5)
        _, info = request("GET", f"/submissions/{sub_id}", key=cred["apiKey"])
        st = info.get("status") or (info.get("submission") or {}).get("status")
        print("  狀態：", st)
        if st in ("Active", "Failed"):
            if st == "Failed":
                print("失敗原因：", info.get("error") or info)
            break


def status():
    cred = load_credentials()
    state = load_state()
    used = 0
    for sub in state["submissions"]:
        _, info = request("GET", f"/submissions/{sub['id']}", key=cred["apiKey"])
        body = info.get("submission") or info
        used += body.get("matchesPlayed") or 0
        allowance = (body.get("engine") or {}).get("allowance")
        print(f"{sub['id']}｜{body.get('status')}｜這個版本打了 {body.get('matchesPlayed')} 場｜allowance {allowance}")
    print(f"所有版本合計已用 {used} 場（平台不會告訴你總數，要自己加）")
    _, board = request("GET", f"/competition/leaderboard?competitionId={COMPETITION_ID}&limit=200")
    for row in board.get("data") or []:
        if (row.get("agent") or {}).get("id") == cred["agentId"]:
            print(f"排行榜：第 {row.get('rank')} 名，rating {row.get('rating') or row.get('totalScore')}")
            break
    else:
        print("還不在排行榜上（要 X 驗證、而且打滿 5 場）")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "register":
        register()
    elif cmd == "claim":
        claim()
    elif cmd == "submit":
        submit(Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "dist" / "bundle.zip")
    elif cmd == "status":
        status()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
