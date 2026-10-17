#!/usr/bin/env python3
"""把一場實戰逐回合攤開：每個主要回合的盤面（雙方戰鬥場／備戰區、我的手牌）和我們選了什麼。

資料來源是 run_agent.py 另存的 data/runs/run_*_obs.jsonl（含自己的手牌）。
用法：python3 tools/timeline.py <matchId 前幾碼> [--all＝連挑卡、選目標也印]
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("strategy", ROOT / "harness" / "strategy.py")
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)

OPT_NAMES = {7: "出牌", 8: "貼能量", 9: "進化", 10: "特性", 12: "撤退", 13: "攻擊", 14: "結束回合", 3: "選卡", 0: "數字"}
ENERGY = {1: "草", 2: "火", 3: "水", 4: "雷", 5: "超", 6: "鬥", 7: "惡", 8: "鋼", 9: "龍", 10: "無"}


def name(card_id):
    return (S.card_info(card_id) or {}).get("name", f"#{card_id}")


def mon(m):
    if not m:
        return "—"
    energies = "".join(ENERGY.get(e, "?") for e in m.get("energies") or [])
    return f"{name(S.card_id_of(m))}({m.get('hp')}/{m.get('maxHp')}{' ' + energies if energies else ''})"


def side(player):
    active = (player.get("active") or [None])[0]
    bench = ", ".join(mon(m) for m in player.get("bench") or [])
    prizes = len(player.get("prize") or [])
    return f"戰鬥 {mon(active)}｜備戰 [{bench}]｜獎賞卡剩 {prizes}｜牌庫 {player.get('deckCount')}"


def describe(board, action):
    picks = S.parse_action(action) or []
    out = []
    for i in picks:
        if not 0 <= i < len(board.options):
            continue
        o = board.options[i]
        label = OPT_NAMES.get(o.get("type"), f"type{o.get('type')}")
        if o.get("type") == 13:
            label += " " + (S.attack_info(o.get("attackId")) or {}).get("name", "?")
        else:
            cid = board.option_card_id(o)
            if cid:
                label += " " + name(cid)
        out.append(label)
    return "、".join(out) or action


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    prefix, show_all = sys.argv[1], "--all" in sys.argv
    records = []
    for path in sorted((ROOT / "data" / "runs").glob("run_*_obs.jsonl")):
        for line in path.read_text().splitlines():
            r = json.loads(line)
            if r["matchId"].startswith(prefix):
                records.append(r)
    if not records:
        sys.exit("找不到這場的紀錄")
    last_turn = None
    for r in records:
        board = S.Board(r["obs"])
        turn = board.current.get("turn")
        main_turn = board.select.get("type") == S.SELECT_MAIN
        if turn != last_turn:
            last_turn = turn
            hand = ", ".join(name(S.card_id_of(c)) for c in board.me.get("hand") or [])
            print(f"\n=== 第 {turn} 回合 ===")
            print(f"  我  ：{side(board.me)}")
            print(f"  對手：{side(board.opp)}")
            print(f"  手牌：{hand}")
        if main_turn or show_all:
            tag = "" if main_turn else f"（select {board.select.get('type')}/{board.select.get('context')}）"
            print(f"  → {describe(board, r['action'])}{tag}")


if __name__ == "__main__":
    main()
