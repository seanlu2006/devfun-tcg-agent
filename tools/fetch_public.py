#!/usr/bin/env python3
"""下載 dev.fun Arena 的公開資料：卡牌目錄、招式目錄、最近對戰與每一步的決策紀錄。

只呼叫不需要登入的公開端點。結果存在 data/raw/（不進 git）。
用法：python3 tools/fetch_public.py [場數，預設 20]
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://arena.dev.fun/api/arena"
COMPETITION_ID = "cmv7zk0ln217r1411n5brb9xq"  # [TCG] Playground S3
RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
MATCH_DIR = RAW / "matches"


def get_json(path):
    """GET 一個端點；遇到網路錯誤就退避重試。"""
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.load(resp)
        except Exception as err:
            print(f"  重試 {attempt + 1}：{err}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"抓不到 {path}")


def save(name, data):
    (RAW / name).write_text(json.dumps(data, ensure_ascii=False))


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    MATCH_DIR.mkdir(parents=True, exist_ok=True)

    save("cards.json", get_json(f"/tcg/cards?competitionId={COMPETITION_ID}"))
    save("attacks.json", get_json("/tcg/attacks"))

    # 分頁往回抓已結束的對戰清單
    matches, cursor = [], None
    while len(matches) < limit:
        path = f"/tcg/matches?competitionId={COMPETITION_ID}&limit=20"
        if cursor:
            path += f"&cursor={cursor}"
        page = get_json(path)
        matches += [m for m in page["matches"] if m["status"] == "Settled"]
        cursor = page.get("nextCursor")
        if not cursor:
            break
    matches = matches[:limit]
    save("matches_index.json", matches)

    for i, m in enumerate(matches, 1):
        mid = m["matchId"]
        out = MATCH_DIR / f"{mid}.json"
        if out.exists():
            continue  # 已經抓過就跳過
        battle = get_json(f"/tcg/battle/{mid}")
        decisions = get_json(f"/tcg/battle/{mid}/decisions")
        out.write_text(json.dumps({"battle": battle, "decisions": decisions}, ensure_ascii=False))
        print(f"[{i}/{len(matches)}] {mid} 決策點 {len(decisions['decisionPoints'])}")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
