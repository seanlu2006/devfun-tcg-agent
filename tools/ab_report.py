#!/usr/bin/env python3
"""A/B 結果：run_agent.py --ab 打的對戰，按組別（A＝當時的目前版本、B＝指定舊版）比較。

為什麼要分層：平台按實力配對，碰到強隊的比例會變；同一時段輪流上場已經讓兩組對手差不多，
再按「對手現在的排行榜名次」分層看，確認差距不是因為某一組剛好多碰到弱隊。
差距要大於 2 個標準誤（約 95% 信心）才標「顯著」；場數少的時候大多不會顯著，這是正常的。

用法：python3 tools/ab_report.py            （最近一次 A/B：B 組最新的那個 commit）
      python3 tools/ab_report.py <B 組 commit>
"""
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from deck_profile import analyse_match, archetype  # noqa: E402
from review_runs import load_match  # noqa: E402
import arena_client as ac  # noqa: E402

TIERS = ((1, 60, "前 60 名"), (61, 90, "61–90 名"), (91, 10**6, "91 名以後"))


def leaderboard_ranks():
    ranks, offset = {}, 0
    while True:
        status, board = ac.request("GET", f"/competition/leaderboard?competitionId={ac.COMPETITION_ID}"
                                          f"&limit=100&offset={offset}")
        rows = board.get("data") or [] if status < 300 else []
        for row in rows:
            ranks[(row.get("agent") or {}).get("id")] = row.get("rank")
        offset += len(rows)
        if not rows or offset >= board.get("total", 0):
            return ranks


def rate(rows):
    n = len(rows)
    w = sum(r["won"] for r in rows)
    return w, n, (w / n if n else None)


def compare(label, a, b):
    wa, na, pa = rate(a)
    wb, nb, pb = rate(b)
    line = f"  {label:<12} A {wa}/{na}" + (f"（{pa:.0%}）" if na else "") + f"｜B {wb}/{nb}" + (f"（{pb:.0%}）" if nb else "")
    if na and nb:
        diff = pa - pb
        se = math.sqrt(max(pa * (1 - pa), 0.25 / na) / na + max(pb * (1 - pb), 0.25 / nb) / nb)
        line += f"｜A−B {diff:+.0%} ± {2 * se:.0%}" + ("　顯著" if abs(diff) > 2 * se else "　還分不出來")
    print(line)


def main():
    state = json.loads((ROOT / ".arena-tcg-state").read_text())
    me = state.get("agentId")
    if not me:
        sys.exit("狀態檔沒有 agentId：先用新版 run_agent.py 跑過一次")
    ab = [m for m in state.get("matches") or [] if (m.get("version") or {}).get("arm")]
    if not ab:
        sys.exit("還沒有 A/B 對戰")
    b_ref = sys.argv[1] if len(sys.argv) > 1 else next(m["version"]["git"] for m in reversed(ab)
                                                       if m["version"]["arm"] == "B")
    b_hash = next((m["version"]["strategy"] for m in reversed(ab)
                   if m["version"]["arm"] == "B" and m["version"]["git"].startswith(b_ref)), None)
    # 同一次實驗＝B 組是同一個策略檔；A 組取同一段時間（第一場 B 到最後一場 B）裡的對戰
    idx = [i for i, m in enumerate(ab) if m["version"]["arm"] == "B" and m["version"]["strategy"] == b_hash]
    if not idx:
        sys.exit(f"找不到 B 組 {b_ref} 的對戰")
    window = ab[idx[0]:idx[-1] + 2]
    ranks = leaderboard_ranks()

    rows = []
    for m in window:
        match = load_match(m["matchId"])
        battle = match["battle"]
        result = battle.get("result") or {}
        if result.get("reason") in ("timeout_forfeit", "forfeit"):
            continue
        opp = next((p["agentId"] for p in battle["players"] if p["agentId"] != me), None)
        theirs = analyse_match(match).get(opp) or {}
        arch = archetype(theirs.get("attacker") or Counter(), theirs.get("cards") or ())
        if arch == "（沒攻擊過）":
            continue
        rows.append({"arm": m["version"]["arm"], "won": result.get("winnerAgentId") == me,
                     "arch": arch, "rank": ranks.get(opp) or 10**6, "reason": result.get("reason")})

    a_git = next((m["version"]["git"] for m in window if m["version"]["arm"] == "A"), "?")
    print(f"A/B：A＝{a_git}、B＝{b_ref}｜有效對戰 {len(rows)} 場（扣掉超時／投降、對手沒攻擊過）")
    A = [r for r in rows if r["arm"] == "A"]
    B = [r for r in rows if r["arm"] == "B"]
    compare("全部", A, B)
    for lo, hi, label in TIERS:
        compare(f"對手{label}", [r for r in A if lo <= r["rank"] <= hi], [r for r in B if lo <= r["rank"] <= hi])
    compare("對 Crustle", [r for r in A if r["arch"] == "Crustle"], [r for r in B if r["arch"] == "Crustle"])
    compare("非 Crustle", [r for r in A if r["arch"] != "Crustle"], [r for r in B if r["arch"] != "Crustle"])
    for arm, group in (("A", A), ("B", B)):
        print(f"  {arm} 組輸的原因：{dict(Counter(r['reason'] for r in group if not r['won']))}")


if __name__ == "__main__":
    main()
