# 策略練習（Sean 寫）

> 每個練習都是改 `harness/strategy.py` 裡標 `TODO(Sean)` 的函式。
> 改完一定跑這兩個：
> ```
> python3 tests/replay_test.py     # 必須 PASS（不會當掉、一定合法）
> python3 tests/agreement.py       # 看哪一類跟贏家更一致了
> ```

## 練習 1：什麼時候該攻擊？

### 問題
`tests/agreement.py` 顯示：**贏家選攻擊的時候，v0 只有約 20% 也選攻擊**，大部分時候它還在出手牌。
原因：v0 的分數表裡，出訓練家卡（50 分）永遠比攻擊（10 分）高，所以只要手上還有牌能出，它就不攻擊。

寶可夢卡牌的基本節奏是「先佈局，再攻擊」——但有一個情況該**馬上**攻擊：**這一下能把對手的戰鬥寶可夢打倒（KO）**。打倒就拿獎賞卡，先拿完 6 張的人贏。

### 你要做的
在 `score_main_option()` 的 `OPT_ATTACK` 分支裡，判斷「這個招式能不能打倒對手的戰鬥寶可夢」：
- 能 → 給一個很高的分數（比所有佈局動作都高）
- 不能 → 維持低分（先佈局）

### 用得到的東西
| 想知道 | 怎麼拿 |
|---|---|
| 招式的基礎傷害 | `attack_info(option["attackId"])["damage"]` |
| 對手戰鬥寶可夢還剩多少 HP | `board.opp_active["hp"]`（`maxHp` 是滿血值） |
| 對手戰鬥寶可夢是哪張卡 | `card_info(board.opp_active["id"])` |
| 我方戰鬥寶可夢的屬性 | `card_info(board.my_active["id"])["energyType"]`（例：7＝惡） |
| 對手的弱點屬性 | `card_info(board.opp_active["id"])["weakness"]`（屬性代碼，跟 energyType 同一套；None＝沒有弱點） |

規則提示：攻擊方的屬性＝防守方的弱點時，傷害 **×2**。

### 要小心的
1. `board.opp_active` 可能是 `None`（戰鬥場暫時是空的）——先檢查再取值，不然會拋例外（雖然 `act()` 會接住，但那一步就退回預設了）。
2. 很多招式的 `damage` 是 0，但說明文字寫「每個正面 30」之類的變動傷害——練習 1 先只看 `damage`，變動傷害之後再處理。
3. 抗性（`resistance`）會減傷害，練習 1 可以先忽略。

### 想一想（寫進 Obsidian 筆記的「自己的理解」）
- 打不倒的時候，攻擊還有沒有意義？什麼情況下「先打一下」比「繼續佈局」好？
- 對手是 ex（被打倒給 2 張獎賞卡）、Mega ex（給 3 張）時，優先順序該不該不一樣？

## 之後的練習（預告）
- 練習 2：Switch／Boss's Orders 什麼時候出（v0 目前完全不出）
- 練習 3：能量要貼給誰（看顏色，不只看數量）
- 練習 4：`choose_other` 依題型分別處理（題型對照見 `docs/protocol.md`）
