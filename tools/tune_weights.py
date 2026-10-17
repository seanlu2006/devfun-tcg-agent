#!/usr/bin/env python3
"""自動調整 strategy.SCORE 的分數，讓「主要回合」的選擇更接近指定高手——用訓練組調、驗收組驗。

沒有遊戲引擎就不能自我對打，這是退而求其次的「多跑幾輪」：
  - 高手的對戰按場次切成訓練組（70%）與驗收組（30%），切法固定（看 matchId 雜湊），每次結果一樣
  - 座標搜尋：每個分數往上／往下試幾個值，訓練組一致率變好才保留
  - 最後印出驗收組的前後對照；驗收組沒變好就代表只是背答案，不要採用
用法：python3 tools/tune_weights.py --handles StartupBros,godam,keris,clairenuttall,grimm_grinder [--rounds 2]
結果存 data/tune_result.json，不會自動改 strategy.py（要不要採用由人決定）。
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MATCH_DIR = ROOT / "data" / "raw" / "matches"
STEPS = (-20, -10, -5, 5, 10, 20)


def load_strategy():
    spec = importlib.util.spec_from_file_location("strategy", ROOT / "harness" / "strategy.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expert_ids(handles):
    board = json.loads((ROOT / "data" / "raw" / "leaderboard.json").read_text())["data"]
    wanted = {h.strip() for h in handles.split(",")}
    return {r["agent"]["id"] for r in board if r["agent"]["handle"] in wanted}


def collect(strategy, experts):
    """把高手在「主要回合」的每一步整理成 (split, Board, legal, answer)。"""
    rows = []
    for path in sorted(MATCH_DIR.glob("*.json")):
        split = "test" if int(hashlib.md5(path.stem.encode()).hexdigest(), 16) % 10 < 3 else "train"
        match = json.loads(path.read_text())
        for target in [p["agentId"] for p in match["battle"]["players"] if p["agentId"] in experts]:
            answers = {a["seq"]: a["action"] for a in match["battle"]["actions"] if a.get("agentId") == target}
            for dp in match["decisions"]["decisionPoints"]:
                player = dp["perPlayer"].get(target) or {}
                legal, answer = player.get("legalActions") or [], answers.get(dp["seq"])
                obs = player.get("obs") or {}
                if legal and answer in legal and (obs.get("select") or {}).get("type") == strategy.SELECT_MAIN:
                    rows.append((split, strategy.Board(obs), legal, answer))
    return rows


def accuracy(strategy, rows, split):
    hit = total = 0
    for s, board, legal, answer in rows:
        if s != split:
            continue
        total += 1
        hit += strategy.choose_main(board, legal) == answer
    return hit / total if total else 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--handles", required=True)
    parser.add_argument("--rounds", type=int, default=2)
    args = parser.parse_args()

    strategy = load_strategy()
    rows = collect(strategy, expert_ids(args.handles))
    original = dict(strategy.SCORE)
    base_train, base_test = accuracy(strategy, rows, "train"), accuracy(strategy, rows, "test")
    print(f"主要回合決策點：訓練 {sum(r[0] == 'train' for r in rows)}、驗收 {sum(r[0] == 'test' for r in rows)}")
    print(f"起點：訓練 {base_train:.1%}｜驗收 {base_test:.1%}")

    best = base_train
    for rnd in range(args.rounds):
        for key in list(strategy.SCORE):
            if key == "end_turn":
                continue  # 結束回合固定 0 當基準
            start = strategy.SCORE[key]
            for step in STEPS:
                strategy.SCORE[key] = start + step
                acc = accuracy(strategy, rows, "train")
                if acc > best + 0.002:  # 至少進步 0.2 個百分點才算，避免追雜訊
                    best, start = acc, start + step
                    print(f"  第 {rnd + 1} 輪 {key}: {start - step} → {start}｜訓練 {acc:.1%}")
            strategy.SCORE[key] = start

    tuned_test = accuracy(strategy, rows, "test")
    changed = {k: (original[k], v) for k, v in strategy.SCORE.items() if v != original[k]}
    print(f"\n結果：訓練 {base_train:.1%} → {best:.1%}｜**驗收 {base_test:.1%} → {tuned_test:.1%}**")
    print("改了哪些分數：", changed or "沒有")
    (ROOT / "data" / "tune_result.json").write_text(json.dumps(
        {"handles": args.handles, "train": [base_train, best], "test": [base_test, tuned_test],
         "changed": changed, "score": strategy.SCORE}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
