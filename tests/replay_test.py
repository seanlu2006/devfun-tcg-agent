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
import re
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STRATEGY = ROOT / "harness" / "strategy.py"
MATCH_DIR = ROOT / "data" / "raw" / "matches"
FIXTURE_DIR = ROOT / "tests" / "fixtures"  # 沒下載公開資料時改用這份固定資料（乾淨 checkout 也能跑）
SANDBOX_PYTHON = (3, 11)


# 3.12 才允許 f-string 的 {} 裡面再用同一種引號，例如 f"{d["k"]}"；ast 的 feature_version 擋不到
NESTED_SAME_QUOTE = re.compile(r"""\bf("|')[^\n]*?\{[^}\n]*?\1""")


def check_source():
    """回傳問題清單（空的＝沒問題）：3.11 文法、f-string 巢狀同引號、非標準函式庫 import。

    限制：本機是 3.14，`sys.stdlib_module_names` 也是 3.14 的；3.12 以後才新增的標準庫模組／函式
    這裡擋不到。strategy.py 只用 json、os 這類老模組，維持這個習慣就安全。"""
    problems = []
    source = STRATEGY.read_text(encoding="utf-8")
    tree = ast.parse(source, feature_version=SANDBOX_PYTHON)
    for lineno, line in enumerate(source.splitlines(), 1):
        if NESTED_SAME_QUOTE.search(line):
            problems.append(f"第 {lineno} 行疑似 3.12 才支援的 f-string 巢狀同引號：{line.strip()}")
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    not_stdlib = sorted(m for m in imports if m not in sys.stdlib_module_names)
    if not_stdlib:
        problems.append(f"import 了非標準函式庫：{not_stdlib}")
    return problems


def load_strategy():
    spec = importlib.util.spec_from_file_location("strategy", STRATEGY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic_cases(strategy):
    """公開紀錄裡手牌都是 null，這些手工決策點用來測「看得到手牌」與邊界情況。
    回傳 [(說明, context, 預期動作或 None＝只要求合法且不拋例外)]。"""
    yveltal = 1062                                   # Yveltal ex：基礎寶可夢
    attacks = strategy.card_info(yveltal).get("attacks") or []
    weak, strong = sorted(attacks, key=lambda a: strategy.attack_info(a).get("damage") or 0)[:2] if len(attacks) >= 2 else (None, None)

    def main_turn(hand, options, legal=None):
        players = [{"active": [{"id": yveltal, "energies": [1, 1, 1]}], "bench": [], "benchMax": 5, "hand": hand},
                   {"active": [{"id": yveltal, "energies": []}], "bench": [], "benchMax": 5}]
        obs = {"current": {"yourIndex": 0, "players": players, "turnActionCount": 1},
               "select": {"type": 0, "context": 0, "option": options}}
        return {"observation": obs, "legalActions": legal or [f"[{i}]" for i in range(len(options))]}

    return [
        ("手牌是 cardId 整數：基礎寶可夢要放上備戰區",
         main_turn([yveltal], [{"type": 14}, {"type": 7, "index": 0}]), "[1]"),
        ("手牌是 dict：Switch 在 v0 不出，改結束回合",
         main_turn([{"id": 1123}], [{"type": 7, "index": 0}, {"type": 14}]), "[1]"),
        ("兩個招式：選傷害高的",
         main_turn([], [{"type": 13, "attackId": weak}, {"type": 13, "attackId": strong}, {"type": 14}]), "[1]"),
        ("legalActions 混了 __forfeit__：照樣選最好的，不投降",
         main_turn([], [{"type": 14}, {"type": 13, "attackId": strong}], ["__forfeit__", "[0]", "[1]"]), "[1]"),
        ("對手是 Crustle（ex 打不動）、備戰區有充好能量的 Drakloak：撤退換人", crustle_case(strategy, drakloak_ready=True), "[0]"),
        ("對手是 Crustle、沒人能換：選 Phantom Dive（備戰區指示物照樣有效），不選 Jet Headbutt",
         crustle_case(strategy, drakloak_ready=False), "[1]"),
        ("兩招都打得倒 Dreepy：選 Phantom Dive（多 6 個指示物），不選 Jet Headbutt", mirror_case(strategy, boss=False), "[1]"),
        ("戰鬥場的 Fezandipiti ex 本來就打得倒（2 張）：不出 Boss 拉 1 張的 Dreepy，直接 Phantom Dive",
         mirror_case(strategy, boss=True), "[2]"),
        ("手上只剩 Poké Pad 和接得上的 Drakloak：不出 Ultra Ball（會把 Drakloak 丟掉）", ultra_ball_case(strategy), "[1]"),
        ("context 是 None", None, None),
        ("legalActions 不是 list", {"observation": {}, "legalActions": 5}, None),
        ("observation 缺欄位", {"observation": {"select": {"type": 0, "option": None}}, "legalActions": ["[0]"]}, "[0]"),
    ]


def crustle_case(strategy, drakloak_ready):
    """戰鬥場 Dragapult ex（火＋超）對上 Crustle；選項：[0] 撤退、[1] Phantom Dive、[2] Jet Headbutt、[3] 結束。"""
    ids = {v["name"]: k for k, v in strategy.CARDS.items() if v["name"] in ("Dragapult ex", "Drakloak", "Crustle")}
    atk = {strategy.attack_info(a)["name"]: a for a in strategy.card_info(ids["Dragapult ex"])["attacks"]}
    bench = [{"id": ids["Drakloak"], "hp": 90, "maxHp": 90, "energies": [2, 5] if drakloak_ready else []}]
    players = [{"active": [{"id": ids["Dragapult ex"], "hp": 320, "maxHp": 320, "energies": [2, 5]}],
                "bench": bench, "benchMax": 5, "hand": []},
               {"active": [{"id": ids["Crustle"], "hp": 150, "maxHp": 150, "energies": []}], "bench": [], "benchMax": 5}]
    options = [{"type": 12}, {"type": 13, "attackId": atk["Phantom Dive"]}, {"type": 13, "attackId": atk["Jet Headbutt"]},
               {"type": 14}]
    obs = {"current": {"yourIndex": 0, "players": players, "turnActionCount": 3},
           "select": {"type": 0, "context": 0, "option": options}}
    return {"observation": obs, "legalActions": [f"[{i}]" for i in range(len(options))]}


def mirror_case(strategy, boss):
    """2026-10-18 第 6 批的同流派局面：戰鬥場 Dragapult ex（火＋超）。
    boss=False：對手戰鬥場是 70 HP 的 Dreepy；選項 [0] Jet Headbutt、[1] Phantom Dive、[2] 結束。
    boss=True：對手戰鬥場是 140 HP 的 Fezandipiti ex、備戰區有 Dreepy；
               選項 [0] 出 Boss's Orders、[1] Jet Headbutt、[2] Phantom Dive、[3] 結束。"""
    ids = {}
    for k, v in strategy.CARDS.items():
        ids.setdefault(v["name"].replace("’", "'"), k)
    atk = {strategy.attack_info(a)["name"]: a for a in strategy.card_info(ids["Dragapult ex"])["attacks"]}
    dreepy = {"id": ids["Dreepy"], "hp": 70, "maxHp": 70, "energies": []}
    fez = {"id": ids["Fezandipiti ex"], "hp": 140, "maxHp": 210, "energies": []}
    attacks = [{"type": 13, "attackId": atk["Jet Headbutt"]}, {"type": 13, "attackId": atk["Phantom Dive"]}]
    if boss:
        opp, hand, options = {"active": [fez], "bench": [dreepy]}, [{"id": ids["Boss's Orders"]}], \
            [{"type": 7, "index": 0}] + attacks + [{"type": 14}]
    else:
        opp, hand, options = {"active": [dreepy], "bench": []}, [], attacks + [{"type": 14}]
    players = [{"active": [{"id": ids["Dragapult ex"], "hp": 320, "maxHp": 320, "energies": [2, 5]}],
                "bench": [], "benchMax": 5, "hand": hand, "deckCount": 30}, dict(opp, benchMax=5)]
    obs = {"current": {"yourIndex": 0, "players": players, "turnActionCount": 3},
           "select": {"type": 0, "context": 0, "option": options}}
    return {"observation": obs, "legalActions": [f"[{i}]" for i in range(len(options))]}


def ultra_ball_case(strategy):
    """備戰區 1 隻 Dreepy、手上 Ultra Ball＋Poké Pad＋Drakloak；選項 [0] 出 Ultra Ball、[1] 結束。"""
    ids = {}
    for k, v in strategy.CARDS.items():
        ids.setdefault(v["name"], k)
    hand = [{"id": ids["Ultra Ball"]}, {"id": ids["Poké Pad"]}, {"id": ids["Drakloak"]}]
    players = [{"active": [{"id": ids["Fezandipiti ex"], "hp": 210, "maxHp": 210, "energies": []}],
                "bench": [{"id": ids["Dreepy"], "hp": 70, "maxHp": 70, "energies": []},
                          {"id": ids["Munkidori"], "hp": 110, "maxHp": 110, "energies": []}],
                "benchMax": 5, "hand": hand, "deckCount": 40},
               {"active": [{"id": ids["Dreepy"], "hp": 70, "maxHp": 70, "energies": []}], "bench": [], "benchMax": 5}]
    options = [{"type": 7, "index": 0}, {"type": 14}]
    obs = {"current": {"yourIndex": 0, "players": players, "turnActionCount": 3},
           "select": {"type": 0, "context": 0, "option": options}}
    return {"observation": obs, "legalActions": ["[0]", "[1]"]}


def iter_decision_points():
    paths = sorted(MATCH_DIR.glob("*.json")) or sorted(FIXTURE_DIR.glob("*.json"))
    for path in paths:
        data = json.loads(path.read_text())
        for dp in data["decisions"]["decisionPoints"]:
            for player in dp["perPlayer"].values():
                if player.get("legalActions"):
                    yield path.stem, dp["seq"], player


def main():
    failures = []

    failures += check_source()

    strategy = load_strategy()
    if not strategy.CARDS:
        failures.append("讀不到 assets/catalog.json（先跑 tools/build_assets.py）")

    total, illegal, slowest, main_fallbacks = 0, 0, 0.0, 0
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
        picks = strategy.parse_action(action) or []
        kind = options[picks[0]].get("type") if len(picks) == 1 and picks[0] < len(options) else "multi/empty"
        chosen_kinds[kind] += 1
        if (player["obs"].get("select") or {}).get("type") == strategy.SELECT_MAIN:
            if strategy.decide(context["observation"], context["legalActions"]) is None:
                main_fallbacks += 1

    for label, context, expected in synthetic_cases(strategy):
        try:
            got = strategy.act(context)
        except Exception as err:
            failures.append(f"手工案例「{label}」拋例外：{err!r}")
            continue
        if not isinstance(got, str):
            failures.append(f"手工案例「{label}」回傳的不是字串：{got!r}")
        elif expected is not None and got != expected:
            failures.append(f"手工案例「{label}」預期 {expected}，實際 {got}")

    if total == 0:
        failures.append("沒有任何決策點（先跑 tools/fetch_public.py）")
    if illegal:
        failures.append(f"{illegal} 次回傳了不合法的動作")
    if decide_errors:
        failures.append(f"decide() 拋例外 {sum(decide_errors.values())} 次：{dict(decide_errors)}")

    print(f"決策點 {total}｜不合法 {illegal}｜decide 例外 {sum(decide_errors.values())}｜"
          f"主要回合沒選出動作（退回預設）{main_fallbacks}｜最慢一步 {slowest * 1000:.1f} ms")
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
