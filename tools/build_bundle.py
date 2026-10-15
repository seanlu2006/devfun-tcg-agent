#!/usr/bin/env python3
"""打包上傳用的 dist/bundle.zip：manifest.json ＋ harness/strategy.py ＋ assets/。

打包前會先擋三關，任何一關沒過就不產生 zip：
  1. 牌組合法（tools/validate_deck.py）
  2. strategy.py 符合 Python 3.11 文法、只用標準函式庫
  3. 把 zip 解到空資料夾，用隔離模式（python3 -I -S）實際載入並呼叫一次 act()，
     確認在 bundle 的目錄結構下讀得到 assets/catalog.json
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
from validate_deck import expand, validate  # noqa: E402
from replay_test import check_source  # noqa: E402

DIST = ROOT / "dist"
FILES = ["harness/strategy.py", "assets/catalog.json"]

# 一個最小的決策點：只有「結束回合」可選。用來確認 act() 能在 bundle 裡跑起來。
SMOKE_TEST = """
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("strategy", "harness/strategy.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ctx = {"observation": {"current": {"yourIndex": 0, "players": [{}, {}]},
                       "select": {"type": 0, "option": [{"type": 14}]}},
       "legalActions": ["[0]"]}
out = m.act(ctx)
print(json.dumps({"action": out, "cards": len(m.CARDS), "attacks": len(m.ATTACKS)}))
"""


def main():
    deck_path = Path(sys.argv[1])
    deck = json.loads(deck_path.read_text())

    errors, warnings = validate(deck)
    for w in warnings:
        print("警告：", w)
    if errors:
        sys.exit("牌組不合法：" + "；".join(errors))

    not_stdlib = check_source()
    if not_stdlib:
        sys.exit(f"strategy.py import 了非標準函式庫：{not_stdlib}")

    manifest = {
        "schemaVersion": 1,
        "gameType": "PokemonTcg",
        "runtime": "python3.11",
        "entrypoint": "harness/strategy.py",
        "joinPayload": expand(deck),
    }
    DIST.mkdir(exist_ok=True)
    zip_path = DIST / "bundle.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        for rel in FILES:
            zf.write(ROOT / rel, rel)

    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(tmp)
        result = subprocess.run([sys.executable, "-I", "-S", "-c", SMOKE_TEST],
                                cwd=tmp, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            zip_path.unlink()
            sys.exit("bundle 內實際執行失敗：\n" + result.stderr)
        smoke = json.loads(result.stdout.strip().splitlines()[-1])
        if smoke["action"] != "[0]" or smoke["cards"] == 0:
            zip_path.unlink()
            sys.exit(f"bundle 內實際執行結果不對：{smoke}")

    print(f"OK：{zip_path}（{zip_path.stat().st_size / 1024:.0f} KB）｜牌組 {deck['name']}｜"
          f"bundle 內讀到 {smoke['cards']} 張卡、{smoke['attacks']} 個招式")


if __name__ == "__main__":
    main()
