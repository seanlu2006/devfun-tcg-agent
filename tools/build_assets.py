#!/usr/bin/env python3
"""把 data/raw 的官方卡牌／招式目錄精簡成 assets/catalog.json，隨 bundle 一起上傳。

比賽沙盒沒有網路，策略要查卡名、HP、招式傷害，只能讀我們自己打包進去的檔案。
用法：python3 tools/fetch_public.py 之後執行 python3 tools/build_assets.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "assets" / "catalog.json"

CARD_FIELDS = ("name", "cardType", "hp", "basic", "stage1", "stage2", "ex", "megaEx",
               "aceSpec", "evolvesFrom", "attacks", "energyType", "pokemonType",
               "retreatCost", "weakness", "resistance")


def main():
    cards = json.loads((RAW / "cards.json").read_text())
    attacks = json.loads((RAW / "attacks.json").read_text())
    catalog = {
        # JSON 的 key 只能是字串，策略讀進來時再轉回 int
        "cards": {str(c["cardId"]): {k: c.get(k) for k in CARD_FIELDS} for c in cards},
        "attacks": {str(a["attackId"]): {"name": a["name"], "damage": a["damage"],
                                          "energies": a["energies"], "text": a.get("text", "")}
                    for a in attacks},
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")))
    print(f"寫入 {OUT}：{len(catalog['cards'])} 張卡、{len(catalog['attacks'])} 個招式，"
          f"{OUT.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
