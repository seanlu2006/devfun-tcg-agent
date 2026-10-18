#!/usr/bin/env python3
"""檢討自己的實戰：讀 .arena-tcg-state 記下的每一場，從公開紀錄抓結果，整理勝敗、原因、對手流派、我們的節奏。

用法：python3 tools/review_runs.py [只看最近幾場，預設全部]
結果另存 data/review.json；公開紀錄存在 data/runs/match_<id 前 8 碼>.json（抓過就不重抓）。
"""
import json
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from deck_profile import CARDS, analyse_match, archetype  # noqa: E402

BASE = "https://arena.dev.fun/api/arena"
RUN_DIR = ROOT / "data" / "runs"


def get(path):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.load(resp)
        except Exception:
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(path)


def load_match(match_id):
    path = RUN_DIR / f"match_{match_id[:8]}.json"
    if path.exists():
        return json.loads(path.read_text())
    match = {"battle": get(f"/tcg/battle/{match_id}"), "decisions": get(f"/tcg/battle/{match_id}/decisions")}
    path.write_text(json.dumps(match, ensure_ascii=False))
    return match


def prizes_taken(match, agent_index):
    """從最後一個看得到的盤面，算這位玩家拿了幾張獎賞卡（6 − 剩下的）。"""
    last = None
    for dp in match["decisions"]["decisionPoints"]:
        for player in dp["perPlayer"].values():
            cur = (player.get("obs") or {}).get("current")
            if cur:
                last = cur
    if not last:
        return None
    return 6 - len(last["players"][agent_index].get("prize") or [])


def main():
    state = json.loads((ROOT / ".arena-tcg-state").read_text())
    # agentId 由 run_agent.py 記在狀態檔；舊狀態檔還沒有時才退回讀金鑰檔
    me = state.get("agentId") or json.loads((ROOT / ".arena-credentials").read_text())["agentId"]
    matches = state.get("matches") or []
    if len(sys.argv) > 1:
        matches = matches[-int(sys.argv[1]):]

    rows = []
    for m in matches:
        match = load_match(m["matchId"])
        battle = match["battle"]
        result = battle.get("result") or {}
        prof = analyse_match(match)
        opp_id = next((p["agentId"] for p in battle["players"] if p["agentId"] != me), None)
        index_of = {}
        for dp in match["decisions"]["decisionPoints"]:
            for agent, player in dp["perPlayer"].items():
                cur = (player.get("obs") or {}).get("current")
                if cur:
                    index_of.setdefault(agent, cur["yourIndex"])
        mine = prof.get(me) or {}
        theirs = prof.get(opp_id) or {}
        rows.append({
            "matchId": m["matchId"][:8],
            "version": ((m.get("version") or {}).get("git")) or "（舊紀錄，沒記版本）",
            "opponent": next((p["handle"] for p in battle["players"] if p["agentId"] == opp_id), "?"),
            "opp_archetype": archetype(theirs.get("attacker") or Counter(), theirs.get("cards") or ()),
            "won": result.get("winnerAgentId") == me,
            "reason": result.get("reason"),
            "turns": mine.get("turns"),
            "first_attack_turn": mine.get("first_attack_turn"),
            "prizes": [prizes_taken(match, index_of[me]) if me in index_of else None,
                       prizes_taken(match, index_of[opp_id]) if opp_id in index_of else None],
            "our_attacks": {CARDS.get(c, {}).get("name", c): n for c, n in (mine.get("attacker") or Counter()).items()},
        })

    wins = sum(r["won"] for r in rows)
    real = [r for r in rows if r["reason"] not in ("timeout_forfeit", "forfeit")]
    print(f"共 {len(rows)} 場：{wins} 勝 {len(rows) - wins} 敗"
          f"｜扣掉對手超時／投降：{sum(r['won'] for r in real)}/{len(real)}")
    print(f"{'場次':<9}{'對手':<16}{'流派':<14}{'結果':<4}{'原因':<20}{'回合':>4}{'首攻':>5}  獎賞卡(我/對手)  我們的攻擊")
    for r in rows:
        print(f"{r['matchId']:<9}{r['opponent'][:15]:<16}{r['opp_archetype'][:13]:<14}{'勝' if r['won'] else '敗':<4}"
              f"{str(r['reason'])[:19]:<20}{str(r['turns']):>4}{str(r['first_attack_turn']):>5}  "
              f"{str(r['prizes'][0])}/{str(r['prizes'][1]):<12}{r['our_attacks']}")
    print("\n按策略版本（扣掉對手超時／投降）：")
    for version in dict.fromkeys(r["version"] for r in rows):
        vr = [r for r in rows if r["version"] == version and r["reason"] not in ("timeout_forfeit", "forfeit")]
        if vr:
            print(f"  {version}：{sum(r['won'] for r in vr)}/{len(vr)}（{sum(r['won'] for r in vr) / len(vr):.0%}）"
                  + ("　樣本不足（< 20 場），只能看方向" if len(vr) < 20 else ""))
    by_arch = Counter((r["opp_archetype"], r["won"]) for r in rows)
    print("\n對各流派：" + "｜".join(f"{a} {by_arch[(a, True)]}勝{by_arch[(a, False)]}敗"
                                for a in sorted({r['opp_archetype'] for r in rows})))
    print("輸的原因：", dict(Counter(r["reason"] for r in rows if not r["won"])))
    (ROOT / "data" / "review.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
