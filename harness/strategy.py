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
THIN_BENCH = 3  # 場上（含戰鬥場）不到這個數量，就優先鋪寶可夢
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
        my_type = card_info(attacker.get("id")).get("energyType")
        target = card_info(defender.get("id"))
        if target.get("weakness") is not None and target.get("weakness") == my_type:
            dmg *= 2
        if target.get("resistance") is not None and target.get("resistance") == my_type:
            dmg -= 30
        return max(dmg, 0)

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
        return SCORE["evolve"]

    if kind == OPT_ATTACH_ENERGY:
        return score_attach(board, option)

    if kind == OPT_PLAY_FROM_HAND:
        return score_play_card(board, option)

    if kind == OPT_ABILITY:
        return SCORE["ability"]

    if kind == OPT_ATTACK:
        damage = board.damage_against(option.get("attackId"), board.my_active, board.opp_active)
        opp = board.opp_active
        if opp and damage >= (opp.get("hp") or 0) > 0:
            return SCORE["attack_ko"] + prize_value(opp.get("id"))  # 打得倒：拿獎賞卡，優先
        return SCORE["attack"] + damage / 1000                   # 打不倒：佈局之後再打，同分挑傷害高的

    if kind == OPT_RETREAT:
        # 戰鬥場打不出招式、備戰區有一隻已經可以打 → 撤退換牠上來
        ready = [m for m in board.me.get("bench") or [] if m and board.can_attack_now(m)]
        if not board.can_attack_now(board.my_active) and ready:
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
    missing = missing_energy(target.get("energies"), plan_cost(target.get("id")))
    if not missing:
        return SCORE["attach_extra"]
    energy_type = card_info(board.hand_card_id(option.get("index", 0))).get("energyType")
    on_active = option.get("inPlayArea") == AREA_ACTIVE
    if energy_type is not None and energy_type in missing and energy_type != COLORLESS:
        return SCORE["attach_needed_active" if on_active else "attach_needed_bench"] + (2 if on_active else 0)
    if COLORLESS in missing or energy_type is None:
        return SCORE["attach_colorless"] + (2 if on_active else 0)
    return SCORE["attach_extra"]  # 顏色不對：除非沒別的事做，不然不貼


def score_play_card(board, option):
    card = card_info(board.hand_card_id(option.get("index", 0)))
    name, card_type = card.get("name"), card.get("cardType")

    if name in SWITCH_CARDS:
        # 戰鬥場打不出招式、備戰區有人準備好了，才換
        ready = [m for m in board.me.get("bench") or [] if m and board.can_attack_now(m)]
        return SCORE["retreat_ready"] if ready and not board.can_attack_now(board.my_active) else -1
    if name in GUST_CARDS:
        # 對手備戰區有一隻「拉上來就打得倒」的 → 拉（獎賞卡越多越優先）
        damage = board.best_damage_now()
        targets = [m for m in board.opp.get("bench") or [] if m and 0 < (m.get("hp") or 0) <= damage]
        if targets and board.can_attack_now(board.my_active):
            return SCORE["attack_ko"] + 5 + max(prize_value(m.get("id")) for m in targets)
        return -1
    if name in BOARD_CHANGING_CARDS:
        return -1  # TODO(Sean)：Energy Switch 等其他換位／移能量的卡，還沒寫條件，先不出

    thin = len(board.my_pokemon()) < THIN_BENCH
    if card_type == CARD_POKEMON and card.get("basic"):
        if board.bench_space() <= 0:
            return -1
        return SCORE["evolve"] - 1 if thin else SCORE["bench_basic"]  # 場上快沒寶可夢了：先鋪，不然被打倒就直接輸
    if name in SEARCH_POKEMON_CARDS:
        if board.bench_space() <= 0:
            return SCORE["item"]
        return SCORE["evolve"] - 2 if thin else SCORE["draw"] + 5
    if name in DISRUPTION_CARDS:
        return SCORE["item"]  # 干擾對手（拆能量、洗手牌）：自己佈局好了再說
    if card_type == CARD_SUPPORTER:
        return SCORE["draw"]
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
    if ctx in (CTX_NEW_ACTIVE, CTX_SWITCH, CTX_OPP_TARGET):
        return pick_pokemon(board, legal)
    if ctx == CTX_DISCARD_HAND:
        return pick_cards(board, legal, keep_value, prefer="low")
    if ctx in (CTX_TO_HAND, CTX_DECK_TO_BENCH):
        return pick_cards(board, legal, want_value, prefer="high")

    non_empty = [a for a in legal if a != "[]"]
    return non_empty[0] if non_empty else None


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
        hurt = hp < ((mon or {}).get("maxHp") or hp)
        if hp <= remain:
            key = (1, prize_value(mon.get("id")), hp, hurt, 0)
        else:
            key = (0, 0, 0, hurt, -hp)
        scored.append((key, action))
    return max(scored)[1] if scored else None


def pokemon_value(board, mon, side):
    """挑寶可夢時的分數（2026-10-17 用高手對戰的訓練組／驗收組比較過幾種規則）：
    自己的（上戰鬥場、Switch）：身上能量多的 → 現在就能打的 → 傷害高的。驗收組 78% → 85%
    對手的（選目標、Boss's Orders）：HP 最低的 → 身上能量多的（威脅大）。驗收組 30% → 67%
      舊規則「獎賞卡多優先」會一直挑 HP 320 的 Dragapult ex，等於挑最難打的。"""
    if not mon:
        return (-1, 0, 0)
    energies = len(mon.get("energies") or [])
    if side == "me":
        atk = best_attack(mon.get("id"))
        return (energies, 1 if board.can_attack_now(mon) else 0, atk[1] if atk else 0)
    if board.select.get("context") == CTX_SWITCH:
        # Boss's Orders：把對手拉上來是為了打倒拿獎賞卡 → 獎賞卡多的優先（這題用舊規則一致率較高：72% vs 61%）
        return (prize_value(mon.get("id")), -(mon.get("hp") or 0), energies)
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


def want_value(board, card_id):
    """搜牌／拿牌時，這張卡有多想要（越大越想要）。看不到是什麼卡回傳 None。"""
    card = card_info(card_id)
    if not card:
        return None
    in_play = board.names_in_play()
    if card.get("cardType") == CARD_POKEMON:
        if card.get("evolvesFrom") in in_play:
            return 90                                          # 能馬上進化的
        if card.get("basic") and EVOLVES_INTO.get(card.get("name")):
            return 70 if board.bench_space() > 0 else 20       # 進化線的起點
        return 50 if board.bench_space() > 0 else 15
    if card.get("cardType") in (CARD_BASIC_ENERGY, CARD_SPECIAL_ENERGY):
        needs = [e for m in board.my_pokemon() for e in missing_energy(m.get("energies"), plan_cost(m.get("id")))]
        return 60 if card.get("energyType") in needs else 25
    if card.get("cardType") == CARD_SUPPORTER:
        return 40
    return 30


def keep_value(board, card_id):
    """丟牌時，這張卡有多想留（越小越先丟）。"""
    value = want_value(board, card_id)
    return 50 if value is None else value


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
            key = (-sum(values), -len(values))
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
