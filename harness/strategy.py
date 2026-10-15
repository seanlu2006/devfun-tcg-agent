"""dev.fun Arena TCG agent — 出牌決策。

平台每遇到一個決策點就呼叫 act(context)，我們要從 context["legalActions"] 挑一個字串回傳。
三層結構：
  1. act()：安全外殼。任何例外都退回合法動作（程式當掉＝直接判輸）。
  2. Board：把 observation 裡的數字代碼翻成看得懂的東西（代碼意思見 docs/protocol.md）。
  3. 策略函式：score_main_option() 與 choose_other()。標 TODO(Sean) 的地方是要自己改的策略。

限制：沙盒是 Python 3.11、沒有網路，只能用標準函式庫和 assets/ 裡的檔案。
"""
import json
import os

# ---------------------------------------------------------------- 代碼常數（見 docs/protocol.md）
SELECT_MAIN = 0          # 主要回合動作
SELECT_YES_NO = 9        # 是／否確認

OPT_YES = 1
OPT_NO = 2
OPT_PLAY_FROM_HAND = 7   # 從手牌打出一張卡
OPT_ATTACH_ENERGY = 8    # 把手牌的能量貼到場上
OPT_EVOLVE = 9           # 進化
OPT_ABILITY = 10         # 使用特性
OPT_RETREAT = 12         # 撤退
OPT_ATTACK = 13          # 使用招式
OPT_END_TURN = 14        # 結束回合

AREA_ACTIVE = 4
AREA_BENCH = 5

CARD_POKEMON = 0
CARD_ITEM = 1
CARD_TOOL = 2
CARD_SUPPORTER = 3
CARD_STADIUM = 4
CARD_BASIC_ENERGY = 5
CARD_SPECIAL_ENERGY = 6

FORFEIT = "__forfeit__"
MAX_ACTIONS_PER_TURN = 40  # 保險：一個回合動作太多就收手，避免卡在某種循環裡


# ---------------------------------------------------------------- 卡牌資料（隨 bundle 打包）
def _catalog_paths():
    paths = []
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        paths.append(os.path.join(here, "..", "assets", "catalog.json"))
    except NameError:  # 有些執行環境沒有 __file__
        pass
    paths.append(os.path.join(os.getcwd(), "assets", "catalog.json"))
    return paths


def _load_catalog():
    for path in _catalog_paths():
        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
            cards = {int(k): v for k, v in raw["cards"].items()}
            attacks = {int(k): v for k, v in raw["attacks"].items()}
            return cards, attacks
        except Exception:
            continue
    return {}, {}  # 讀不到就當沒有資料，策略會退回保守做法


CARDS, ATTACKS = _load_catalog()


def card_info(card_id):
    return CARDS.get(card_id) or {}


def attack_info(attack_id):
    return ATTACKS.get(attack_id) or {}


def parse_action(action):
    """'[0,2]' → [0, 2]；'[]' → []。"""
    inner = action.strip()[1:-1]
    return [int(x) for x in inner.split(",") if x.strip()]


# ---------------------------------------------------------------- 盤面工具
class Board:
    """把一個決策點的 observation 包成好讀的物件。"""

    def __init__(self, obs):
        self.obs = obs or {}
        self.current = self.obs.get("current") or {}
        players = self.current.get("players") or []
        my_index = self.current.get("yourIndex", 0)
        self.me = players[my_index] if my_index < len(players) else {}
        self.opp = players[1 - my_index] if len(players) == 2 else {}
        self.select = self.obs.get("select") or {}
        self.options = self.select.get("option") or []

    # --- 自己的牌
    def hand_card_id(self, hand_index):
        """手牌第 hand_index 張的 cardId；看不到手牌（公開紀錄被遮掉）就回傳 None。"""
        hand = self.me.get("hand")
        if not hand or hand_index >= len(hand):
            return None
        card = hand[hand_index]
        return card.get("id") if isinstance(card, dict) else card

    def in_play(self, area, index, side="me"):
        """場上某隻寶可夢（area 4＝戰鬥場、5＝備戰區）。"""
        player = self.me if side == "me" else self.opp
        zone = player.get("active" if area == AREA_ACTIVE else "bench") or []
        return zone[index] if index < len(zone) else None

    @property
    def my_active(self):
        return (self.me.get("active") or [None])[0]

    @property
    def opp_active(self):
        return (self.opp.get("active") or [None])[0]

    def bench_space(self):
        return self.me.get("benchMax", 5) - len(self.me.get("bench") or [])

    def energy_needed(self, pokemon):
        """這隻寶可夢最便宜的招式還差幾個能量（粗估，不看能量顏色）。"""
        if not pokemon:
            return 0
        costs = [len(attack_info(a).get("energies") or []) for a in card_info(pokemon["id"]).get("attacks") or []]
        if not costs:
            return 0
        return max(0, min(costs) - len(pokemon.get("energies") or []))

    @property
    def turn_action_count(self):
        return self.current.get("turnActionCount", 0)


# ---------------------------------------------------------------- 策略（TODO(Sean)：這一段是你的）
def score_main_option(board, option):
    """主要回合時，替一個選項打分數，分數最高的會被選。

    v0 只是讓流程能跑的陽春版：先佈局（進化、貼能量、放寶可夢、出訓練家卡），最後攻擊。
    TODO(Sean)：這裡是策略的核心。可以改進的方向：
      - 貼能量要看顏色，不是只看數量
      - 選招式要看對手剩多少 HP、能不能一擊打倒（拿獎賞卡）
      - 什麼時候該撤退、該留哪張支援者
      - 哪些訓練家卡有副作用不該亂出
    """
    kind = option.get("type")

    if kind == OPT_EVOLVE:
        return 90

    if kind == OPT_ATTACH_ENERGY:
        target = board.in_play(option.get("inPlayArea"), option.get("inPlayIndex", 0))
        if option.get("inPlayArea") == AREA_ACTIVE and board.energy_needed(target) > 0:
            return 80  # 戰鬥場還打不出招式，先補它
        return 60

    if kind == OPT_PLAY_FROM_HAND:
        card = card_info(board.hand_card_id(option.get("index", 0)))
        card_type = card.get("cardType")
        if card_type == CARD_POKEMON and card.get("basic"):
            return 70 if board.bench_space() > 0 else -1
        if card_type in (CARD_ITEM, CARD_SUPPORTER):
            return 50
        if card_type in (CARD_TOOL, CARD_STADIUM):
            return 40
        return 45  # 看不到手牌時的保守分數

    if kind == OPT_ABILITY:
        return 55

    if kind == OPT_ATTACK:
        damage = attack_info(option.get("attackId")).get("damage") or 0
        return 10 + damage / 1000  # 攻擊會結束回合，所以排在佈局之後；同分時挑傷害高的

    if kind == OPT_RETREAT:
        return -10  # v0 不撤退

    if kind == OPT_END_TURN:
        return 0

    return 1  # 不認得的選項：比結束回合高一點，但不優先


def choose_main(board, legal):
    if board.turn_action_count > MAX_ACTIONS_PER_TURN:
        return pick_by_type(board, legal, (OPT_ATTACK, OPT_END_TURN))

    best, best_score = None, None
    for action in legal:
        picks = parse_action(action)
        if len(picks) != 1 or picks[0] >= len(board.options):
            continue
        score = score_main_option(board, board.options[picks[0]])
        if best_score is None or score > best_score:
            best, best_score = action, score
    return best


def choose_other(board, legal):
    """主要回合以外的題目（挑卡、是／否、選數字…）。

    TODO(Sean)：v0 很粗糙。select.context 代表是哪種效果（搜牌庫、丟手牌、選攻擊對象…），
    要先在 docs/protocol.md 把 context 分辨清楚，才能針對性地選。
    """
    if board.select.get("type") == SELECT_YES_NO:
        return pick_by_type(board, legal, (OPT_YES,))
    non_empty = [a for a in legal if a != "[]"]
    return non_empty[0] if non_empty else None


def pick_by_type(board, legal, wanted_types):
    """照 wanted_types 的順序，挑第一個種類符合的單選動作。"""
    for wanted in wanted_types:
        for action in legal:
            picks = parse_action(action)
            if len(picks) == 1 and picks[0] < len(board.options) and board.options[picks[0]].get("type") == wanted:
                return action
    return None


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
    legal = [a for a in (context.get("legalActions") or []) if isinstance(a, str)]
    try:
        choice = decide(context.get("observation") or {}, legal)
        if choice in legal and choice != FORFEIT:
            return choice
    except Exception:
        pass  # 不讓任何錯誤冒出去：冒出去＝這場直接判輸
    return safe_default(legal)


choose_action = act  # 平台也接受 choose_action 這個名字
