#!/usr/bin/env python3
"""牌組側寫：排行榜前 N 名各自用什麼牌、怎麼打；再把所有玩家按主力攻擊手分流派，算流派對戰勝率。

資料來源是公開對戰紀錄（手牌、牌庫看不到），所以牌表是「被看到過的卡」，不是完整 60 張。
用法：python3 tools/deck_profile.py [前幾名，預設 15]   → 印出摘要，並存 data/deck_profiles.json
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
CATALOG = json.loads((ROOT / "assets" / "catalog.json").read_text())
CARDS = {int(k): v for k, v in CATALOG["cards"].items()}
ATTACKS = {int(k): v for k, v in CATALOG["attacks"].items()}
TYPE_LABEL = {0: "寶可夢", 1: "物品", 2: "道具", 3: "支援者", 4: "競技場", 5: "基本能量", 6: "特殊能量"}


def name(card_id):
    return CARDS.get(card_id, {}).get("name", f"#{card_id}")


def analyse_match(match):
    """回傳 {agentId: 這場的側寫}。"""
    battle = match["battle"]
    winner = (battle.get("result") or {}).get("winnerAgentId")
    reason = (battle.get("result") or {}).get("reason")
    index_of = {}
    for dp in match["decisions"]["decisionPoints"]:
        for agent, player in dp["perPlayer"].items():
            cur = (player.get("obs") or {}).get("current")
            if cur and agent not in index_of:
                index_of[agent] = cur["yourIndex"]
    agent_of = {i: a for a, i in index_of.items()}

    prof = {a: {"cards": set(), "attacks": Counter(), "attack_damage": defaultdict(list), "attacker": Counter(),
                "first_attack_turn": None, "won": a == winner, "reason": reason, "turns": 0} for a in index_of}
    for dp in match["decisions"]["decisionPoints"]:
        for agent, player in dp["perPlayer"].items():
            obs = player.get("obs") or {}
            cur = obs.get("current") or {}
            turn = cur.get("turn") or obs.get("turn") or 0
            for a in prof:
                prof[a]["turns"] = max(prof[a]["turns"], turn)
            for idx, side in enumerate(cur.get("players") or []):
                owner = agent_of.get(idx)
                if owner is None:
                    continue
                for mon in (side.get("active") or []) + (side.get("bench") or []):
                    if mon:
                        prof[owner]["cards"].add(mon["id"])
                        for pre in mon.get("preEvolution") or []:
                            prof[owner]["cards"].add(pre.get("id") if isinstance(pre, dict) else pre)
                        for e in mon.get("energyCards") or []:
                            prof[owner]["cards"].add(e.get("id") if isinstance(e, dict) else e)
                for c in side.get("discard") or []:
                    prof[owner]["cards"].add(c.get("id") if isinstance(c, dict) else c)
            logs = obs.get("logs") or []
            viewer = cur.get("yourIndex")
            for i, log in enumerate(logs):
                owner = agent_of.get(log.get("playerIndex"))
                # 同一個事件雙方視角各記一次：只採用「事件主人自己的視角」，避免重複計算
                if owner is None or log.get("playerIndex") != viewer:
                    continue
                if log.get("type") in (10, 11, 12) and log.get("cardId"):
                    prof[owner]["cards"].add(log["cardId"])
                if log.get("type") == 15:
                    attack_id = log.get("attackId")
                    prof[owner]["attacks"][attack_id] += 1
                    prof[owner]["attacker"][log.get("cardId")] += 1
                    if prof[owner]["first_attack_turn"] is None:
                        prof[owner]["first_attack_turn"] = turn
                    dmg = 0
                    for nxt in logs[i + 1:]:
                        if nxt.get("type") == 15:
                            break
                        # 傷害 log 記的是 HP 變化（負數＝受傷），playerIndex 是受傷那一方
                        if nxt.get("type") == 16 and (nxt.get("value") or 0) < 0 and nxt.get("playerIndex") != log.get("playerIndex"):
                            dmg += -nxt["value"]
                    prof[owner]["attack_damage"][attack_id].append(dmg)
    return prof


SIGNATURES = [  # 依序比對：牌組裡有這張就歸這一派
    ("Dragapult ex", "Dragapult"), ("Alakazam", "Alakazam"), ("Kadabra", "Alakazam"),
    ("Team Rocket's Mewtwo ex", "Team Rocket"), ("Team Rocket's Spidops", "Team Rocket"),
    ("Mega Starmie ex", "Mega Starmie"), ("Mega Lucario ex", "Mega Lucario"), ("Crustle", "Crustle"),
    ("Mega Kangaskhan ex", "Mega Kangaskhan"), ("N’s Zoroark ex", "N's Zoroark"),
]


def archetype(attacker_counter, cards=()):
    names = {name(c) for c in cards} | {name(c) for c in attacker_counter}
    for card_name, label in SIGNATURES:
        if card_name in names:
            return label
    mons = [name(c) for c, _ in attacker_counter.most_common(1) if c]
    return mons[0] if mons else "（沒攻擊過）"


def main():
    top_n = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    board = json.loads((RAW / "leaderboard.json").read_text())["data"][:top_n]
    top = {r["agent"]["id"]: r for r in board}

    per_agent = defaultdict(list)
    all_players = []  # (archetype, won, opponent_archetype)
    for path in sorted((RAW / "matches").glob("*.json")):
        match = json.loads(path.read_text())
        prof = analyse_match(match)
        arch = {a: archetype(p["attacker"], p["cards"]) for a, p in prof.items()}
        agents = list(prof)
        for a in agents:
            per_agent[a].append(prof[a])
            opp = [x for x in agents if x != a]
            all_players.append((arch[a], prof[a]["won"], arch[opp[0]] if opp else None))

    out = []
    for aid, row in top.items():
        games = per_agent.get(aid, [])
        if not games:
            continue
        n = len(games)
        card_freq = Counter(c for g in games for c in g["cards"])
        attacks = Counter()
        damage = defaultdict(list)
        attackers = Counter()
        for g in games:
            attacks.update(g["attacks"])
            attackers.update(g["attacker"])
            for k, v in g["attack_damage"].items():
                damage[k] += v
        firsts = [g["first_attack_turn"] for g in games if g["first_attack_turn"] is not None]
        profile = {
            "rank": row["rank"], "handle": row["agent"]["handle"], "rating": round(row["totalScore"]),
            "games": n, "wins": sum(g["won"] for g in games),
            "archetype": archetype(attackers, card_freq),
            "core": {kind: [f"{name(c)}({card_freq[c]}/{n})" for c, k in card_freq.most_common()
                            if CARDS.get(c, {}).get("cardType") in kinds and k / n >= 0.5]
                     for kind, kinds in (("寶可夢", (0,)), ("訓練家", (1, 2, 3, 4)), ("能量", (5, 6)))},
            "attacks": [f"{ATTACKS.get(a, {}).get('name', a)}×{c} 平均{sum(damage[a]) / max(len(damage[a]), 1):.0f}"
                        for a, c in attacks.most_common(3)],
            "first_attack_turn": round(sum(firsts) / len(firsts), 1) if firsts else None,
            "avg_turns": round(sum(g["turns"] for g in games) / n, 1),
            "win_reasons": dict(Counter(g["reason"] for g in games if g["won"])),
        }
        out.append(profile)

    for p in sorted(out, key=lambda p: p["rank"]):
        print(f"\n#{p['rank']} {p['handle']}（rating {p['rating']}，樣本 {p['wins']}/{p['games']} 勝）｜流派：{p['archetype']}")
        print(f"   寶可夢：{'、'.join(p['core']['寶可夢'][:8])}")
        print(f"   訓練家：{'、'.join(p['core']['訓練家'][:8])}")
        print(f"   能量：{'、'.join(p['core']['能量'][:4])}")
        print(f"   招式：{'；'.join(p['attacks'])}｜第 {p['first_attack_turn']} 回合開始攻擊，平均 {p['avg_turns']} 回合結束｜"
              f"贏法 {p['win_reasons']}")

    # 流派對戰：全部 150 場的所有玩家
    arch_games = Counter(a for a, _, _ in all_players)
    arch_wins = Counter(a for a, w, _ in all_players if w)
    vs = defaultdict(Counter)
    for a, w, opp in all_players:
        if opp:
            vs[(a, opp)]["n"] += 1
            vs[(a, opp)]["w"] += w
    print("\n== 流派（全部對戰，出現 ≥6 次）：場數、勝率")
    common = [a for a, n in arch_games.most_common() if n >= 6]
    for a in common:
        print(f"  {a:<40} {arch_games[a]:>3} 場  {arch_wins[a] / arch_games[a]:.0%}")
    print("\n== 主要流派互打（列＝自己，欄＝對手；格內＝勝場/場數）")
    head = common[:6]
    for a in head:
        cells = []
        for b in head:
            c = vs[(a, b)]
            cells.append(f"{c['w']}/{c['n']}" if c["n"] else "—")
        print(f"  {a[:28]:<28} " + "  ".join(f"{x:>5}" for x in cells))
    print("  欄順序：" + "｜".join(h[:20] for h in head))

    (ROOT / "data" / "deck_profiles.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
