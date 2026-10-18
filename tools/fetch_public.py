#!/usr/bin/env python3
"""下載 dev.fun Arena 的公開資料：卡牌目錄、招式目錄、對戰與每一步的決策紀錄。

只呼叫不需要登入的公開端點。結果存在 data/raw/（不進 git）。
公開的對戰清單只給「最近 20 場」、沒有下一頁，所以要更多場就按 agent 抓：
先讀排行榜前 N 名，再用 agentId 篩選各自的對戰（這些也剛好是高分玩家的對戰）。
用法：python3 tools/fetch_public.py [總場數上限，預設 20] [排行榜前幾名，預設 0＝只抓最近 20 場]
      python3 tools/fetch_public.py --scout raps,usecommitt [每人幾場，預設 30]
        研究特定對手：按 handle 抓他們的對戰，存到 data/raw/scout/（不混進高手對照用的 data/raw/matches/）
"""
import json
import sys
import time
import urllib.parse
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


def list_matches(agent_id=None, limit=50):
    """分頁抓已結束的對戰；agent_id 給了就只抓那位 agent 的。"""
    matches, cursor = [], None
    while len(matches) < limit:
        path = f"/tcg/matches?competitionId={COMPETITION_ID}&limit=50"
        if agent_id:
            path += f"&agentId={agent_id}"
        if cursor:
            path += f"&cursor={urllib.parse.quote(cursor)}"
        page = get_json(path)
        matches += [m for m in page["matches"] if m["status"] == "Settled"]
        cursor = page.get("nextCursor")
        if not cursor:
            break
    return matches[:limit]


def find_agents(handles):
    """在排行榜裡找這些 handle 的 agentId（分頁掃完整個排行榜）。"""
    wanted, found, offset = {h.lower() for h in handles}, {}, 0
    while True:
        board = get_json(f"/competition/leaderboard?competitionId={COMPETITION_ID}&limit=100&offset={offset}")
        rows = board.get("data") or []
        for row in rows:
            handle = ((row.get("agent") or {}).get("handle") or "").lower()
            if handle in wanted:
                found[handle] = row["agent"]["id"]
        offset += len(rows)
        if not rows or offset >= board.get("total", 0):
            return found


def scout(handles, per_agent):
    out_dir = RAW / "scout"
    out_dir.mkdir(parents=True, exist_ok=True)
    agents = find_agents(handles)
    for handle in handles:
        if handle.lower() not in agents:
            print(f"排行榜上找不到 {handle}")
    for handle, agent_id in agents.items():
        matches = list_matches(agent_id=agent_id, limit=per_agent)
        print(f"{handle}：{len(matches)} 場")
        for m in matches:
            out = out_dir / f"{m['matchId']}.json"
            if out.exists():
                continue
            battle = get_json(f"/tcg/battle/{m['matchId']}")
            decisions = get_json(f"/tcg/battle/{m['matchId']}/decisions")
            out.write_text(json.dumps({"battle": battle, "decisions": decisions, "scouted": handle}, ensure_ascii=False))
            time.sleep(0.5)


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--scout":
        scout([h.strip() for h in sys.argv[2].split(",") if h.strip()], int(sys.argv[3]) if len(sys.argv) > 3 else 30)
        return
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    top_agents = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    MATCH_DIR.mkdir(parents=True, exist_ok=True)

    save("cards.json", get_json(f"/tcg/cards?competitionId={COMPETITION_ID}"))
    save("attacks.json", get_json("/tcg/attacks"))

    matches = {m["matchId"]: m for m in list_matches(limit=limit)}
    if top_agents:
        board = get_json(f"/competition/leaderboard?competitionId={COMPETITION_ID}&limit={min(top_agents, 100)}")
        save("leaderboard.json", board)
        per_agent = max(1, limit // top_agents)
        for row in board.get("data") or []:
            for m in list_matches(agent_id=row["agent"]["id"], limit=per_agent):
                matches.setdefault(m["matchId"], m)
    matches = list(matches.values())[:limit]
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
