# 策略練習（Sean 寫）

> 每個練習都是改 `harness/strategy.py` 裡標 `TODO(Sean)` 的函式。
> 改完一定跑這兩個：
> ```
> python3 tests/replay_test.py     # 必須 PASS（不會當掉、一定合法）
> python3 tests/agreement.py       # 看哪一類跟贏家更一致了
> ```

## 練習 1：什麼時候該攻擊？（✅ 2026-10-17 已在 v1 完成，可以當範例讀）

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

v1 的做法（`score_main_option` 的 `OPT_ATTACK` 分支＋`Board.damage_against`）：算上弱點 ×2、抗性 −30，打得倒給 60＋獎賞卡數，打不倒給 40（在有價值的佈局之後才打）。

## v1 已經做了什麼（2026-10-17，對照 Dragapult 高手的一致率 43% → 53%）
| 規則 | 在哪 | 從高手學到的 |
|---|---|---|
| Phantom Dive 的指示物：先放「打得倒的」，再放 HP 最低的 | `pick_counter_target` | 43.7% → 68.5% |
| 選數字一律選最大 | `pick_max_number` | 0% → 100% |
| 特性排在進化之後、其他動作之前 | `SCORE["ability"]` | 28% → 69% |
| 能量看「進化後的招式」要什麼顏色 | `score_attach`、`plan_cost` | 25% → 27～32% |
| 戰鬥場打不出、備戰區有人準備好 → 撤退／Switch | `score_main_option`、`score_play_card` | 0% → 49% |
| Boss's Orders 只在「拉上來就打得倒」時出 | `score_play_card` | — |
| 挑誰上場：自己的挑能打的；對手的挑打得倒、獎賞卡多的 | `pick_pokemon` | 51% → 76% |

## 接下來的練習（Sean）
- **練習 2：丟牌**（`keep_value`）——現在只有 22% 跟高手一樣。Ultra Ball 要丟 2 張時，該丟什麼？提示：第一次真的上場後，看 `data/runs/` 的紀錄，比賽時手牌看得到。
- **練習 3：Lillie's Determination／Judge 什麼時候出**——這兩張會洗掉手牌，手上好牌多的時候出反而虧。
- **練習 4：Budew 第一回合**——還打不出 Phantom Dive 時，用 Itchy Pollen 鎖對手物品卡（Alakazam 靠 Rare Candy、Team Rocket 靠 Ultra Ball）。
- **練習 5：搜牌**（`want_value`）——需要比賽時的 `select.deck` 才知道搜到的是哪張卡，第一次上場後再寫。
