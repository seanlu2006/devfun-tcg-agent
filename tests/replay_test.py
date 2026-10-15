#!/usr/bin/env python3
"""重播測試：把公開對戰的每個決策點餵給 harness/strategy.py。

官方沒有本機模擬器，這是我們上傳前唯一的保險。檢查：
  1. act() 回傳的一定在 legalActions 裡
  2. decide() 有沒有拋例外（act() 會吞掉，但吞掉代表策略那一步失效，要知道）
  3. 每一步的耗時
  4. strategy.py 符合 Python 3.11 語法、只 import 標準函式庫
用法：python3 tests/replay_test.py        （失敗時 exit code 1）
"""
import ast
import importlib.util
import json
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STRATEGY = ROOT / "harness" / "strategy.py"
MATCH_DIR = ROOT / "data" / "raw" / "matches"
SANDBOX_PYTHON = (3, 11)


def check_source():
    """用 3.11 的文法規則解析，並列出所有 import。"""
    source = STRATEGY.read_text(encoding="utf-8")
    tree = ast.parse(source, feature_version=SANDBOX_PYTHON)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    not_stdlib = sorted(m for m in imports if m not in sys.stdlib_module_names)
    return not_stdlib


def load_strategy():
    spec = importlib.util.spec_from_file_location("strategy", STRATEGY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def iter_decision_points():
    for path in sorted(MATCH_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        for dp in data["decisions"]["decisionPoints"]:
            for player in dp["perPlayer"].values():
                if player.get("legalActions"):
                    yield path.stem, dp["seq"], player


def main():
    failures = []

    not_stdlib = check_source()
    if not_stdlib:
        failures.append(f"import 了非標準函式庫：{not_stdlib}")

    strategy = load_strategy()
    if not strategy.CARDS:
        failures.append("讀不到 assets/catalog.json（先跑 tools/build_assets.py）")

    total, illegal, slowest = 0, 0, 0.0
    decide_errors = Counter()
    first_error = None
    chosen_kinds = Counter()

    for match_id, seq, player in iter_decision_points():
        context = {"observation": player["obs"], "legalActions": player["legalActions"]}
        total += 1

        start = time.perf_counter()
        action = strategy.act(context)
        slowest = max(slowest, time.perf_counter() - start)
        if action not in player["legalActions"]:
            illegal += 1

        try:
            strategy.decide(context["observation"], context["legalActions"])
        except Exception as err:
            decide_errors[type(err).__name__] += 1
            if first_error is None:
                first_error = f"{match_id} seq {seq}\n{traceback.format_exc()}"

        options = (player["obs"].get("select") or {}).get("option") or []
        picks = strategy.parse_action(action) if action.startswith("[") else []
        kind = options[picks[0]].get("type") if len(picks) == 1 and picks[0] < len(options) else "multi/empty"
        chosen_kinds[kind] += 1

    if total == 0:
        failures.append("沒有任何決策點（先跑 tools/fetch_public.py）")
    if illegal:
        failures.append(f"{illegal} 次回傳了不合法的動作")
    if decide_errors:
        failures.append(f"decide() 拋例外 {sum(decide_errors.values())} 次：{dict(decide_errors)}")

    print(f"決策點 {total}｜不合法 {illegal}｜decide 例外 {sum(decide_errors.values())}｜最慢一步 {slowest * 1000:.1f} ms")
    print(f"選到的 option.type 分布：{dict(chosen_kinds.most_common())}")
    if first_error:
        print("第一個例外：\n" + first_error)
    if failures:
        print("FAIL")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
