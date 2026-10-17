#!/usr/bin/env python3
"""解讀「非主要回合」的題目：每個 (select.type, select.context) 是被哪張卡觸發、選項來自哪個區域、要選幾張。

做法：遇到這類題目時，往回找同一位玩家最近的「打出卡片／使用招式／進化」log，當作觸發來源。
研究用，不進 bundle。用法：python3 tools/explore_contexts.py
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MATCH_DIR = ROOT / "data" / "raw" / "matches"
CATALOG = json.loads((ROOT / "assets" / "catalog.json").read_text())
CARDS = {int(k): v for k, v in CATALOG["cards"].items()}
ATTACKS = {int(k): v for k, v in CATALOG["attacks"].items()}
TRIGGER_LOGS = {10: "出牌", 12: "進化", 15: "招式"}


def trigger_name(log):
    if log["type"] == 15:
        return "招式:" + ATTACKS.get(log.get("attackId"), {}).get("name", "?")
    return TRIGGER_LOGS[log["type"]] + ":" + CARDS.get(log.get("cardId"), {}).get("name", "?")


def main():
    triggers = defaultdict(Counter)
    shapes = defaultdict(Counter)
    totals = Counter()
    for path in sorted(MATCH_DIR.glob("*.json")):
        match = json.loads(path.read_text())
        recent = {}  # playerIndex → 最近一筆觸發 log
        for dp in match["decisions"]["decisionPoints"]:
            for player in dp["perPlayer"].values():
                obs = player.get("obs") or {}
                for log in obs.get("logs") or []:
                    if log.get("type") in TRIGGER_LOGS:
                        recent[log.get("playerIndex")] = log
                if not player.get("legalActions"):
                    continue
                sel = obs.get("select") or {}
                if sel.get("type") == 0:
                    continue
                key = (sel.get("type"), sel.get("context"))
                totals[key] += 1
                me = (obs.get("current") or {}).get("yourIndex")
                src = recent.get(me)
                triggers[key][trigger_name(src) if src else "（找不到）"] += 1
                areas = sorted({o.get("area") for o in sel.get("option") or [] if "area" in o})
                owners = sorted({"自己" if o.get("playerIndex") == me else "對手"
                                 for o in sel.get("option") or [] if "playerIndex" in o})
                kinds = sorted({o.get("type") for o in sel.get("option") or []})
                shapes[key][f"選{sel.get('minCount')}~{sel.get('maxCount')} 區域{areas} {','.join(owners)} 選項種類{kinds}"] += 1

    for key, n in totals.most_common():
        print(f"== select {key}：{n} 次")
        print("   觸發：", "、".join(f"{k}×{v}" for k, v in triggers[key].most_common(4)))
        print("   形狀：", "；".join(f"{k}×{v}" for k, v in shapes[key].most_common(2)))


if __name__ == "__main__":
    main()
