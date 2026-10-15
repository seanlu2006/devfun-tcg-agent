#!/usr/bin/env python3
"""打包上傳用的 dist/bundle.zip：manifest.json ＋ harness/strategy.py。

卡牌資料（assets/catalog.json）在打包時直接寫進 bundle 裡的 strategy.py（_EMBEDDED_CATALOG），
所以 bundle 不依賴「檔案在哪、cwd 是什麼」。

打包前會先刪掉舊的 zip，再擋三關，任何一關沒過就不產生 zip：
  1. 牌組合法（tools/validate_deck.py）
  2. strategy.py 符合 Python 3.11 文法、只用標準函式庫（tests/replay_test.py 的 check_source）
  3. 把 zip 解開，用隔離模式（python3 -I -S）實際執行兩種載入方式：
       a. 從一個無關的資料夾，用絕對路徑載入檔案
       b. 沒有 __file__、直接 exec 原始碼
     兩種都要讀到卡牌資料，而且在「兩個招式」的決策點選出傷害較高的那個（要靠卡牌資料才答得對）
用法：python3 tools/build_bundle.py decks/starter_dark.json
"""
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))
from validate_deck import ATTACKS, CARDS, expand, validate  # noqa: E402
from replay_test import check_source  # noqa: E402

DIST = ROOT / "dist"
STRATEGY = ROOT / "harness" / "strategy.py"
CATALOG = ROOT / "assets" / "catalog.json"
EMBED_LINE = "_EMBEDDED_CATALOG = None"

PROBE_CARD = 1062  # Yveltal ex：兩個招式，傷害 0 與 210


def embed_catalog(source):
    if source.count(EMBED_LINE) != 1:
        sys.exit(f"strategy.py 裡要剛好有一行 `{EMBED_LINE}`，打包時才能把卡牌資料嵌進去")
    return source.replace(EMBED_LINE, f"_EMBEDDED_CATALOG = {CATALOG.read_text(encoding='utf-8')!r}")


def probe_context():
    """戰鬥場是 Yveltal ex，兩個招式擺成「弱的在前」；正確答案是 [1]。"""
    weak, strong = sorted(CARDS[PROBE_CARD]["attacks"], key=lambda a: ATTACKS[a]["damage"] or 0)[:2]
    players = [{"active": [{"id": PROBE_CARD, "energies": [7, 7, 7]}], "bench": [], "benchMax": 5},
               {"active": [{"id": PROBE_CARD, "energies": []}], "bench": [], "benchMax": 5}]
    obs = {"current": {"yourIndex": 0, "players": players, "turnActionCount": 1},
           "select": {"type": 0, "context": 0,
                      "option": [{"type": 13, "attackId": weak}, {"type": 13, "attackId": strong}]}}
    return {"observation": obs, "legalActions": ["[0]", "[1]"]}


SMOKE_BY_PATH = """
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("strategy", sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print(json.dumps({"action": m.act(json.loads(sys.argv[2])), "cards": len(m.CARDS)}))
"""

SMOKE_BY_EXEC = """
import json, sys
ns = {"__name__": "strategy"}            # 刻意不給 __file__
exec(open(sys.argv[1], encoding="utf-8").read(), ns)
print(json.dumps({"action": ns["act"](json.loads(sys.argv[2])), "cards": len(ns["CARDS"])}))
"""


def smoke(script, strategy_path, cwd):
    result = subprocess.run([sys.executable, "-I", "-S", "-c", script, str(strategy_path), json.dumps(probe_context())],
                            cwd=cwd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        return None, result.stderr.strip()[-800:]
    return json.loads(result.stdout.strip().splitlines()[-1]), None


def main():
    deck_path = Path(sys.argv[1])
    deck = json.loads(deck_path.read_text())
    zip_path = DIST / "bundle.zip"
    zip_path.unlink(missing_ok=True)  # 先刪舊的：驗證沒過時不能留一個舊版讓人誤傳

    errors, warnings = validate(deck)
    for w in warnings:
        print("警告：", w)
    if errors:
        sys.exit("牌組不合法：" + "；".join(errors))

    problems = check_source()
    if problems:
        sys.exit("strategy.py 沒過檢查：" + "；".join(problems))

    manifest = {
        "schemaVersion": 1,
        "gameType": "PokemonTcg",
        "runtime": "python3.11",
        "entrypoint": "harness/strategy.py",
        "joinPayload": expand(deck),
    }
    DIST.mkdir(exist_ok=True)
    tmp_zip = zip_path.with_suffix(".tmp")
    with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("harness/strategy.py", embed_catalog(STRATEGY.read_text(encoding="utf-8")))

    with tempfile.TemporaryDirectory() as bundle_dir, tempfile.TemporaryDirectory() as elsewhere:
        with zipfile.ZipFile(tmp_zip) as zf:
            zf.extractall(bundle_dir)
        entry = Path(bundle_dir) / "harness" / "strategy.py"
        for label, script in (("絕對路徑載入", SMOKE_BY_PATH), ("無 __file__ 的 exec", SMOKE_BY_EXEC)):
            out, err = smoke(script, entry, cwd=elsewhere)
            if err or out["action"] != "[1]" or out["cards"] == 0:
                tmp_zip.unlink()
                sys.exit(f"bundle 實測失敗（{label}）：{err or out}（預期選 [1]、讀到卡牌資料）")

    tmp_zip.replace(zip_path)  # 全部通過才變成正式的 bundle.zip
    print(f"OK：{zip_path}（{zip_path.stat().st_size / 1024:.0f} KB）｜牌組 {deck['name']}｜"
          f"兩種載入方式都讀到 {out['cards']} 張卡，並選對高傷害招式")


if __name__ == "__main__":
    main()
