#!/usr/bin/env python3
"""偵察環境（metagame）：從公開對戰還原每位玩家「被看到過的卡」，以及誰贏。

手牌和牌庫在公開紀錄裡被遮掉，所以只能看到打出來、貼上去、進化、攻擊過的卡。
得到的是「部分牌表」，拿來看主流是哪些寶可夢、哪些組合常贏。
用法：python3 tools/meta_scout.py
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MATCH_DIR = ROOT / "data" / "raw" / "matches"
CATALOG = json.loads((ROOT / "assets" / "catalog.json").read_text())
CARDS = {int(k): v for k, v in CATALOG["cards"].items()}
CARD_LOG_KEYS = ("cardId", "cardIdTarget", "cardIdActive", "cardIdBench")


def name(card_id):
    return CARDS.get(card_id, {}).get("name", f"#{card_id}")


def seen_cards(match):
    """回傳 {playerIndex: Counter(cardId → 看到幾次)} 與 playerIndex → agentId 的對應。"""
    seen = defaultdict(Counter)
    index_to_agent = {}
    for dp in match["decisions"]["decisionPoints"]:
        for agent, player in dp["perPlayer"].items():
            obs = player.get("obs") or {}
            current = obs.get("current")
            if current:
                index_to_agent[current["yourIndex"]] = agent
                for idx, side in enumerate(current["players"]):
                    for mon in (side.get("active") or []) + (side.get("bench") or []):
                        if not mon:
                            continue  # 戰鬥場可能暫時是空的
                        seen[idx][mon["id"]] += 0  # 有出現過就記一筆（次數不重要）
                        for pre in mon.get("preEvolution") or []:
                            seen[idx][pre.get("id") if isinstance(pre, dict) else pre] += 0
            for log in obs.get("logs") or []:
                for key in CARD_LOG_KEYS:
                    if key in log and log.get("playerIndex") is not None:
                        seen[log["playerIndex"]][log[key]] += 1
    return seen, index_to_agent


def main():
    pokemon_wins, pokemon_games = Counter(), Counter()
    for path in sorted(MATCH_DIR.glob("*.json")):
        match = json.loads(path.read_text())
        result = match["battle"].get("result") or {}
        winner = result.get("winnerAgentId")
        seen, index_to_agent = seen_cards(match)
        for idx, cards in seen.items():
            mons = sorted({name(c) for c in cards if CARDS.get(c, {}).get("cardType") == 0})
            won = index_to_agent.get(idx) == winner
            for m in mons:
                pokemon_games[m] += 1
                pokemon_wins[m] += won
        print(f"{path.stem[:8]} 結果={result.get('reason')}")
        for idx, cards in sorted(seen.items()):
            mons = sorted({name(c) for c in cards if CARDS.get(c, {}).get("cardType") == 0})
            tag = "勝" if index_to_agent.get(idx) == winner else "敗"
            print(f"   [{tag}] {', '.join(mons[:10])}")

    print("\n== 出現 ≥3 場的寶可夢：場數、勝場、勝率")
    for mon, games in pokemon_games.most_common():
        if games >= 3:
            print(f"  {mon:<28} {games:>3} 場  勝 {pokemon_wins[mon]:>3}  {pokemon_wins[mon] / games:.0%}")


if __name__ == "__main__":
    main()
