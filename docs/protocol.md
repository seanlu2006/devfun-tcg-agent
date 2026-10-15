# 決策點協定（逆向整理）

> 官方 introspection **沒有**定義下面這些數字代碼。表裡的意思是從 20 場公開對戰（`tools/explore_options.py`）統計「選了某個選項之後，下一步出現哪種 log」反推出來的。
> 信心欄：**高**＝樣本多、而且 log 對得上；**中**＝有例子但還沒逐一驗證；**低**＝猜測。發現對不上就更新這份文件。
> 引擎：`pokemon-tcg`，版本 `2+cabt@1.32.0+seeded-rng@1`（不是公開套件，本機沒有模擬器）。

## 每個決策點長這樣
```
context = {
  "observation": obs,          # 盤面（同 pending-actions 的 obs）
  "legalActions": ["[0]", "[1]", "[0,1]", "[]", ...]   # 只能從這裡面挑一個字串
}
```
- `legalActions` 的字串是 `obs["select"]["option"]` 的**索引**，不是動作名稱。多選題會出現 `"[0,1]"` 這種組合，`"[]"` 代表「一個都不選」（只有 minCount＝0 時才會出現）。
- `obs["current"]["yourIndex"]` 是自己在 `players` 裡的位置，**每次都要重新讀**，不要假設是 0。
- 公開對戰紀錄裡手牌是 `null`（被遮掉）。比賽沙盒裡自己的手牌看得到，但程式還是要能處理 `None`。

## select（被問的是哪一種題目）
| select.type | 常見 context | 意思 | 信心 |
|---|---|---|---|
| 0 | 0 | **主要回合動作**（出牌、貼能量、進化、特性、撤退、攻擊、結束回合） | 高 |
| 1 | 1～22 | **挑卡**：從某個區域挑 minCount～maxCount 張（搜牌庫、丟手牌、選對象…），context 代表是哪種效果 | 中 |
| 2 | 28 | 挑某隻寶可夢身上的能量 | 低 |
| 4 | 30、33 | 挑要移動或丟棄的能量（帶 count） | 中 |
| 5 | 34 | 挑一張特定的卡（cardId＋serial） | 低 |
| 7 | 37 | 未確認 | 低 |
| 8 | 38、40 | 選一個數字 | 中 |
| 9 | 41～43 | 是／否確認 | 中 |

## option.type（每個選項的種類）
| option.type | 欄位 | 選了之後的 log | 意思 | 信心 |
|---|---|---|---|---|
| 0 | number | 16 | 選數字 | 中 |
| 1 | — | 4 | 「是」 | 中 |
| 2 | — | （無） | 「否」 | 中 |
| 3 | area, index, playerIndex | 依效果而定 | 某區域的某張卡 | 高 |
| 5 | area, index, playerIndex, energyIndex | — | 某隻寶可夢身上的某個能量 | 低 |
| 6 | area, index, playerIndex, energyIndex, count | 6 | 能量＋數量 | 中 |
| 7 | index | 10 | **從手牌打出第 index 張**（寶可夢放到備戰區、訓練家卡） | 高 |
| 8 | area, index, inPlayArea, inPlayIndex | 11 | **把手牌的能量貼到場上**（area 2＝手牌 → inPlayArea 4 戰鬥場／5 備戰區） | 高 |
| 9 | area, index, inPlayArea, inPlayIndex | 12 | **進化**（手牌的進化卡 → 場上那隻） | 高 |
| 10 | area, index | 6 等 | **使用場上寶可夢的特性**（area 4／5） | 中 |
| 12 | — | （之後會問換誰上場） | **撤退** | 中 |
| 13 | attackId | 15、16 | **使用招式**（attackId 對照 `/tcg/attacks`） | 高 |
| 14 | — | — | **結束回合** | 高 |
| 15 | cardId, serial | 16 | 指定某一張實體卡 | 低 |

## area（區域代碼）
| area | 推測 | 信心 |
|---|---|---|
| 1 | 牌庫 | 中（搜牌時 index 很大） |
| 2 | 手牌 | 高 |
| 4 | 戰鬥場（active） | 高 |
| 5 | 備戰區（bench） | 高 |
| 3、6 | 棄牌堆、獎賞卡（未確認） | 低 |

## log.type（`obs["logs"]` 裡發生過的事）
| log.type | 欄位 | 推測 | 信心 |
|---|---|---|---|
| 6 | playerIndex | 抽牌 | 中 |
| 8 | cardIdActive, cardIdBench | 戰鬥場與備戰區交換 | 中 |
| 10 | cardId | 打出一張卡 | 高 |
| 11 | cardId, cardIdTarget | 貼能量 | 高 |
| 12 | cardId, cardIdTarget | 進化 | 高 |
| 15 | attackId, cardId | 使用招式 | 高 |
| 16 | cardId, value, putDamageCounter | 造成傷害或放傷害指示物 | 高 |
| 0～5、14、18、22 | playerIndex | 回合開始、洗牌、擲硬幣等（未分辨） | 低 |
