"""dev.fun Arena TCG agent — 出牌決策。

平台（透過 tools/run_agent.py）每遇到一個決策點就呼叫 act(context)，我們要從 context["legalActions"] 挑一個字串回傳。
三層結構：
  1. act()：安全外殼。任何例外都退回合法動作（拋出去＝那一步失效，嚴重時整場判輸）。
  2. Board：把 observation 裡的數字代碼翻成看得懂的東西（代碼意思見 docs/protocol.md）。
  3. 策略：score_main_option()（主要回合）與 choose_other()（其他題目）。
     v1（2026-10-17）依 docs/meta-analysis.md 的 Dragapult 打法調整，規則都是從前 15 名高手的對戰歸納出來的，
     用 `python3 tests/agreement.py --handles StartupBros,godam,keris,clairenuttall` 檢查跟高手的一致率。

相容性：S3 是 owner-hosted，程式在自己的電腦上跑；仍維持 Python 3.11 語法、只用標準函式庫（之後若改成上傳 bundle 也能用）。
"""
import json
import re
import os

# ---------------------------------------------------------------- 代碼常數（見 docs/protocol.md）
SELECT_MAIN = 0          # 主要回合動作
SELECT_NUMBER = 8        # 選數字
SELECT_YES_NO = 9        # 是／否確認

CTX_TO_HAND = 7          # (1, 7) 把一張卡加到手牌（搜牌庫、拿獎賞卡）
CTX_NEW_ACTIVE = 4       # (1, 4) 挑一隻上戰鬥場
CTX_DISCARD_HAND = 8     # (1, 8) 從手牌選卡丟掉
CTX_SWITCH = 3           # (1, 3) 換位：Switch（自己）或 Boss's Orders（對手）
CTX_DECK_TO_BENCH = 5    # (1, 5) 從牌庫放上備戰區
CTX_BENCH_COUNTERS = 14  # (1, 14) 把傷害指示物放到對手備戰區（Phantom Dive）
CTX_OPP_TARGET = 13      # (1, 13) 選對手的某隻寶可夢當目標

OPT_NUMBER = 0
OPT_YES = 1
OPT_NO = 2
OPT_CARD = 3             # 某區域的某張卡
OPT_PLAY_FROM_HAND = 7   # 從手牌打出一張卡
OPT_ATTACH_ENERGY = 8    # 把手牌的能量貼到場上
OPT_EVOLVE = 9           # 進化
OPT_ABILITY = 10         # 使用特性
OPT_RETREAT = 12         # 撤退
OPT_ATTACK = 13          # 使用招式
OPT_END_TURN = 14        # 結束回合

AREA_DECK = 1
AREA_HAND = 2
AREA_DISCARD = 3
AREA_ACTIVE = 4
AREA_BENCH = 5
AREA_STADIUM = 7    # 競技場（current.stadium）
AREA_LOOKING = 12   # 正在看的牌（Drakloak 特性看牌庫上面 2 張），實際卡片在 current.looking

CARD_POKEMON = 0
CARD_ITEM = 1
CARD_TOOL = 2
CARD_SUPPORTER = 3
CARD_STADIUM = 4
CARD_BASIC_ENERGY = 5
CARD_SPECIAL_ENERGY = 6
COLORLESS = 0

FORFEIT = "__forfeit__"
MAX_ACTIONS_PER_TURN = 40  # 保險：一個回合動作太多就收手，避免卡在某種循環裡
DAMAGE_COUNTER = 10        # 一個傷害指示物＝10 點

# 會改變誰在戰鬥場的卡。Switch 類只在「戰鬥場打不出招式、備戰區有人準備好」時才出；
# Boss's Orders 類只在「拉上來就打得倒」時才出（見 score_main_option）。
SWITCH_CARDS = {"Switch", "Scramble Switch"}

# 訓練家卡按用途分（2026-10-17 第 1 場實戰輸在「備戰區沒鋪起來」：手上的 Crushing Hammer 跟搜寶可夢的卡同分，先被打出去）
SEARCH_POKEMON_CARDS = {"Buddy-Buddy Poffin", "Ultra Ball", "Poké Pad", "Nest Ball", "Dawn", "Hilda"}
DISRUPTION_CARDS = {"Crushing Hammer", "Enhanced Hammer", "Unfair Stamp", "Judge", "Xerosic’s Machinations"}
# 不受 ex 寶可夢招式傷害的防守者（2026-10-17：Dragapult ex 打 Crustle 11 次全部 0 傷害；不是 ex 的 Drakloak 打出 70）
EX_IMMUNE_DEFENDERS = {"Crustle"}
ENERGY_FETCH_CARDS = {"Crispin"}        # 從牌庫拿基本能量
DISCARD_COST_CARDS = {"Ultra Ball": 2}   # 出牌時要先丟幾張手牌當代價
RECOVERY_CARDS = {"Night Stretcher"}    # 從棄牌堆撿回寶可夢或基本能量
EX_BLOCKING_STADIUMS = {"Neutralization Zone"}   # 競技場：ex 的招式對非 ex 沒有傷害（雙方都適用）
DRAW_SUPPORTERS = {"Lillie's Determination", "Lillie’s Determination", "Judge"}
TURN_ENDING_ABILITIES = {"Lumiose City"}   # 用了就結束回合的特性（卡牌目錄沒有特性文字，只能寫死）
ABILITY_ENERGY = {"Munkidori": 7}          # 特性要身上有這種能量才能用（Munkidori 的 Adrena-Brain 要惡能量）
THIN_BENCH = 3  # 場上（含戰鬥場）不到這個數量，就優先鋪寶可夢
LOW_DECK = 10   # 牌庫剩這麼少，就停止用找牌特性
GUST_CARDS = {"Boss’s Orders", "Boss's Orders", "Prime Catcher"}
BOARD_CHANGING_CARDS = SWITCH_CARDS | GUST_CARDS | {"Energy Switch"}


# ---------------------------------------------------------------- 卡牌資料
# tools/build_bundle.py 打包時，會把 assets/catalog.json 的內容直接寫進下面這一行，
# 讓 bundle 完全不依賴「檔案在哪」。本機開發時它是 None，改從 assets/ 讀檔。
_EMBEDDED_CATALOG = None


def _catalog_paths():
    paths = []
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        paths.append(os.path.join(here, "..", "assets", "catalog.json"))
    except Exception:  # 有些執行環境沒有 __file__
        pass
    try:
        paths.append(os.path.join(os.getcwd(), "assets", "catalog.json"))
    except Exception:
        pass
    return paths


def _parse_catalog(raw):
    cards = {int(k): v for k, v in raw["cards"].items()}
    attacks = {int(k): v for k, v in raw["attacks"].items()}
    return cards, attacks


def _load_catalog():
    try:
        if _EMBEDDED_CATALOG:
            return _parse_catalog(json.loads(_EMBEDDED_CATALOG))
        for path in _catalog_paths():
            try:
                with open(path, encoding="utf-8") as f:
                    return _parse_catalog(json.load(f))
            except Exception:
                continue
    except Exception:
        pass
    return {}, {}  # 讀不到就當沒有資料，策略會退回保守做法


CARDS, ATTACKS = _load_catalog()

# 名稱 → 從它進化出來的卡（Dreepy → [Drakloak]，Drakloak → [Dragapult ex]），用來「往後看」該貼什麼能量
EVOLVES_INTO = {}
for _cid, _card in CARDS.items():
    if _card.get("evolvesFrom"):
        EVOLVES_INTO.setdefault(_card["evolvesFrom"], []).append(_cid)


def card_info(card_id):
    return CARDS.get(card_id) or {}


def attack_info(attack_id):
    return ATTACKS.get(attack_id) or {}


def card_id_of(card):
    """觀察裡的卡可能是 dict（帶 id）或直接是 cardId 整數。"""
    if isinstance(card, dict):
        return card.get("id")
    return card if isinstance(card, int) else None


def prize_value(card_id):
    """被打倒時對手拿幾張獎賞卡：Mega ex 3、ex 2、其他 1。"""
    card = card_info(card_id)
    if card.get("megaEx"):
        return 3
    return 2 if card.get("ex") else 1


def best_attack(card_id):
    """這張卡傷害最高的招式（attackId, 基礎傷害, 能量費用）；沒招式回傳 None。"""
    best = None
    for attack_id in card_info(card_id).get("attacks") or []:
        atk = attack_info(attack_id)
        entry = (attack_id, atk.get("damage") or 0, atk.get("energies") or [])
        if best is None or entry[1] > best[1]:
            best = entry
    return best


def bench_spread(attack_id):
    """招式說明裡「放傷害指示物到對手備戰區」的額外價值（例：Phantom Dive 6 個＝60）。"""
    text = (attack_info(attack_id).get("text") or "").lower()
    if "damage counters on your opponent" in text and "bench" in text:
        for word, n in (("6 damage counters", 6), ("5 damage counters", 5), ("4 damage counters", 4),
                        ("3 damage counters", 3), ("2 damage counters", 2)):
            if word in text:
                return n * DAMAGE_COUNTER
    return 0


def spread_ko_prizes(board, spread):
    """招式放到對手備戰區的 spread 點傷害，最多能順便打倒幾張獎賞卡（從 HP 最低的開始塞，夠就算）。"""
    if spread and opp_stadium_blocks_spread(board):
        return 0
    prizes, left = 0, spread
    for mon in sorted((m for m in board.opp.get("bench") or [] if m and (m.get("hp") or 0) > 0 and not counter_immune(m)),
                      key=lambda m: m.get("hp")):
        if mon["hp"] > left:
            break
        left -= mon["hp"]
        prizes += prize_value(mon.get("id"))
    return prizes


def plan_cost(card_id, depth=2):
    """這隻寶可夢「打算用的招式」要什麼能量：看自己和往後 depth 階的進化型，取傷害最高的那招。
    例：Dreepy 的計畫招式是 Dragapult ex 的 Phantom Dive（火＋超）——能量先貼在 Dreepy 上，進化後就能直接打。"""
    candidates = [card_id]
    frontier = [card_id]
    for _ in range(depth):
        frontier = [c for f in frontier for c in EVOLVES_INTO.get(card_info(f).get("name"), [])]
        candidates += frontier
    best = None
    for cid in candidates:
        atk = best_attack(cid)
        if atk and (best is None or atk[1] > best[1]):
            best = atk
    return best[2] if best else []


def missing_energy(attached, cost):
    """attached（能量屬性代碼清單）付 cost 之後還缺哪些（有顏色的先配對，無色最後用剩下的補）。"""
    pool = list(attached or [])
    missing = []
    for need in sorted(cost or [], key=lambda e: e == COLORLESS):  # 先處理有顏色的
        if need != COLORLESS and need in pool:
            pool.remove(need)
        elif need == COLORLESS and pool:
            pool.pop()
        else:
            missing.append(need)
    return missing


def parse_action(action):
    """'[0,2]' → [0, 2]；'[]' → []；格式不對（例如 '__forfeit__'）→ None。"""
    try:
        text = action.strip()
        if not (text.startswith("[") and text.endswith("]")):
            return None
        return [int(x) for x in text[1:-1].split(",") if x.strip()]
    except (AttributeError, ValueError):
        return None


def single_pick(board, action):
    """單選動作對應的 option；不是單選或索引超出範圍就回傳 None。"""
    picks = parse_action(action)
    if picks is None or len(picks) != 1 or not 0 <= picks[0] < len(board.options):
        return None
    option = board.options[picks[0]]
    return option if isinstance(option, dict) else None


# ---------------------------------------------------------------- 盤面工具
class Board:
    """把一個決策點的 observation 包成好讀的物件。"""

    def __init__(self, obs):
        self.obs = obs or {}
        self.current = self.obs.get("current") or {}
        players = self.current.get("players") or []
        my_index = self.current.get("yourIndex", 0)
        self.my_index = my_index
        self.me = players[my_index] if my_index < len(players) else {}
        self.opp = players[1 - my_index] if len(players) == 2 else {}
        self.select = self.obs.get("select") or {}
        self.options = self.select.get("option") or []

    # --- 卡在哪裡
    def hand_card_id(self, hand_index):
        """手牌第 hand_index 張的 cardId；看不到手牌（公開紀錄被遮掉）就回傳 None。"""
        hand = self.me.get("hand")
        if not hand or not 0 <= hand_index < len(hand):
            return None
        return card_id_of(hand[hand_index])

    def in_play(self, area, index, side="me"):
        """場上某隻寶可夢（area 4＝戰鬥場、5＝備戰區）。"""
        player = self.me if side == "me" else self.opp
        zone = player.get("active" if area == AREA_ACTIVE else "bench") or []
        return zone[index] if index is not None and 0 <= index < len(zone) else None

    def option_side(self, option):
        if "playerIndex" not in option:
            return "me"
        return "me" if option.get("playerIndex") == self.my_index else "opp"

    def option_card_id(self, option):
        """選項指到的那張卡的 cardId（看得到才有；牌庫要看 select.deck 有沒有給）。"""
        area, index = option.get("area"), option.get("index")
        if option.get("cardId"):
            return option["cardId"]
        if area == AREA_HAND:
            return self.hand_card_id(index or 0)
        if area in (AREA_ACTIVE, AREA_BENCH):
            mon = self.in_play(area, index, self.option_side(option))
            return mon.get("id") if mon else None
        if area == AREA_DISCARD:
            pile = (self.me if self.option_side(option) == "me" else self.opp).get("discard") or []
            return card_id_of(pile[index]) if index is not None and 0 <= index < len(pile) else None
        if area == AREA_STADIUM:
            cards = self.current.get("stadium") or []
            return card_id_of(cards[index]) if isinstance(index, int) and 0 <= index < len(cards) else None
        if area == AREA_LOOKING:
            # Codex 敗局分析（2026-10-18）：以前沒讀這區，Drakloak 看到的兩張都當成未知卡、固定拿第一張，
            # 6 場有 7 次放過了「拿了就能湊齊 Phantom Dive」的能量
            cards = self.current.get("looking") or []
            return card_id_of(cards[index]) if isinstance(index, int) and 0 <= index < len(cards) else None
        if area == AREA_DECK:
            deck = self.select.get("deck")
            if isinstance(deck, list) and index is not None and 0 <= index < len(deck):
                return card_id_of(deck[index])
        return None

    # --- 場上狀況
    @property
    def my_active(self):
        return (self.me.get("active") or [None])[0]

    @property
    def opp_active(self):
        return (self.opp.get("active") or [None])[0]

    def my_pokemon(self):
        return [m for m in (self.me.get("active") or []) + (self.me.get("bench") or []) if m]

    def bench_space(self):
        return self.me.get("benchMax", 5) - len([m for m in self.me.get("bench") or [] if m])

    def names_in_play(self):
        return {card_info(m.get("id")).get("name") for m in self.my_pokemon()}

    def energy_needed(self, pokemon):
        """這隻寶可夢（含往後的進化型）的計畫招式，還缺幾個能量。"""
        if not pokemon:
            return 0
        return len(missing_energy(pokemon.get("energies"), plan_cost(pokemon.get("id"))))

    def can_attack_now(self, pokemon):
        """這隻寶可夢「現在的樣子」有沒有一招的能量已經付得起。"""
        if not pokemon:
            return False
        for attack_id in card_info(pokemon.get("id")).get("attacks") or []:
            cost = attack_info(attack_id).get("energies") or []
            if (attack_info(attack_id).get("damage") or 0) > 0 and not missing_energy(pokemon.get("energies"), cost):
                return True
        return False

    def damage_against(self, attack_id, attacker, defender):
        """招式打 defender 的估計傷害：基礎傷害、弱點 ×2、抗性 −30（變動傷害的招式算基礎值）。"""
        dmg = attack_info(attack_id).get("damage") or 0
        if not (attacker and defender) or dmg <= 0:
            return dmg
        my_card = card_info(attacker.get("id"))
        target = card_info(defender.get("id"))
        attacker_ex = my_card.get("ex") or my_card.get("megaEx")
        stadium = (self.current.get("stadium") or [None])[0]
        if attacker_ex and stadium and card_info(card_id_of(stadium)).get("name") in EX_BLOCKING_STADIUMS \
                and not (target.get("ex") or target.get("megaEx")):
            return 0  # Neutralization Zone：ex 的招式打不痛非 ex（Codex 敗局分析 cd088efe：Phantom Dive 正面打 Alakazam 被擋）
        if target.get("name") in EX_IMMUNE_DEFENDERS and attacker_ex:
            return 0  # 特性：不受對手 ex 寶可夢招式的傷害（卡牌目錄沒有特性資料，只能寫死）
        my_type = my_card.get("energyType")
        if target.get("weakness") is not None and target.get("weakness") == my_type:
            dmg *= 2
        if target.get("resistance") is not None and target.get("resistance") == my_type:
            dmg -= 30
        return max(dmg, 0)

    def power_now(self, pokemon):
        """這隻寶可夢「現在就付得起」的招式，打對手戰鬥場的最高估計傷害（付不起任何一招＝0）。
        有算 Crustle 這類 ex 打不動的對手，所以會讓「Dragapult ex 打 0、Drakloak 打 70」時換人。"""
        if not pokemon:
            return 0
        best = 0
        for attack_id in card_info(pokemon.get("id")).get("attacks") or []:
            atk = attack_info(attack_id)
            if not missing_energy(pokemon.get("energies"), atk.get("energies") or []):
                hit = self.damage_against(attack_id, pokemon, self.opp_active) if self.opp_active \
                    else (atk.get("damage") or 0)
                # Phantom Dive 放到對手備戰區的指示物也算戰力（對手有備戰寶可夢時）：打 Crustle 本體是 0，
                # 但 60 點照樣有效（Codex 敗局分析 121bda75 T27：戰鬥場 Dragapult 沒能量、備戰區有備好的，
                # 兩隻都被算成 0，於是沒補撤退費換人）
                # 對手的 Battle Cage 會擋掉備戰區指示物 → 不算（Codex 敗局分析 5b1c90af：被當成 60 戰力，沒換 Drakloak）
                # 備戰區全都帶 Mist／Rock Fighting Energy（指示物打不進去）也算 0（Codex 敗局分析 83ae9aed T13）
                hittable = any(m and not counter_immune(m) for m in self.opp.get("bench") or [])
                spread = bench_spread(attack_id) if hittable and not opp_stadium_blocks_spread(self) else 0
                best = max(best, hit + spread)
        return best

    def max_damage_vs(self, defender):
        """我方戰鬥場「現在付得起」的招式打 defender 的最高估計傷害（不在主要回合也能算）。"""
        attacker = self.my_active
        if not attacker or not defender:
            return 0
        best = 0
        for attack_id in card_info(attacker.get("id")).get("attacks") or []:
            if not missing_energy(attacker.get("energies"), attack_info(attack_id).get("energies") or []):
                best = max(best, self.damage_against(attack_id, attacker, defender))
        return best

    def better_attacker_on_bench(self):
        """備戰區有沒有一隻「現在就能打、而且明顯比戰鬥場那隻強」的（至少 60，且多 50 以上）。
        2026-10-17 實戰：舊規則只看「戰鬥場打不打得出招式」，Budew 的 10 點招式不用能量，
        於是整場卡在戰鬥場，備戰區的 Dragapult ex 從沒上來；也發生過把 Meowth ex 換成只打 10 的 Dreepy。"""
        active_power = self.power_now(self.my_active)
        opp = self.opp_active
        opp_hp = (opp or {}).get("hp") or 0
        for mon in self.me.get("bench") or []:
            p = self.power_now(mon)
            card = card_info(mon.get("id"))
            active_card = card_info((self.my_active or {}).get("id"))
            # 只在戰鬥場是非 ex 配角時才擋：對上 Crustle 時 ex 打不動，Drakloak 本來就該上前
            # 牆對局（Crustle）時解除：Drakloak 是唯一打得動牆的（Codex 對局分析 1f44ea4d：T5 就備好，拖到 T13 才打）
            engine = card.get("stage1") and EVOLVES_INTO.get(card.get("name")) \
                and not (active_card.get("ex") or active_card.get("megaEx")) and not facing_wall(self)
            # 還能再進化的中間型（Drakloak＝找牌引擎）不為了「打得比較痛」推上前，只在打得倒時才換（下面那條）
            # （Codex 敗局分析 cfd39c6f T3：撤退 Munkidori 讓 90 HP 的 Drakloak 打 70，下回合被打倒；
            #  高手對照：改變的 11 點裡高手都沒撤退，0／2／9）
            if p >= 60 and p >= active_power + 50 and not engine:
                return True
            # 戰鬥場打不倒、備戰區這隻打得倒 → 換（撤退不會結束回合）
            # （Codex 敗局分析 cd088efe T13：Neutralization Zone 下 Dragapult 打 0，備戰區 Drakloak 70 剛好打倒 Alakazam）
            if opp_hp and self.damage_vs_opp(mon) >= opp_hp > self.damage_vs_opp(self.my_active):
                return True
        return False

    def damage_vs_opp(self, pokemon):
        """這隻現在付得起的招式，打對手戰鬥場的最高正面傷害（不含備戰區指示物）。"""
        best = 0
        for attack_id in card_info((pokemon or {}).get("id")).get("attacks") or []:
            if not missing_energy(pokemon.get("energies"), attack_info(attack_id).get("energies") or []):
                best = max(best, self.damage_against(attack_id, pokemon, self.opp_active))
        return best

    def opp_threat(self, defender):
        """對手戰鬥場「現在付得起」的招式打 defender 的最高估計傷害（變動傷害的招式算基礎值，會低估）。"""
        attacker = self.opp_active
        if not attacker or not defender:
            return 0
        best = 0
        for attack_id in card_info(attacker.get("id")).get("attacks") or []:
            if not missing_energy(attacker.get("energies"), attack_info(attack_id).get("energies") or []):
                dmg = self.damage_against(attack_id, attacker, defender)
                # 「雙方戰鬥寶可夢每有 1 個能量多 N 傷害」（Teal Mask Ogerpon ex 的 Myriad Leaf Shower：以前只算基礎 30，實際打 210）
                bonus = re.search(r"(\d+) more damage for each energy attached to both active", (attack_info(attack_id).get("text") or "").lower())
                if bonus and dmg > 0:
                    total = len(attacker.get("energies") or []) + len((self.my_active or {}).get("energies") or [])
                    dmg += int(bonus.group(1)) * total
                optional = re.search(r"you may [^.]*?(\d+) more damage", (attack_info(attack_id).get("text") or "").lower())
                if optional and dmg > 0:
                    dmg += int(optional.group(1))   # 「可以棄能量多打 N」：對手會用（Codex 敗局分析 24eb937e：Riotous Blasting 200＋130）
                dmg = max(dmg, self.hand_counter_damage(attack_id))
                best = max(best, dmg)
        return best

    def hand_counter_damage(self, attack_id, hand_count=None):
        """「對手手牌每 1 張，放 N 個傷害指示物到戰鬥場」（Alakazam 的 Powerful Hand）。"""
        m = re.search(r"place (\d+) damage counters? on your opponent.s active pok.mon for each card in your hand",
                      (attack_info(attack_id).get("text") or "").lower())
        if not m:
            return 0
        n = self.opp.get("handCount") if hand_count is None else hand_count
        return int(m.group(1)) * DAMAGE_COUNTER * (n or 0)

    def judge_saves_active(self):
        """對手靠手牌張數打傷害（Powerful Hand），現在打得倒我們的戰鬥場、而被打倒就輸；Judge 讓他只剩 4 張就打不倒。
        （Codex 敗局分析 cd088efe T19：對手 17 張手牌＝340，滿血 Dragapult 320；Judge 合法卻選了打不完的 Phantom Dive）"""
        active, attacker = self.my_active, self.opp_active
        if not active or not attacker:
            return False
        hp = active.get("hp") or 0
        # 不必等到「被打倒就輸」：對手下回合開頭還會抽 1 張（Codex 敗局分析 553cceb5 T6：15 張手牌＋1＝320，
        # 下回合打 340 收掉 Dragapult）
        opp_hand = (self.opp.get("handCount") or 0) + 1
        for attack_id in card_info(attacker.get("id")).get("attacks") or []:
            if missing_energy(attacker.get("energies"), attack_info(attack_id).get("energies") or []):
                continue
            if self.hand_counter_damage(attack_id, opp_hand) >= hp > self.hand_counter_damage(attack_id, 5):
                return True
        return False

    def losing_swap_available(self):
        """戰鬥場被打倒就輸（對手剩下的獎賞卡 ≤ 它值的張數）、這回合又打不倒對手 →
        換一隻「挨得住、還能打 60 以上」的上來，就算火力比較弱（Codex 敗局分析 ff63b361 T15）。"""
        active = self.my_active
        if not active or self.opp_threat(active) < (active.get("hp") or 0):
            return False
        if len(self.opp.get("prize") or []) > prize_value(active.get("id")):
            return False
        opp = self.opp_active
        if opp and self.max_damage_vs(opp) >= (opp.get("hp") or 0) > 0:
            return False
        return any(self.power_now(m) >= 60 and (m.get("hp") or 0) > self.opp_threat(m) for m in self.me.get("bench") or [])

    def healthy_swap_available(self):
        """戰鬥場那隻下回合會被打倒，備戰區有一隻「現在戰力不輸它、而且挨得住」的 → 撤退換牠上來。
        撤退不會結束回合，換上來的照樣能攻擊；代價只是受傷那隻丟 1 個能量。
        （Codex 對局分析 49b04e7c T11：前排 Dragapult 剩 80 HP、後排滿血 Dragapult 已備好，照打 Phantom Dive，
         下回合前排被打倒、對手拿到最後的獎賞卡）"""
        active = self.my_active
        threat = self.opp_threat(active)
        if not active or threat < (active.get("hp") or 0):
            return False
        power = self.power_now(active)
        return any(self.power_now(m) >= max(power, 60) and (m.get("hp") or 0) > self.opp_threat(m)
                   for m in self.me.get("bench") or [])

    def save_evolution_line(self):
        """戰鬥場是還能再進化的中間型（Drakloak），下回合會被打倒、這回合又打不倒對手 →
        撤退，換一隻不在進化線上的非 ex 配角（Budew）出來擋：送的獎賞卡一樣是 1 張，但保住找牌特性和進化線。
        （Codex 敗局分析 8d2c126f T11、038bc37c T11：Drakloak 連能量一起被打倒）"""
        active = self.my_active
        card = card_info((active or {}).get("id"))
        mid_line = card.get("stage1") and EVOLVES_INTO.get(card.get("name"))
        # 也包括「打不出像樣傷害的 ex」：被打倒送 2 張，換 Budew 上去只送 1 張（Codex 敗局分析 66a66af0 T6：Meowth ex）
        weak_ex = (card.get("ex") or card.get("megaEx")) and self.power_now(active) < 60
        if not active or not (mid_line or weak_ex):
            return False
        opp = self.opp_active
        if self.opp_threat(active) < (active.get("hp") or 0):
            return False
        if opp and self.max_damage_vs(opp) >= (opp.get("hp") or 0) > 0:
            return False   # 這回合打得倒對手：先打
        for mon in self.me.get("bench") or []:
            info = card_info(mon.get("id"))
            if info.get("basic") and not (info.get("ex") or info.get("megaEx")) and not EVOLVES_INTO.get(info.get("name")):
                return True
        return False

    def best_damage_now(self):
        """主要回合裡「現在合法的招式」能打出的最高估計傷害（打對手戰鬥場）。"""
        best = 0
        for option in self.options:
            if isinstance(option, dict) and option.get("type") == OPT_ATTACK:
                best = max(best, self.damage_against(option.get("attackId"), self.my_active, self.opp_active))
        return best

    @property
    def turn_action_count(self):
        return self.current.get("turnActionCount", 0)


# ---------------------------------------------------------------- 主要回合：替每個選項打分數（分數最高的被選）
# 分數梯度（高 → 低）：進化 90 ＞ 特性 88 ＞ 貼需要的能量 80～85 ＞ 放基礎寶可夢 70 ＞ 打得倒的攻擊 60
#                    ＞ 抽牌／搜牌 50 ＞ 打不倒的攻擊 40 ＞ 其他物品 30 ＞ 多貼能量 15 ＞ 結束回合 0
# 特性排第二：高手幾乎都先用特性（Drakloak 找牌等）看到更多牌再決定，對照高手的一致率 28% → 69%。
# 想法：攻擊會結束回合，所以「有價值的佈局」先做；但不必把手牌全部出完才攻擊（高手很少這樣）。
SCORE = {
    "evolve": 90, "attach_needed_active": 85, "attach_needed_bench": 80, "attach_colorless": 65,
    "bench_basic": 70, "attack_ko": 60, "ability": 88, "draw": 50, "attack": 40, "retreat_ready": 75,
    "item": 30, "tool": 25, "stadium": 20, "attach_extra": 15, "end_turn": 0,
}


def score_main_option(board, option):
    """主要回合時，替一個選項打分數。TODO(Sean)：這是策略核心，數字都可以調。"""
    kind = option.get("type")

    if kind == OPT_EVOLVE:
        # 要進化的那隻現在還能用特性（Drakloak 看 2 張拿 1 張）→ 先用特性，進化後就沒了
        # （Codex 敗局分析：24 場、37 次先進化成 Dragapult ex，白白少看兩張牌）
        deck_count = board.me.get("deckCount")
        if (deck_count is None or deck_count > LOW_DECK) and any(
                isinstance(o, dict) and o.get("type") == OPT_ABILITY and o.get("area") == option.get("inPlayArea")
                and o.get("index") == option.get("inPlayIndex") for o in board.options):
            return SCORE["ability"] - 1
        # 場上已經有 2 隻 Dragapult ex，就別把最後一隻 Drakloak 也進化掉：之後每回合還要靠它找牌
        # （Codex 對局分析 f6698511 T7：進化成第三隻 Dragapult 後，T9、T11 都沒有 Drakloak 可以用）
        target = board.in_play(option.get("inPlayArea"), option.get("inPlayIndex"))
        target_name = card_info((target or {}).get("id")).get("name")
        evolves_to = card_info(board.hand_card_id(option.get("index", 0))).get("name")
        names = [card_info(m.get("id")).get("name") for m in board.my_pokemon()]
        if target_name == "Drakloak" and names.count("Drakloak") == 1 and names.count(evolves_to) >= 2:
            return -1   # 等其中一隻 Dragapult ex 被打倒（剩不到 2 隻）才進化，這條就不擋了
        # 進化後戰力反而下降（對上 Crustle：能打 70 的 Drakloak 進化成打 0 的 Dragapult ex）→ 不進化
        # （Codex 對局分析：三場 Crustle 消耗戰都這樣把唯一打得動的攻擊手進化掉）
        if target and facing_wall(board) and target_name == "Drakloak" and board.hand_card_id(option.get("index", 0)) is not None:
            # 牆對局：差 1 個能量就能打的 Drakloak 也別進化（進化成 Dragapult ex 對 Crustle 打 0），
            # 除非已經有別的非 ex 攻擊手備好（Codex 對局分析 275fa6ca T9、T17）
            own_cost = min((attack_info(a).get("energies") or [] for a in card_info(target.get("id")).get("attacks") or []),
                           key=len, default=[])
            others_ready = any(m is not target and not card_info(m.get("id")).get("ex") and board.power_now(m) >= 60
                               for m in board.my_pokemon())
            lacking = missing_energy(target.get("energies"), own_cost)
            if len(lacking) <= 1 and not others_ready:
                # 補齊後比較進化前後的戰力（含有效的備戰區指示物）：只有進化會變弱才擋
                # （第 28 批：一律擋時，沒帶 Battle Cage 的 Crustle 對局也不進化，Phantom Dive 的 60 點被浪費）
                filled = (target.get("energies") or []) + [e if e != COLORLESS else 1 for e in lacking]
                before = board.power_now(dict(target, energies=filled))
                after = board.power_now(dict(target, energies=filled, id=board.hand_card_id(option.get("index", 0))))
                # 只在「進化後完全打不出東西」（Battle Cage 擋掉備戰指示物）時擋：備戰指示物有效時，
                # Dragapult ex 的 320 HP 撐得住 Crustle，Drakloak 的 90 撐不住（第 28 批 54a52fdc：一律擋，0 比 5 輸）
                if after == 0 < before:
                    return -1
        if target and board.hand_card_id(option.get("index", 0)) is not None:   # 看不到手牌（公開紀錄）就不判斷
            evolved = dict(target, id=board.hand_card_id(option.get("index", 0)))
            if board.power_now(target) >= 60 and board.power_now(evolved) < board.power_now(target):
                return -1
        # 試過「進化後會被打倒的戰鬥場改進化別隻」（Codex 建議）：高手 13 次跟舊規則、9 次跟新規則，不採用
        return SCORE["evolve"]

    if kind == OPT_ATTACH_ENERGY:
        return score_attach(board, option)

    if kind == OPT_PLAY_FROM_HAND:
        return score_play_card(board, option)

    if kind == OPT_ABILITY:
        if card_info(board.option_card_id(option)).get("name") in TURN_ENDING_ABILITIES:
            # 競技場 Lumiose City：搜完寶可夢就結束回合 → 排在佈局和攻擊之後
            # （Codex 敗局分析 121bda75：4 個回合被它提前結束，其中一回合連攻擊都沒打）
            return 1
        # 牌庫快見底就別再用找牌／抽牌類特性（2026-10-17 實戰：3 隻 Drakloak 每回合都找牌，牌庫被抽光判輸）
        deck_count = board.me.get("deckCount")
        # 只擋抽牌／找牌的特性；Munkidori 移傷害不碰牌庫（Codex 敗局分析 388f3888 T21：牌庫 7 張時沒移傷，
        # 被 250 打倒；高手 4 比 0）
        draws = card_info(board.option_card_id(option)).get("name") not in COUNTER_MOVERS
        if draws and wall_attacker_ready(board):
            return 5   # 牆對局、已有非 ex 攻擊手在打：省牌庫（raps 的 Crustle 三場都是我們先抽光；Codex 對局分析）
        if draws and wall_in_play(board) and deck_count is not None and deck_count <= 25 \
                and len(board.me.get("hand") or []) >= 4:
            # 對手有 Crustle：手上已經有牌就別再挖牌庫（第 30 批 599b0a95：已拿 5 獎、對手 0 獎，T24 牌庫抽光；
            # 累計 8 場 Crustle 對局都是我們先抽光）
            return 5
        if draws and deck_count is not None and deck_count <= LOW_DECK:  # 不能寫 (deckCount or 99)：0 張會被當成 99（Codex 審查抓到）
            return 5
        return SCORE["ability"]

    if kind == OPT_ATTACK:
        text = (attack_info(option.get("attackId")).get("text") or "").lower()
        if "this pokémon and all attached cards into your hand" in text and not (board.me.get("bench") or []):
            return -1  # Meowth ex 的 Tuck Tail：備戰區沒人時用了＝場上沒寶可夢，直接判輸（Codex 敗局分析 2f177d48）
        damage = board.damage_against(option.get("attackId"), board.my_active, board.opp_active)
        spread = bench_spread(option.get("attackId"))
        opp = board.opp_active
        prizes = spread_ko_prizes(board, spread)   # 放到備戰區的指示物順便打倒的
        if opp and damage >= (opp.get("hp") or 0) > 0:
            prizes += prize_value(opp.get("id"))
        # 同分挑「總價值」高的——Phantom Dive 這類招式另外有 60 點放到備戰區
        # （打 Crustle 時本體是 0，但備戰區的 6 個指示物照樣有效，所以要選它而不是 Jet Headbutt；
        #  2026-10-18 第 6 批：兩招都打得倒 70 HP 的 Dreepy，卻選了 Jet Headbutt，白白浪費 6 個指示物）
        tiebreak = (damage + spread) / 1000
        if prizes:
            return SCORE["attack_ko"] + prizes + tiebreak  # 打得倒：拿獎賞卡，優先
        return SCORE["attack"] + tiebreak

    if kind == OPT_RETREAT:
        # 備戰區有明顯更強、而且現在就能打的 → 撤退換牠上來
        if board.healthy_swap_available():
            # 先保住殘血主力再 Boss：Boss 拉上新目標後，這個條件可能就不成立了
            # （Codex 敗局分析 d6310aa9 T15：先 Boss，留場的 80 HP Dragapult 被打倒送 2 獎）
            return SCORE["attach_needed_active"] + 2
        if board.better_attacker_on_bench() or board.save_evolution_line() or board.losing_swap_available():
            return SCORE["retreat_ready"]
        return -10

    if kind == OPT_END_TURN:
        return SCORE["end_turn"]

    return 1  # 不認得的選項：比結束回合高一點，但不優先


def score_attach(board, option):
    """貼能量：貼到「計畫招式還缺這個顏色」的寶可夢上（Dreepy 會看 Dragapult ex 要的火＋超）。"""
    target = board.in_play(option.get("inPlayArea"), option.get("inPlayIndex", 0))
    if not target:
        return SCORE["attach_extra"]
    if option.get("inPlayArea") == AREA_ACTIVE and needs_energy_to_retreat(board) and board.better_attacker_on_bench():
        # 備戰區已經有備好的主攻手，戰鬥場那隻（例：Meowth ex）卻付不起撤退費 → 這張能量先拿去付撤退費
        # （Codex 對局分析 f6698511 T7：超能量貼給第二隻 Dragapult，Meowth 換不下來，等它被打倒才上場）
        # 排在進化（90）、特性（88）之後：高手多半先進化、先用 Drakloak 看牌，再貼（高手對照 2026-10-18）
        return SCORE["ability"] - 2
    energy_type = card_info(board.hand_card_id(option.get("index", 0))).get("energyType")
    if option.get("inPlayArea") == AREA_ACTIVE and wasted_on_doomed_active(board, target, energy_type):
        return SCORE["attach_extra"]
    ability_energy = ABILITY_ENERGY.get(card_info(target.get("id")).get("name"))
    if ability_energy is not None and energy_type == ability_energy and ability_energy not in (target.get("energies") or []):
        # 惡能量貼給還沒有惡能量的 Munkidori，牠的特性才能用（Codex 敗局分析 d963cd2f；高手 15 比 1）
        return SCORE["attach_needed_active"] - 1
    if option.get("inPlayArea") == AREA_BENCH and board.power_now(board.my_active) == 0 and energy_type is not None:
        # 戰鬥場打不出東西（例：Dragapult ex 對 Crustle）：先補齊「貼完就能打 60 以上」的候補，再撤退換它
        # （Codex 敗局分析 d9eb6e13 T23：最後一張超能量貼給打 0 的 Dragapult，沒補齊能打 70 的 Drakloak，差 1 獎輸掉）
        after = dict(target, energies=(target.get("energies") or []) + [energy_type])
        if board.power_now(after) >= 60 > board.power_now(target):
            return SCORE["attach_needed_active"] + 2 + board.power_now(after) / 1000   # 打得越痛越優先
    missing = missing_energy(target.get("energies"), plan_cost(target.get("id")))
    if not missing:
        return SCORE["attach_extra"]
    on_active = option.get("inPlayArea") == AREA_ACTIVE
    # 同分時的優先順序（2026-10-17 實戰：超能量貼給了 Drakloak，差一個就能打的 Dragapult ex 反而沒拿到）：
    # 貼完就湊齊的 +4 ＞ 進化階段高的（2 階 +2、1 階 +1）＞ 戰鬥場 +1
    card = card_info(target.get("id"))
    bonus = (4 if len(missing) == 1 else 0) + (2 if card.get("stage2") else 1 if card.get("stage1") else 0) \
        + (1 if on_active else 0)
    if energy_type is not None and energy_type in missing and energy_type != COLORLESS:
        return SCORE["attach_needed_active" if on_active else "attach_needed_bench"] + bonus
    if COLORLESS in missing or energy_type is None:
        return SCORE["attach_colorless"] + bonus
    return SCORE["attach_extra"]  # 顏色不對：除非沒別的事做，不然不貼


SPREAD_BLOCKING_STADIUMS = {"Battle Cage"}   # 擋掉「放到備戰區的傷害指示物」的競技場


def opp_stadium_blocks_spread(board):
    """場上是對手放的、會擋 Phantom Dive 備戰區指示物的競技場，而我們的戰鬥場有放指示物的招式。"""
    stadium = (board.current.get("stadium") or [None])[0]
    if not stadium or card_info(card_id_of(stadium)).get("name") not in SPREAD_BLOCKING_STADIUMS:
        return False
    if isinstance(stadium, dict) and stadium.get("playerIndex") == board.my_index:
        return False
    active = board.my_active or {}
    return any(bench_spread(a) for a in card_info(active.get("id")).get("attacks") or [])


def opp_stadium_blocks_ex(board):
    """對手放的 Neutralization Zone 擋住我們已經能打的 ex（Codex 敗局分析 dfa490a5、bdaf4054：Jamming Tower 被留到丟掉）。"""
    stadium = (board.current.get("stadium") or [None])[0]
    if not stadium or card_info(card_id_of(stadium)).get("name") not in EX_BLOCKING_STADIUMS:
        return False
    if isinstance(stadium, dict) and stadium.get("playerIndex") == board.my_index:
        return False
    return any((card_info(m.get("id")).get("ex") or card_info(m.get("id")).get("megaEx")) and board.can_attack_now(m)
               for m in board.my_pokemon())


EVOLUTION_SEARCH_CARDS = {"Ultra Ball", "Poké Pad"}   # 能搜進化卡的（Poké Pad 不能搜規則寶可夢＝ex）


def missing_evolution(board, search_card):
    """場上有沒有一隻「下一階進化卡不在手上」的寶可夢（Poké Pad 只算非 ex 的進化卡）。"""
    hand = {card_info(card_id_of(c)).get("name") for c in board.me.get("hand") or []}
    for mon in board.my_pokemon():
        for evo_id in EVOLVES_INTO.get(card_info(mon.get("id")).get("name")) or []:
            evo_card = card_info(evo_id)
            if search_card == "Poké Pad" and (evo_card.get("ex") or evo_card.get("megaEx")):
                continue
            if evo_card.get("name") not in hand:
                return True
    return False


def wasted_on_doomed_active(board, target, energy_type):
    """戰鬥場是非 ex 配角（不在進化線上）、貼完這回合還是打不出招、對手現在就打得倒它，
    而備戰區有進化線要這個顏色 → 這張能量別給它（Codex 對局分析 a528c722 T5：超能量貼給 Munkidori，隔回合被打倒）。"""
    card = card_info(target.get("id"))
    if card.get("ex") or card.get("megaEx") or EVOLVES_INTO.get(card.get("name")) or card.get("stage1") or card.get("stage2"):
        return False
    if board.opp_threat(target) < (target.get("hp") or 0):
        return False
    after = (target.get("energies") or []) + [energy_type]
    if any(not missing_energy(after, attack_info(a).get("energies") or []) for a in card.get("attacks") or []):
        return False
    return bool(board.me.get("bench"))   # 備戰區有別人可以接這張能量


def facing_wall(board):
    """對手戰鬥場是 ex 打不動的牆（Crustle）。只在這種對局啟用省牌庫、保 Drakloak 等規則。"""
    return card_info((board.opp_active or {}).get("id")).get("name") in EX_IMMUNE_DEFENDERS


def wall_in_play(board):
    """對手場上（戰鬥場或備戰區）有 ex 打不動的牆 → 這場會拖很久，要省牌庫。"""
    return any(card_info((m or {}).get("id")).get("name") in EX_IMMUNE_DEFENDERS
               for m in (board.opp.get("active") or []) + (board.opp.get("bench") or []))


def wall_attacker_ready(board):
    """牆對局：我們的戰鬥場是非 ex、能打 60 以上、而且下回合挨得住 → 可以開始省牌庫。"""
    active = board.my_active
    card = card_info((active or {}).get("id"))
    return facing_wall(board) and active and not (card.get("ex") or card.get("megaEx")) \
        and board.power_now(active) >= 60 and (active.get("hp") or 0) > board.opp_threat(active)


def needs_energy_to_retreat(board):
    """戰鬥場那隻差 1 個能量就付得起撤退費（而且這回合還沒撤退過）。"""
    active = board.my_active
    if not active or board.current.get("retreated"):
        return False
    cost = card_info(active.get("id")).get("retreatCost") or 0
    return len(active.get("energies") or []) + 1 == cost


def score_play_card(board, option):
    card = card_info(board.hand_card_id(option.get("index", 0)))
    name, card_type = card.get("name"), card.get("cardType")

    if name in SWITCH_CARDS:
        # 備戰區有明顯更強、而且現在就能打的，才換
        return SCORE["retreat_ready"] if board.better_attacker_on_bench() else -1
    if name in GUST_CARDS:
        # 對手備戰區有一隻「拉上來就打得倒」的 → 拉（獎賞卡越多越優先）
        # 逐隻用 damage_against 算：戰鬥場是 Crustle 這類打不動的牆時，也能把後面打得動的拉上來
        # 但戰鬥場那隻本來就打得倒、獎賞卡又不比較少 → 不用出（2026-10-18 第 6 批：戰鬥場 140 HP 的
        # Fezandipiti ex 一擊就倒＝2 張，卻出 Boss 拉 70 HP 的 Dreepy＝1 張，還浪費一張 Boss）
        attacks = [o.get("attackId") for o in board.options if isinstance(o, dict) and o.get("type") == OPT_ATTACK]
        targets = [m for m in board.opp.get("bench") or [] if m and 0 < (m.get("hp") or 0)
                   <= max([board.damage_against(a, board.my_active, m) for a in attacks] or [0])]
        if not targets and board.power_now(board.my_active) == 0 and board.can_attack_now(board.my_active):
            # 戰鬥場完全打不出效果（例：Crustle＋Battle Cage）：拉一隻「兩擊打得倒」的上來，至少開始扣血
            # （Codex 敗局分析 5b1c90af T13：13 次 Phantom Dive 有 12 次對 Crustle 打 0）
            two_hit = [m for m in board.opp.get("bench") or [] if m and 0 < (m.get("hp") or 0) <= 2 * max(
                [board.damage_against(a, board.my_active, m) for a in attacks] or [0])]
            if two_hit:
                return SCORE["attack_ko"]
        if targets and board.can_attack_now(board.my_active):
            best_bench = max(prize_value(m.get("id")) for m in targets)
            if best_bench >= len(board.opp.get("prize") or [0] * 6):
                return SCORE["evolve"] + 5   # 拉上來打倒就贏了
            opp = board.opp_active
            active_ko = opp and 0 < (opp.get("hp") or 0) <= board.max_damage_vs(opp)
            if active_ko and prize_value(opp.get("id")) >= best_bench:
                return -1
            active = board.my_active or {}
            if not missing_energy(active.get("energies"), plan_cost(active.get("id"))):
                # 戰鬥場的計畫招式能量都齊了（Crispin 也幫不上它）→ Boss 取獎排在 Crispin（82）前面
                # （Codex 敗局分析 0fc82924 T13：用 Crispin 把能量貼給 Meowth，晚兩回合才 Boss 收 10 HP 的 Psyduck）
                return SCORE["attach_needed_bench"] + 3 + best_bench
            return SCORE["attack_ko"] + 5 + best_bench
        return -1
    if name in BOARD_CHANGING_CARDS:
        return -1  # TODO(Sean)：Energy Switch 等其他換位／移能量的卡，還沒寫條件，先不出

    thin = len(board.my_pokemon()) < THIN_BENCH
    if card_type == CARD_POKEMON and card.get("basic"):
        if board.bench_space() <= 0:
            return -1
        if thin:
            return SCORE["evolve"] - 1  # 場上快沒寶可夢了：先鋪，不然被打倒就直接輸
        names = [card_info(m.get("id")).get("name") for m in board.my_pokemon()]
        if not EVOLVES_INTO.get(name) and (card.get("hp") or 0) <= 30 and name in names:
            # 第二隻 Budew（30 HP）＝送對手一張獎賞卡（Codex 對局分析 0903e2e6：Mega Starmie 的備戰 50 點
            # 同回合打倒兩隻 Budew）
            return -1
        meowth_search = name == "Meowth ex" and not board.current.get("supporterPlayed") and not any(
            card_info(card_id_of(c)).get("cardType") == CARD_SUPPORTER for c in board.me.get("hand") or [])
        if len(board.opp.get("prize") or []) <= 1 and len(names) >= THIN_BENCH and not meowth_search:
            # 對手只剩 1 張獎賞卡：新放的基礎寶可夢只是給對手的最後一個目標（0903e2e6 T10：新 Dreepy 被收掉最後一獎）
            return -1
        if prize_value(board.hand_card_id(option.get("index", 0))) >= 2 and not EVOLVES_INTO.get(name):
            # 會送 2 張獎賞卡的配角 ex（Fezandipiti ex、Meowth ex）：不急著擺上備戰區當靶子
            # （2026-10-17 第 2 批：輸的 5 場裡這兩隻被打倒 3 次＝送對手 6 張）
            if name == "Meowth ex":
                hand_names = {card_info(card_id_of(c)).get("name") for c in board.me.get("hand") or []}
                # 缺能量、這回合還沒用支援者、手上沒有 Crispin 或抽牌支援者（Boss 不算解法）→ 上場搜 Crispin 補能量
                # （Codex 敗局分析 d9fe2e8e T9：缺火只打 Jet Headbutt，手上只有 Boss，沒放 Meowth 去搜 Crispin）
                if (energy_starved(board) or active_color_starved(board)) and not board.current.get("supporterPlayed") \
                        and not hand_names & (DRAW_SUPPORTERS | ENERGY_FETCH_CARDS):
                    return SCORE["attach_needed_bench"] + 1
                if not any(card_info(card_id_of(c)).get("cardType") == CARD_SUPPORTER for c in board.me.get("hand") or []):
                    return SCORE["draw"]  # Meowth ex 上場可以搜支援者：手上沒支援者時才值得
            return SCORE["item"] - 5
        return SCORE["bench_basic"]
    if name in DISCARD_COST_CARDS and not can_afford_discard(board, option.get("index", 0), DISCARD_COST_CARDS[name]):
        # 2026-10-18 第 6 批：手上只剩 Poké Pad 和 Drakloak 還出 Ultra Ball，丟掉 Drakloak 去搜另一張 Drakloak
        return -1
    if name in EVOLUTION_SEARCH_CARDS and (missing_engine(board) or (ready_upgrade(board) and name == "Ultra Ball")) \
            and missing_evolution(board, name):
        return SCORE["evolve"] - 3   # 場上有 Dreepy 卻沒有任何 Drakloak：先把找牌引擎搜出來（Codex 對局分析 76378bdb）
    if card_type == CARD_SUPPORTER and name in SEARCH_POKEMON_CARDS and energy_starved(board) \
            and any(card_info(card_id_of(c)).get("name") in ENERGY_FETCH_CARDS for c in board.me.get("hand") or []):
        # 缺能量而手上有 Crispin：Dawn 這類搜寶可夢的支援者別先用掉支援者額度（Codex 敗局分析 250b6969 T9）
        return SCORE["attach_needed_bench"] + 1
    if name in SEARCH_POKEMON_CARDS:
        if board.bench_space() <= 0:
            # 滿場也還能搜「場上缺的進化卡」（Codex 敗局分析 d963cd2f：滿場時 Poké Pad 一直留在手上；高手 13 比 0）
            return SCORE["draw"] + 5 if name in EVOLUTION_SEARCH_CARDS and missing_evolution(board, name) else SCORE["item"]
        if thin:
            return SCORE["evolve"] - 2
        if len(board.my_pokemon()) <= THIN_BENCH:
            # 場上剛好 3 隻：在打得倒的攻擊（60＋獎賞卡）之前先鋪場，攻擊會結束回合
            # （Codex 對局分析 412ef0e7 T9：Jet Headbutt 打得倒就直接打，沒先出 Poffin，主力倒下後只剩 Dreepy）
            return SCORE["attack_ko"] + 5
        return SCORE["draw"] + 5
    if name == "Crushing Hammer":
        # 擲硬幣拆對手 1 個能量：不花任何代價，攻擊會結束回合，所以對手場上有能量就在攻擊前先出
        # （Codex 敗局分析：20 場、41 次打不倒對手卻沒先出鎚子，對手留著完整能量反擊）
        if any(m and m.get("energies") for m in (board.opp.get("active") or []) + (board.opp.get("bench") or [])):
            return SCORE["attack_ko"] + 8
        return -1
    if name == "Judge" and board.judge_saves_active():
        return SCORE["attach_needed_active"] + 1   # 排在 Crispin（82～85）前面：支援者一回合只能一張
    deck_count = board.me.get("deckCount")
    if name == "Judge" and deck_count is not None and deck_count <= 2 and len(board.me.get("hand") or []) - 1 > 4:
        # 牌庫快抽光：Judge 把手牌洗回去（Codex 敗局分析 5b1c90af T31：牌庫 0、手牌 9，沒出 Judge，抽光判輸）
        return SCORE["attack_ko"] + 9
    if name == "Judge":
        # 雙方洗手牌、各抽 4：自己手上能用的牌少時，它就是抽牌支援者（Codex 敗局分析 f4a8c816、8d2c126f：
        # 手上只剩用不到的牌，Judge 被當干擾卡固定 30 分，一直沒出）
        if len(board.me.get("hand") or []) <= 4:
            return SCORE["draw"] + 6 if energy_starved(board) else SCORE["draw"]
        return SCORE["item"]
    if name == "Unfair Stamp":
        # 合法（上回合有寶可夢被打倒）時：對手手牌壓到 2 張、自己抽 5 張；攻擊會結束回合，所以攻擊前先出
        # （Codex 敗局分析 d62eedec：對手 9、11 張手牌時都沒出）
        if (board.opp.get("handCount") or 0) > 3:
            return SCORE["attack_ko"] + 9
        return SCORE["item"]
    if card_type == CARD_STADIUM and (opp_stadium_blocks_spread(board) or opp_stadium_blocks_ex(board)):
        # 對手的 Battle Cage 會擋掉 Phantom Dive 放到備戰區的指示物 → 先用自己的競技場蓋掉
        # （Codex 敗局分析 db338914：三個回合的指示物都被擋，手上有 Jamming Tower 卻沒出）
        return SCORE["attack_ko"] + 9
    if name in DISRUPTION_CARDS:
        return SCORE["item"]  # 干擾對手（拆能量、洗手牌）：自己佈局好了再說
    if name in ENERGY_FETCH_CARDS:
        # 主力缺能量、手上又沒有對的能量 → 每回合唯一一張支援者先給 Crispin
        # （2026-10-17 第 3 批：這種回合手上有 Crispin 17 次，只打出 8 次，其他被 Lillie's／Boss's 搶走）
        return SCORE["attach_needed_bench"] + 2 if energy_starved(board) else SCORE["draw"] - 5
    if name in RECOVERY_CARDS:
        # Night Stretcher：棄牌堆有主力要的能量或主力線寶可夢才用，不然留著
        return SCORE["draw"] + 5 if recoverable_value(board) else SCORE["item"] - 5
    if name in ("Lillie's Determination", "Lillie’s Determination"):
        deck_count = board.me.get("deckCount")
        draw_n = 8 if len(board.me.get("prize") or []) >= 6 else 6
        if deck_count is not None and deck_count + len(board.me.get("hand") or []) - 1 - draw_n <= 0:
            return -1   # 用完牌庫會變 0（Codex 對局分析 308e86ac T31：牌庫 1 張還出 Lillie's）
        if wall_attacker_ready(board) and draw_n > len(board.me.get("hand") or []) - 1:
            return -1   # 牆對局、攻擊手已在打：會淨減牌庫的 Lillie's 先不用
        net_gain = len(board.me.get("hand") or []) - 1 - draw_n   # >0：洗回去的比抽的多，牌庫反而變多
        if wall_in_play(board) and deck_count is not None and deck_count <= 20 and len(board.me.get("hand") or []) >= 3 \
                and net_gain <= 0:
            return -1   # 對手有 Crustle、牌庫剩 20 以下：手上還有牌就先不用 Lillie's
        if wall_in_play(board) and deck_count is not None and deck_count <= 10 and net_gain > 0:
            # 牌庫快見底、手牌又多：用 Lillie's 把牌洗回去補牌庫（Codex 對手研究：StartupBros 對 rimeblade
            # 的長局 T49 用它把牌庫從 3 補到 19，最後贏）
            return SCORE["attach_needed_active"]
        if active_color_starved(board) and len(board.me.get("hand") or []) <= 2 \
                and not board.current.get("energyAttached"):
            # 戰鬥場缺一種顏色、還能手貼、手牌只剩這麼少：先抽，不要為了 1 獎的小攻擊跳過
            # （Codex 敗局分析 86ccb9d7 T13：手牌只剩 Budew＋Lillie's，直接 Jet Headbutt）
            return SCORE["attack_ko"] + 7
    if card_type == CARD_SUPPORTER:
        # 主力缺顏色、手上又補不上：抽牌（Lillie's 等）優先於 Dawn 這類搜寶可夢的（55）
        # （Codex 對局分析 f6698511 T13：先用 Dawn，支援者額度用掉，看到的 Crispin 用不了）
        return SCORE["draw"] + 6 if energy_starved(board) else SCORE["draw"]
    if card_type == CARD_ITEM:
        return SCORE["draw"] if board.bench_space() > 0 else SCORE["item"]
    if card_type == CARD_TOOL:
        return SCORE["tool"]
    if card_type == CARD_STADIUM:
        return SCORE["stadium"]
    return 45  # 看不到手牌時的保守分數


def choose_main(board, legal):
    stop_setting_up = board.turn_action_count > MAX_ACTIONS_PER_TURN
    best, best_score = None, None
    for action in legal:
        option = single_pick(board, action)
        if option is None:
            continue
        if stop_setting_up and option.get("type") not in (OPT_ATTACK, OPT_END_TURN):
            continue  # 動作太多了：只在攻擊與結束回合之間選
        score = score_main_option(board, option)
        if best_score is None or score > best_score:
            best, best_score = action, score
    return best


# ---------------------------------------------------------------- 其他題目
def choose_other(board, legal):
    """主要回合以外的題目，依題型分開處理；認不得的題型退回「第一個非空的合法動作」。"""
    sel_type, ctx = board.select.get("type"), board.select.get("context")

    if sel_type == SELECT_YES_NO:
        return pick_by_type(board, legal, (OPT_YES,))          # 進化時抽牌之類的可選效果：要
    if sel_type == SELECT_NUMBER:
        return pick_max_number(board, legal)                   # 高手 51/51 次選最大
    if ctx == CTX_BENCH_COUNTERS:
        return pick_counter_target(board, legal)               # Phantom Dive 的 6 個指示物
    if ctx == CTX_OPP_TARGET and card_info((board.select.get("effect") or {}).get("id")).get("name") in COUNTER_MOVERS:
        moved = pick_counter_move_target(board, legal)
        if moved is not None:
            return moved
    if ctx in (CTX_NEW_ACTIVE, CTX_SWITCH, CTX_OPP_TARGET):
        return pick_pokemon(board, legal)
    if card_info((board.select.get("effect") or {}).get("id")).get("name") in ENERGY_FETCH_CARDS:
        crispin = pick_crispin(board, legal, ctx)
        if crispin is not None:
            return crispin
    if (sel_type, ctx) == (1, CTX_OPENING_ACTIVE):
        return pick_opening_active(board, legal) or (legal[0] if legal else None)
    if ctx == CTX_DISCARD_ENERGY and card_info((board.select.get("effect") or {}).get("id")).get("name") == "Crushing Hammer":
        hammer = pick_hammer_target(board, legal)
        if hammer is not None:
            return hammer
    if ctx == CTX_DISCARD_HAND:
        return pick_cards(board, legal, keep_value, prefer="low")
    if ctx in (CTX_TO_HAND, CTX_DECK_TO_BENCH):
        return pick_cards(board, legal, want_value, prefer="high")

    non_empty = [a for a in legal if a != "[]"]
    return non_empty[0] if non_empty else None


CTX_CRISPIN_ATTACH_CARD = 22    # (1, 22) Crispin 第二張（直接貼上場的那張，顏色要不同）
CTX_ATTACH_TARGET = 21          # (1, 21) 貼 contextCard 這張能量到哪一隻


CTX_OPENING_ACTIVE = 1     # (1, 1) 開局從手牌選戰鬥寶可夢
CTX_DISCARD_ENERGY = 30    # (4, 30) 選要丟的能量（Crushing Hammer 拆對手的也是這題）


def pick_opening_active(board, legal):
    """開局的戰鬥寶可夢：Budew（撤退費 0、不用能量就能打）＞ 其他非 ex 的配角 ＞ Dreepy（主力線留在備戰區養）
    ＞ 會送 2 張獎賞卡的 ex（Codex 對局分析 27c62713：以前固定選第一個，常讓 Meowth ex 卡在戰鬥場）"""
    def rank(action):
        option = single_pick(board, action)
        card = card_info(board.option_card_id(option)) if option else {}
        if not card:
            return -1
        if card.get("ex") or card.get("megaEx"):
            return 0
        if card.get("name") == "Budew":
            return 3
        return 1 if EVOLVES_INTO.get(card.get("name")) else 2
    choices = [a for a in legal if single_pick(board, a)]
    return max(choices, key=rank) if choices else None


def pick_hammer_target(board, legal):
    """Crushing Hammer 拆哪個能量：對手戰鬥場的優先（它下回合就要攻擊），再來獎賞卡多的、身上能量少的
    （拆掉唯一一個最能延後它開打）。Codex 對局分析 f6698511 T7：以前固定拆第一個，拆到備戰區 Reshiram。"""
    def rank(action):
        option = single_pick(board, action)
        if not option or board.option_side(option) != "opp":
            return None
        mon = board.in_play(option.get("area"), option.get("index"), "opp") or {}
        return (1 if option.get("area") == AREA_ACTIVE else 0, prize_value(mon.get("id")),
                -len(mon.get("energies") or []))
    # 同分（例：同一隻身上的不同能量）照原本順序拿第一個——高手 17 次裡有 14 次是這樣
    scored = [(rank(a), -i, a) for i, a in enumerate(legal)]
    scored = [x for x in scored if x[0] is not None]
    return max(scored)[2] if scored else None


def energy_urgency(board, energy_type, mon):
    """把這個顏色的能量貼給 mon 有多急：計畫招式缺這個顏色才算；貼完就湊齊、進化階段高、在戰鬥場的更急。"""
    if not mon or energy_type is None:
        return 0
    missing = missing_energy(mon.get("energies"), plan_cost(mon.get("id")))
    if energy_type not in missing:
        return 1 if COLORLESS in missing else 0
    card = card_info(mon.get("id"))
    return 10 + (5 if len(missing) == 1 else 0) + (2 if card.get("stage2") else 1 if card.get("stage1") else 0) \
        + (1 if mon is board.my_active else 0)


def best_urgency(board, energy_type):
    return max([energy_urgency(board, energy_type, m) for m in board.my_pokemon()] or [0])


def pick_crispin(board, legal, ctx):
    """Crispin：牌庫拿 2 張不同顏色的基本能量，第一張（context 7）加到手牌，第二張（context 22）直接貼上。
    Codex 敗局分析：以前三題都選第一個，9 場把能量貼給 Meowth ex 這類不需要的、或選錯顏色。
    - 這回合已經手貼過：手牌那張這回合用不到 → 最急的顏色留給「直接貼上」，手牌拿第二急的
    - 還沒手貼：手牌拿最急的（等一下手貼），直接貼上的拿另一個顏色"""
    def energy_of(action):
        option = single_pick(board, action)
        return card_info(board.option_card_id(option)).get("energyType") if option else None

    choices = [a for a in legal if single_pick(board, a)]
    if not choices:
        return None
    if ctx == CTX_ATTACH_TARGET:
        energy_type = card_info(card_id_of(board.select.get("contextCard"))).get("energyType")
        return max(choices, key=lambda a: energy_urgency(
            board, energy_type, board.in_play(single_pick(board, a).get("area"), single_pick(board, a).get("index"))))
    if ctx == CTX_CRISPIN_ATTACH_CARD:
        return max(choices, key=lambda a: best_urgency(board, energy_of(a)))
    if ctx == CTX_TO_HAND:
        ranked = sorted({energy_of(a) for a in choices} - {None}, key=lambda t: -best_urgency(board, t))
        if not ranked:
            return None
        want = ranked[1] if board.current.get("energyAttached") and len(ranked) > 1 else ranked[0]
        return next(a for a in choices if energy_of(a) == want)
    return None


def pick_by_type(board, legal, wanted_types):
    """照 wanted_types 的順序，挑第一個種類符合的單選動作。"""
    for wanted in wanted_types:
        for action in legal:
            option = single_pick(board, action)
            if option is not None and option.get("type") == wanted:
                return action
    return None


def pick_max_number(board, legal):
    best, best_n = None, None
    for action in legal:
        option = single_pick(board, action)
        if option is not None and option.get("type") == OPT_NUMBER:
            n = option.get("number") or 0
            if best_n is None or n > best_n:
                best, best_n = action, n
    return best


def pick_counter_target(board, legal):
    """一次放一個傷害指示物（剩幾個看 select.remainDamageCounter），照高手的做法：
    1. 剩下的指示物夠打倒的 → 放那隻（獎賞卡多的優先，再來 HP 高的，已經受傷的優先，免得浪費）
    2. 都打不倒 → 先放「已經受傷的」，再挑 HP 最低的，替下一回合鋪路
       （2026-10-17 比較 6 種放法：這種最接近高手，訓練組 69% → 76%、驗收組 85% → 86%）"""
    remain = (board.select.get("remainDamageCounter") or 1) * DAMAGE_COUNTER
    scored = []
    for action in legal:
        option = single_pick(board, action)
        if option is None:
            continue
        mon = board.in_play(option.get("area"), option.get("index"), board.option_side(option))
        hp = (mon or {}).get("hp") or 0
        if hp <= 0:
            continue  # 已經 0 HP（等著被打倒）的不用再放
        if counter_immune(mon) and len(legal) > 1:
            continue   # 帶 Rock Fighting Energy 等的：引擎實測放上去 0 傷害（Codex 敗局分析 61a5e057：浪費 18 個指示物）
        hurt = hp < ((mon or {}).get("maxHp") or hp)
        # 試過 Codex 建議的「先放到下一擊打得倒的門檻」（2026-10-18）：和高手選法不同的 89 次裡，
        # 高手 73 次照舊規則（集中放已受傷的），只有 10 次照新規則 → 不採用
        energies = len(mon.get("energies") or [])   # 完全同分時打能量多的（快能接替攻擊；四位高手 9 比 6）
        if hp <= remain:
            key = (1, prize_value(mon.get("id")), hp, hurt, 0, energies)
        else:
            key = (0, 0, 0, hurt, -hp, energies)
        scored.append((key, action))
    return max(scored)[1] if scored else None


COUNTER_MOVERS = {"Munkidori": 30}   # 特性：把自己身上的傷害指示物移到對手（最多 3 個＝30）


def pick_counter_move_target(board, legal):
    """Munkidori 移傷害：移完後「這回合打得倒」的優先——戰鬥場直接打；備戰區要手上有 Boss's Orders 而且
    這回合還沒用支援者（或有 Prime Catcher）。都沒有就回傳 None，照舊規則選。
    （Codex 對局分析 b57dfd61 T9：30 點放 Staryu；放備戰區 Mega Starmie 210→180，再 Boss＋Phantom Dive 就拿最後 3 獎；
     四位 Dragapult 高手 1 比 0 支持）"""
    moved = COUNTER_MOVERS[card_info((board.select.get("effect") or {}).get("id")).get("name")]
    hand = {card_info(card_id_of(c)).get("name") for c in board.me.get("hand") or []}
    can_gust = bool(hand & {"Prime Catcher"}) or (bool(hand & GUST_CARDS) and not board.current.get("supporterPlayed"))
    best, best_gain = None, 0
    for action in legal:
        option = single_pick(board, action)
        if not option or board.option_side(option) != "opp":
            continue
        mon = board.in_play(option.get("area"), option.get("index"), "opp") or {}
        hp, dmg = mon.get("hp") or 0, board.max_damage_vs(mon)
        if 0 < hp <= moved:
            gain = prize_value(mon.get("id"))                       # 移過去就直接打倒
        elif hp > dmg >= hp - moved and (option.get("area") == AREA_ACTIVE or can_gust):
            gain = prize_value(mon.get("id"))                       # 移完變成這回合打得倒
        else:
            continue
        if gain > best_gain:
            best, best_gain = action, gain
    return best


COUNTER_IMMUNE_ENERGIES = {"Rock Fighting Energy", "Mist Energy"}


def opp_has_hand_attack(board):
    """對手場上有沒有「依手牌張數打傷害」的招式（Alakazam 的 Powerful Hand）。"""
    for mon in (board.opp.get("active") or []) + (board.opp.get("bench") or []):
        for attack_id in card_info((mon or {}).get("id")).get("attacks") or []:
            if board.hand_counter_damage(attack_id, 1):
                return True
    return False


def counter_immune(mon):
    return any(card_info(card_id_of(c)).get("name") in COUNTER_IMMUNE_ENERGIES for c in (mon or {}).get("energyCards") or [])


def pokemon_value(board, mon, side):
    """挑寶可夢時的分數（2026-10-17 用高手對戰的訓練組／驗收組比較過幾種規則）：
    自己的（上戰鬥場、Switch）：身上能量多的 → 現在就能打的 → 傷害高的。驗收組 78% → 85%
    對手的（選目標、Boss's Orders）：HP 最低的 → 身上能量多的（威脅大）。驗收組 30% → 67%
      舊規則「獎賞卡多優先」會一直挑 HP 320 的 Dragapult ex，等於挑最難打的。"""
    if not mon:
        return (-1, 0, 0)
    energies = len(mon.get("energies") or [])
    if side == "me":
        # 先看「現在能打多少」，再看能量數（Codex 對局分析：以前會推出有 1 個能量、卻還不能攻擊的 Drakloak，
        # 而不是撤退費 0 的 Budew；高手對照 3 比 2）。上場後還會被打倒的，排在挨得住的後面
        atk = best_attack(mon.get("id"))
        survives = 1 if (mon.get("hp") or 0) > board.opp_threat(mon) else 0
        # 試過「戰力相同時 Drakloak 排在配角後面」（Codex 建議）：高手一致率（挑一隻上戰鬥場）62% → 55～58%，不採用
        return (survives if board.power_now(mon) >= 60 else 0, board.power_now(mon), energies,
                atk[1] if atk else 0)
    if board.select.get("context") == CTX_SWITCH:
        # Boss's Orders：拉上來是為了打倒拿獎賞卡 →「打得倒的」先，其中獎賞卡多的優先，再來 HP 低的。
        # 一定要先看打不打得倒：出 Boss 的理由就是「有打得倒的目標」，選目標時要用同一個條件
        # （Codex 審查抓到：舊規則只看獎賞卡，會拉 320 HP 打不倒的 Dragapult ex，放過 60 HP 的 Dreepy）
        # 打得倒的裡面挑 HP 高的（＝進化過、對手投資比較多的：同流派時 Drakloak 比 Dreepy 值得打）；
        # 打不倒的才挑 HP 低的
        hp = mon.get("hp") or 0
        killable = 0 < hp <= board.max_damage_vs(mon)
        return (1 if killable else 0, prize_value(mon.get("id")), hp if killable else -hp, energies)
    return (-(mon.get("hp") or 0), energies, 0)


def pick_pokemon(board, legal):
    best, best_key = None, None
    for action in legal:
        option = single_pick(board, action)
        if option is None or option.get("type") != OPT_CARD:
            continue
        side = board.option_side(option)
        key = pokemon_value(board, board.in_play(option.get("area"), option.get("index"), side), side)
        if best_key is None or key > best_key:
            best, best_key = action, key
    if best is None:
        non_empty = [a for a in legal if a != "[]"]
        return non_empty[0] if non_empty else None
    return best


def want_value(board, card_id, in_hand=False):
    """搜牌／拿牌時，這張卡有多想要（越大越想要）。看不到是什麼卡回傳 None。
    in_hand＝這張卡本來就在手上（丟牌時用）：數「手上已經有幾張」時要扣掉它自己。"""
    card = card_info(card_id)
    if not card:
        return None
    in_play = board.names_in_play()
    if card.get("cardType") == CARD_POKEMON:
        if card.get("basic") and board.bench_space() > 0 and len(board.my_pokemon()) < THIN_BENCH:
            # 場上不到 3 隻：先拿能馬上放下的基礎寶可夢，比進化卡優先（2026-10-18 第 9 批：場上只有 Budew＋剛放下的
            # Dreepy，Ultra Ball 搜 Drakloak（這回合本來就不能進化），被快攻一回合打倒一隻，第 6、8 回合就沒寶可夢判輸）
            return 95 if EVOLVES_INTO.get(card.get("name")) else 92
        if card.get("evolvesFrom") in in_play:
            # 能馬上進化的；但手上的同名卡已經夠場上每一隻進化了，就不用再拿
            # （2026-10-18 第 6 批：場上只有 1 隻 Dreepy、手上已有 Drakloak，Ultra Ball 還是搜 Drakloak）
            targets = sum(1 for m in board.my_pokemon() if card_info(m.get("id")).get("name") == card.get("evolvesFrom"))
            return 40 if hand_count(board, card.get("name")) - (1 if in_hand else 0) >= targets else 90
        if card.get("basic") and EVOLVES_INTO.get(card.get("name")):
            return 70 if board.bench_space() > 0 else 20       # 進化線的起點
        return 50 if board.bench_space() > 0 else 15
    if card.get("cardType") in (CARD_BASIC_ENERGY, CARD_SPECIAL_ENERGY):
        # 拿了這回合就能貼上、湊齊某隻的計畫招式（戰鬥場；或備戰區的 Drakloak 等。Codex 對局分析 308e86ac：
        # Night Stretcher 撿 Dreepy 不撿火能量；四位高手 1 比 0）
        if not board.current.get("energyAttached") and not in_hand \
                and card.get("energyType") not in hand_energy_types(board) \
                and any(missing_energy(m.get("energies"), plan_cost(m.get("id"))) == [card.get("energyType")]
                        for m in board.my_pokemon()):
            # 拿了這回合就能貼上、湊齊戰鬥場的計畫招式（Codex 敗局分析 f4a8c816：Night Stretcher 撿 Dreepy 不撿超能量；高手 6 比 1）
            return 92
        return 60 if card.get("energyType") in needed_colors(board) else 25
    if card.get("name") == "Unfair Stamp" and (board.opp.get("handCount") or 0) >= 8 and opp_has_hand_attack(board) \
            and "Unfair Stamp" not in {card_info(card_id_of(c)).get("name") for c in board.me.get("hand") or []}:
        return 94   # 對手靠手牌張數打傷害（Powerful Hand）：Stamp 把他壓到 2 張（Codex 對局分析 c39d05e7：對手 19、23 張手牌時沒拿）
    if card.get("name") in GUST_CARDS and not board.current.get("supporterPlayed") \
            and not {card_info(card_id_of(c)).get("name") for c in board.me.get("hand") or []} & GUST_CARDS:
        opp = board.opp_active or {}
        active_prizes = prize_value(opp.get("id")) if 0 < (opp.get("hp") or 0) <= board.max_damage_vs(opp) else 0
        best = max([prize_value(m.get("id")) for m in board.opp.get("bench") or []
                    if m and 0 < (m.get("hp") or 0) <= board.max_damage_vs(m)] or [0])
        if best > active_prizes:
            return 94   # 備戰區有現在就打得倒、獎賞卡更多的 → 拿 Boss（Codex 敗局分析 5e464d31：放過 130 HP 的 Mega Lucario）
    if card.get("cardType") == CARD_SUPPORTER:
        if card.get("name") in ENERGY_FETCH_CARDS and energy_starved(board) and not board.current.get("supporterPlayed"):
            return 85   # 缺能量又還沒用支援者：Crispin 一張補 2 個能量（Codex 敗局分析 c0e4aafc、d601a6ff）
        if card.get("name") in DRAW_SUPPORTERS and (energy_starved(board) or active_color_starved(board)) \
                and not board.current.get("supporterPlayed") \
                and not any(card_info(card_id_of(c)).get("name") in DRAW_SUPPORTERS | ENERGY_FETCH_CARDS
                            for c in board.me.get("hand") or []):
            return 84   # 缺色、手上沒抽牌也沒 Crispin：拿 Lillie's 去找（Codex 對局分析 7fbdf3b8：一直拿錯色能量、Boss）
        return 40
    if card.get("name") in SEARCH_POKEMON_CARDS:
        return 45
    if card.get("name") in DISRUPTION_CARDS:
        return 20
    return 30


def needed_colors(board):
    """我們需要的能量顏色：場上寶可夢的計畫招式還缺的，加上手牌裡寶可夢（含進化型）的計畫招式要的。
    （2026-10-17 實戰：場上只有 Fezandipiti 時，Ultra Ball 把火、超能量丟了——只看場上會漏掉手牌裡的 Dreepy 線）"""
    needs = {e for m in board.my_pokemon() for e in missing_energy(m.get("energies"), plan_cost(m.get("id")))}
    for card in board.me.get("hand") or []:
        cid = card_id_of(card)
        if card_info(cid).get("cardType") == CARD_POKEMON:
            needs.update(plan_cost(cid))
    needs.discard(COLORLESS)
    return needs


def active_color_starved(board):
    """戰鬥場計畫招式缺的有色能量，手上（這回合還能貼的話）補不上。"""
    active = board.my_active
    if not active:
        return False
    missing = set(missing_energy(active.get("energies"), plan_cost(active.get("id")))) - {COLORLESS}
    usable = set() if board.current.get("energyAttached") else hand_energy_types(board)
    return bool(missing) and not (missing & usable)


def hand_energy_types(board):
    return {card_info(card_id_of(c)).get("energyType") for c in board.me.get("hand") or []
            if card_info(card_id_of(c)).get("cardType") in (CARD_BASIC_ENERGY, CARD_SPECIAL_ENERGY)}


def energy_starved(board):
    """場上寶可夢的計畫招式還缺有顏色的能量，而手上沒有任何一張補得上。"""
    missing = {e for m in board.my_pokemon() for e in missing_energy(m.get("energies"), plan_cost(m.get("id")))}
    missing.discard(COLORLESS)
    # 這回合已經手貼過：手上的能量要下回合才貼得出去，Crispin 的「直接貼上」才補得到
    # （Codex 敗局分析 5ad6e948 T9：前排 Dragapult 只缺火、手上有火但已手貼，選了 Unfair Stamp 沒出 Crispin）
    usable = set() if board.current.get("energyAttached") else hand_energy_types(board)
    return bool(missing) and not (missing & usable)


def recoverable_value(board):
    """棄牌堆裡有沒有值得撿回來的：需要的顏色的基本能量，或能接上場上進化線的寶可夢。"""
    needs = needed_colors(board)
    in_play = board.names_in_play()
    for card in board.me.get("discard") or []:
        info = card_info(card_id_of(card))
        if info.get("cardType") == CARD_BASIC_ENERGY and info.get("energyType") in needs:
            return True
        if info.get("cardType") == CARD_POKEMON and (info.get("evolvesFrom") in in_play or EVOLVES_INTO.get(info.get("name"))):
            return True
    return False


def my_supporter_used(board):
    """這回合「我們」用過支援者了嗎。對手的效果（Xerosic 逼丟牌）出題時，supporterPlayed 記的是對手的
    （Codex 敗局分析 86ccb9d7 T2：被當成我們用過，丟掉唯一的 Lillie's）。"""
    effect = board.select.get("effect") or {}
    if effect.get("playerIndex") is not None and effect.get("playerIndex") != board.my_index:
        return False
    return bool(board.current.get("supporterPlayed"))


def hand_count(board, name):
    return sum(1 for c in board.me.get("hand") or [] if card_info(card_id_of(c)).get("name") == name)


def keep_value(board, card_id):
    """丟牌時，這張卡有多想留（越小越先丟）。
    2026-10-18 第 6 批：第 1 回合場上只有 Fezandipiti ex，Ultra Ball 丟了 Boss's Orders 和唯一的火能量，
    留下兩張 Poké Pad。所以：基本能量至少和搜尋卡一樣值得留（這副牌只有 10 張能量）；
    同一張物品卡手上有兩張以上時，重複的先丟。"""
    value = want_value(board, card_id, in_hand=True)
    if value is None:
        return 50
    card = card_info(card_id)
    if card.get("name") in DRAW_SUPPORTERS and not my_supporter_used(board) \
            and sum(1 for c in board.me.get("hand") or [] if card_info(card_id_of(c)).get("name") in DRAW_SUPPORTERS) == 1:
        return 75
    if card.get("name") in ENERGY_FETCH_CARDS and hand_count(board, card.get("name")) == 1:
        return 75   # 唯一的 Crispin 別丟（Codex 對局分析 7fbdf3b8 T1：丟了 Crispin，首次 Phantom Dive 拖到 T13）   # 唯一的抽牌支援者別丟（Codex 敗局分析 6a4693e4：Ultra Ball 丟了唯一的 Lillie's，之後兩回合停機）
    if card.get("cardType") == CARD_BASIC_ENERGY:
        value = max(value, 45)
    elif card.get("cardType") == CARD_ITEM and hand_count(board, card.get("name")) >= 2:
        value -= 15
    elif card.get("cardType") == CARD_POKEMON and hand_count(board, card.get("name")) >= 2 and value < 90:
        value -= 15   # 這回合用不到的重複寶可夢（例：場上還沒有 Drakloak 時的第二張 Dragapult ex）
    return value


ALL_COPIES_PENALTY = 25


def discard_penalty(board, picked_ids):
    """丟牌組合的額外代價：把手上同名寶可夢「全部」丟光（Codex 敗局分析 ca4848f4：兩張 Dragapult ex
    逐張看都便宜，但不能兩張都丟，不然進化線斷掉）。"""
    penalty = 0
    draw_in_hand = sum(1 for c in board.me.get("hand") or [] if card_info(card_id_of(c)).get("name") in DRAW_SUPPORTERS)
    draw_picked = sum(1 for c in picked_ids if card_info(c).get("name") in DRAW_SUPPORTERS)
    if draw_in_hand and draw_picked >= draw_in_hand and not my_supporter_used(board):
        penalty += ALL_COPIES_PENALTY   # 丟光所有抽牌支援者（Codex 敗局分析 12972564：兩張 Lillie's 一起丟）
    for name in {card_info(c).get("name") for c in picked_ids}:
        copies = hand_count(board, name)
        if copies >= 2 and card_info(next(c for c in picked_ids if card_info(c).get("name") == name)).get(
                "cardType") == CARD_POKEMON and sum(1 for c in picked_ids if card_info(c).get("name") == name) >= copies:
            penalty += ALL_COPIES_PENALTY
    return penalty


def can_afford_discard(board, hand_index, n):
    """出這張卡要丟 n 張手牌：手上（扣掉它自己）夠 n 張，而且最便宜的 n 張都不是「想要的」（keep_value < 60）。"""
    others = [card_id_of(c) for i, c in enumerate(board.me.get("hand") or []) if i != hand_index]
    if board.me.get("hand") is None:
        return True   # 看不到手牌（公開紀錄）：不擋
    if len(others) < n:
        return False
    cheapest = sorted(keep_value(board, cid) for cid in others)[:n]
    # 場上有 Dreepy 卻沒有任何 Drakloak／Dragapult、手上也沒有：找引擎比留一張能量重要，門檻放寬到 75
    # （Codex 對局分析 76378bdb T13：嫌火能量太貴不出 Ultra Ball，整場沒進化過）
    limit = 75 if missing_engine(board) or ready_upgrade(board) else 60
    return all(v < limit for v in cheapest)


def ready_upgrade(board):
    """場上有一隻「能量已經夠進化型打招式」的寶可夢，而那張進化卡不在手上（例：火＋超的 Drakloak、手上沒 Dragapult ex）。
    （Codex 敗局分析 e9622a74 T6：嫌超能量太貴不出 Ultra Ball，Drakloak 只打 70 就被打倒；進化後可打 200、HP 320）"""
    hand = {card_info(card_id_of(c)).get("name") for c in board.me.get("hand") or []}
    for mon in board.my_pokemon():
        for evo_id in EVOLVES_INTO.get(card_info(mon.get("id")).get("name")) or []:
            evo = card_info(evo_id)
            if evo.get("name") in hand:
                continue
            if any(not missing_energy(mon.get("energies"), attack_info(a).get("energies") or [])
                   and (attack_info(a).get("damage") or 0) > 0 for a in evo.get("attacks") or []):
                return True
    return False


def missing_engine(board):
    names = [card_info(m.get("id")) for m in board.my_pokemon()]
    has_base = any(c.get("basic") and EVOLVES_INTO.get(c.get("name")) for c in names)
    has_evolved = any(c.get("stage1") or c.get("stage2") for c in names)
    hand_evo = any(card_info(card_id_of(c)).get("stage1") for c in board.me.get("hand") or [])
    return has_base and not has_evolved and not hand_evo


def pick_cards(board, legal, value_fn, prefer):
    """挑卡題（可能一次挑好幾張）：算每個合法組合的總價值，挑最好的。
    prefer="high"：搜牌拿想要的（能多拿就多拿）；prefer="low"：丟牌丟最不想留的。"""
    best, best_key = None, None
    for action in legal:
        picks = parse_action(action)
        if picks is None:
            continue
        values = []
        for i in picks:
            option = board.options[i] if 0 <= i < len(board.options) else None
            if not isinstance(option, dict):
                values = None
                break
            v = value_fn(board, board.option_card_id(option))
            values.append(40 if v is None else v)              # 看不到的卡當中等價值
        if values is None:
            continue
        if prefer == "high":
            key = (sum(values), len(values))
        else:
            ids = [board.option_card_id(board.options[i]) for i in picks]
            key = (-(sum(values) + discard_penalty(board, [c for c in ids if c])), -len(values))
        if best_key is None or key > best_key:
            best, best_key = action, key
    if best is None:
        non_empty = [a for a in legal if a != "[]"]
        return non_empty[0] if non_empty else None
    return best


def decide(obs, legal):
    board = Board(obs)
    if board.select.get("type") == SELECT_MAIN:
        return choose_main(board, legal)
    return choose_other(board, legal)


# ---------------------------------------------------------------- 安全外殼（平台呼叫的入口）
def safe_default(legal):
    for action in legal:
        if action != FORFEIT:
            return action
    return legal[0] if legal else "[0]"


def act(context):
    """平台的入口。整個包在 try 裡：任何錯誤都不能冒出去（冒出去＝這場直接判輸）。"""
    legal = []
    try:
        legal = [a for a in (context.get("legalActions") or []) if isinstance(a, str)]
        choice = decide(context.get("observation") or {}, [a for a in legal if parse_action(a) is not None])
        if choice in legal and choice != FORFEIT:
            return choice
        return safe_default(legal)
    except Exception:
        try:
            return safe_default(legal)
        except Exception:
            return "[0]"


choose_action = act  # 平台也接受 choose_action 這個名字
