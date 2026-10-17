#!/usr/bin/env python3
"""離線評分：我們的策略跟「贏家」在同一個決策點選得一不一樣。

沒有模擬器，打不了真正的對戰；退而求其次，拿公開對戰裡贏家的每一步當參考答案，
按題型算一致率，並附上「永遠選第一個合法動作」的基準線做比較。
限制：公開紀錄看不到手牌與牌庫內容，所以「出哪張手牌」「搜哪張牌」這類題目的分數只能參考。
贏家的選擇也不一定是最好的——這個分數是方向感，不是勝率。

用法：python3 tests/agreement.py            （改完 strategy.py 跑一次，看哪一類變好、變差）
"""
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MATCH_DIR = ROOT / "data" / "raw" / "matches"

MAIN_LABELS = {7: "出手牌", 8: "貼能量", 9: "進化", 10: "特性", 12: "撤退", 13: "攻擊", 14: "結束回合"}
CONTEXT_LABELS = {
    (1, 7): "加到手牌（搜牌／拿獎賞卡）", (1, 4): "挑一隻上戰鬥場", (1, 8): "從手牌丟卡",
    (1, 3): "換位（Switch／Boss）", (1, 5): "牌庫放上備戰區", (9, 43): "進化時的可選特性",
    (1, 1): "開局選戰鬥寶可夢", (1, 2): "開局放備戰區", (1, 14): "放傷害指示物到對手備戰區",
    (4, 30): "選要丟的能量", (1, 21): "選貼能量的對象", (1, 22): "選能量卡",
}


def load_strategy():
    spec = importlib.util.spec_from_file_location("strategy", ROOT / "harness" / "strategy.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    strategy = load_strategy()
    ours, first = defaultdict(Counter), defaultdict(Counter)  # 類別 → Counter(hit/total)
    main_confusion = defaultdict(Counter)  # 贏家選的種類 → 我們選的種類

    for path in sorted(MATCH_DIR.glob("*.json")):
        match = json.loads(path.read_text())
        winner = (match["battle"].get("result") or {}).get("winnerAgentId")
        expert = {a["seq"]: a["action"] for a in match["battle"]["actions"] if a.get("agentId") == winner}
        for dp in match["decisions"]["decisionPoints"]:
            player = dp["perPlayer"].get(winner) or {}
            legal = player.get("legalActions") or []
            answer = expert.get(dp["seq"])
            if not legal or answer is None or answer not in legal:
                continue
            obs = player["obs"]
            sel = obs.get("select") or {}
            board = strategy.Board(obs)
            if sel.get("type") == strategy.SELECT_MAIN:
                opt = strategy.single_pick(board, answer)
                category = "主要回合／" + MAIN_LABELS.get(opt.get("type") if opt else None, "其他")
            else:
                key = (sel.get("type"), sel.get("context"))
                category = "題目／" + CONTEXT_LABELS.get(key, f"其他 {key}")

            mine = strategy.act({"observation": obs, "legalActions": legal})
            ours[category]["total"] += 1
            ours[category]["hit"] += mine == answer
            first[category]["hit"] += legal[0] == answer
            if sel.get("type") == strategy.SELECT_MAIN:
                my_opt = strategy.single_pick(board, mine)
                main_confusion[category][MAIN_LABELS.get(my_opt.get("type") if my_opt else None, "其他")] += 1

    def pct(hit, total):
        return f"{hit / total:6.1%}" if total else "   —  "

    print(f"{'類別':<26}{'次數':>6}  {'我們':>7}  {'選第一個':>7}")
    tot_h = tot_f = tot_n = 0
    for category in sorted(ours, key=lambda c: -ours[c]["total"]):
        n, h, f = ours[category]["total"], ours[category]["hit"], first[category]["hit"]
        tot_n, tot_h, tot_f = tot_n + n, tot_h + h, tot_f + f
        print(f"{category:<26}{n:>6}  {pct(h, n)}  {pct(f, n)}")
    print(f"{'合計':<26}{tot_n:>6}  {pct(tot_h, tot_n)}  {pct(tot_f, tot_n)}")

    print("\n主要回合：贏家選 X 的時候，我們選了什麼（最常見的前 3 種）")
    for category, counter in sorted(main_confusion.items(), key=lambda kv: -sum(kv[1].values())):
        print(f"  {category:<20} → " + "、".join(f"{k} {v}" for k, v in counter.most_common(3)))


if __name__ == "__main__":
    main()
