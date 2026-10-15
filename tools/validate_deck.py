#!/usr/bin/env python3
"""檢查牌組是否合法（規則來自官方說明檔），並展開成 60 個 cardId。

規則：剛好 60 張；同一張卡最多 4 張（基本能量不限）；ACE SPEC 全牌組最多 1 張；
至少 1 張基礎寶可夢；進化卡要有它的前一階；招式需要的能量顏色牌組裡要有。
用法：python3 tools/validate_deck.py decks/starter_dark.json
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = json.loads((ROOT / "assets" / "catalog.json").read_text())
CARDS = {int(k): v for k, v in CATALOG["cards"].items()}
ATTACKS = {int(k): v for k, v in CATALOG["attacks"].items()}
BASIC_ENERGY, POKEMON = 5, 0


def expand(deck):
    ids = []
    for entry in deck["cards"]:
        ids += [entry["id"]] * entry["count"]
    return ids


def validate(deck):
    """回傳 (錯誤清單, 警告清單)。"""
    errors, warnings = [], []
    ids = expand(deck)
    counts = Counter(ids)

    for entry in deck["cards"]:
        card = CARDS.get(entry["id"])
        if card is None:
            errors.append(f"cardId {entry['id']} 不在卡池裡")
        elif entry.get("name") and entry["name"] != card["name"]:
            warnings.append(f"cardId {entry['id']} 實際是「{card['name']}」，牌表寫的是「{entry['name']}」")
    if errors:
        return errors, warnings

    if len(ids) != 60:
        errors.append(f"總張數 {len(ids)}，必須剛好 60")
    for cid, n in counts.items():
        if CARDS[cid]["cardType"] != BASIC_ENERGY and n > 4:
            errors.append(f"{CARDS[cid]['name']} 有 {n} 張，上限 4")
    ace = sum(n for cid, n in counts.items() if CARDS[cid].get("aceSpec"))
    if ace > 1:
        errors.append(f"ACE SPEC 共 {ace} 張，上限 1")
    if not any(CARDS[cid]["cardType"] == POKEMON and CARDS[cid].get("basic") for cid in counts):
        errors.append("沒有基礎寶可夢，開局無法上場")

    names_in_deck = {CARDS[cid]["name"] for cid in counts}
    for cid in counts:
        pre = CARDS[cid].get("evolvesFrom")
        if pre and pre not in names_in_deck:
            warnings.append(f"{CARDS[cid]['name']} 的前一階「{pre}」不在牌組裡")

    energy_types = {CARDS[cid]["energyType"] for cid in counts if CARDS[cid]["cardType"] == BASIC_ENERGY}
    for cid in counts:
        for attack_id in CARDS[cid].get("attacks") or []:
            needed = {e for e in ATTACKS.get(attack_id, {}).get("energies") or [] if e != 0}  # 0＝無色，什麼能量都行
            missing = needed - energy_types
            if missing:
                warnings.append(f"{CARDS[cid]['name']} 的招式「{ATTACKS[attack_id]['name']}」需要能量 {sorted(missing)}，牌組裡沒有")
    return errors, warnings


def main():
    deck = json.loads(Path(sys.argv[1]).read_text())
    errors, warnings = validate(deck)
    kinds = Counter(CARDS[c]["cardType"] for c in expand(deck) if c in CARDS)
    print(f"{deck['name']}：寶可夢 {kinds[0]}｜訓練家 {kinds[1] + kinds[2] + kinds[3] + kinds[4]}｜能量 {kinds[5] + kinds[6]}")
    for w in warnings:
        print("  警告：", w)
    for e in errors:
        print("  錯誤：", e)
    print("FAIL" if errors else "OK")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
