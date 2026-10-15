#!/usr/bin/env python3
"""統計公開對戰紀錄裡的選項代碼，用來反推每個數字的意思（研究用，不進 bundle）。"""
import json
from collections import Counter, defaultdict
from pathlib import Path

MATCH_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "matches"

select_kinds = Counter()            # (select.type, select.context) 出現次數
option_fields = defaultdict(Counter)  # option.type → 欄位組合
chosen_then_logs = defaultdict(Counter)  # 被選的 option.type → 下一個決策點新增的 log.type
log_fields = defaultdict(Counter)

for f in sorted(MATCH_DIR.glob("*.json")):
    data = json.loads(f.read_text())
    chosen = {a["seq"]: a["action"] for a in data["battle"]["actions"]}
    dps = data["decisions"]["decisionPoints"]
    for i, dp in enumerate(dps):
        for agent, pp in dp["perPlayer"].items():
            if not pp.get("legalActions"):
                continue
            obs = pp["obs"]; sel = obs.get("select") or {}
            select_kinds[(sel.get("type"), sel.get("context"))] += 1
            for opt in sel.get("option") or []:
                option_fields[opt.get("type")][tuple(sorted(opt.keys()))] += 1
            for lg in obs.get("logs") or []:
                log_fields[lg.get("type")][tuple(sorted(lg.keys()))] += 1
            act = chosen.get(dp["seq"])
            if act is None or i + 1 >= len(dps):
                continue
            picks = [int(x) for x in act.strip("[]").split(",") if x.strip()]
            if not picks:
                continue
            idx = picks[0]
            opts = sel.get("option") or []
            if idx >= len(opts):
                continue
            nxt = dps[i + 1]["perPlayer"].get(agent, {}).get("obs", {})
            for lg in (nxt.get("logs") or [])[:3]:
                chosen_then_logs[opts[idx].get("type")][lg.get("type")] += 1

print("== select (type, context) 前 25")
for k, v in select_kinds.most_common(25): print(" ", k, v)
print("== option.type → 欄位")
for t in sorted(option_fields, key=lambda x: (x is None, x)):
    print(" ", t, dict(option_fields[t].most_common(3)))
print("== 選了 option.type 之後，下一步最常見的 log.type")
for t in sorted(chosen_then_logs, key=lambda x: (x is None, x)):
    print(" ", t, chosen_then_logs[t].most_common(5))
print("== log.type → 欄位")
for t in sorted(log_fields, key=lambda x: (x is None, x)):
    print(" ", t, list(log_fields[t].most_common(1)[0][0]))
