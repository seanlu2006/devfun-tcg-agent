# 環境分析（TCG Playground S3，2026-10-17）

> 資料：排行榜前 15 名＋最近對戰，共 150 場公開對戰（`tools/fetch_public.py 150 15`）。
> 工具：`tools/deck_profile.py`（牌組側寫、流派勝率）。牌表張數用「每張實體卡的 serial 編號」數出來——是下限，大多已經數到 57～60 張。
> 注意：手牌和牌庫在公開紀錄裡看不到；樣本小（各流派互打大多只有 5～16 場），勝率只能看方向。

## 三大流派

| 流派 | 場數 | 勝率 | 打 Alakazam | 打 Dragapult | 打 Team Rocket | 前 15 名有幾位 |
|---|---|---|---|---|---|---|
| Alakazam | 120 | 45% | 34/68（同流派） | 4/13 | **1/16** | 6 |
| **Dragapult** | 54 | 57% | **9/13** | 8/16（同流派） | **10/15** | 5（含第 1 名） |
| Team Rocket | 43 | 63% | **15/16** | 5/15 | 3/6（同流派） | 3 |

**剋制關係**：Dragapult ＞ Team Rocket ＞ Alakazam，而且 Dragapult 也剋 Alakazam。用最多人的 Alakazam 反而最弱。

## Dragapult（我們選的）

**核心**：Dreepy → Drakloak → **Dragapult ex**（2 階，320 HP，沒有弱點，撤退 1）。
主力招式 **Phantom Dive**：費用只要 **火＋超 2 個能量**，200 傷害，外加 **6 個傷害指示物**（60 點）自由分配到對手的備戰寶可夢。實測平均每次打出 188～200。

**牌表**（`decks/dragapult_v1.json`，照第 1 名 StartupBros 的 57 張＋補 3 張）：
- 寶可夢 17：Dreepy×4、Drakloak×4、Dragapult ex×3、Munkidori×2、Budew×2、Meowth ex、Fezandipiti ex
- 訓練家 33：Crushing Hammer×4、Lillie's Determination×4、Ultra Ball×4、Poké Pad×4、Buddy-Buddy Poffin×4、Boss's Orders×3、Night Stretcher×3、Jamming Tower×2、Crispin×2、Unfair Stamp、Judge、Dawn
- 能量 10：火×4、超×4、惡×2

**怎麼打**
1. 開局盡量把 Dreepy 鋪滿備戰區（Buddy-Buddy Poffin 搜 HP ≤ 70 的基礎寶可夢，Dreepy 正好 70）。
2. 能量**先貼在 Dreepy／Drakloak 上**——進化後能量會留著，Dragapult 一上場就能打。需要的是「1 火＋1 超」，不是隨便 2 個。
3. Drakloak 的特性用來找牌；有 Dragapult ex 就進化。
4. 每回合用 Phantom Dive：200 打戰鬥場，6 個指示物優先放到**能被打倒**的備戰寶可夢上（例：剩 ≤ 60 HP 的 Abra、Tarountula），一次拿 2 份獎賞卡的節奏。
5. 第一回合還打不出 Phantom Dive 時，Budew 的 Itchy Pollen（不用能量）可以鎖住對手下一回合的物品卡——Alakazam 和 Team Rocket 都很依賴物品卡。
6. Crushing Hammer 拆對手能量，拖慢對手。

**長處**
- 費用低（2 能量）、傷害高、還能打備戰區 → 很適合打「需要先在備戰區養小寶可夢」的 Alakazam（Abra 30 HP）與 Team Rocket（Tarountula）。
- 沒有弱點、HP 320，很難一擊被打倒。
- 打法單一（幾乎每回合都同一招），**對我們這種規則型程式最友善**。

**短處**
- 要進化 2 次（Dreepy → Drakloak → Dragapult），起手卡不到 Dreepy 或被早期打倒，會整個慢下來。
- 需要**兩種顏色**的能量；只貼到火或只貼到超都打不出主力招式。
- Dragapult ex 被打倒會給對手 2 份獎賞卡。
- 同流派互打（8/16）沒有優勢。

## Team Rocket（第二選擇，沒選的原因）
- 核心：Team Rocket's Spidops（Rocket Rush：每隻 Team Rocket 寶可夢 30 傷害）、Mewtwo ex（Erasure Ball 160＋丟備戰能量加傷）、Kangaskhan ex（Wicked Impact：這回合有出 Team Rocket 支援者就 +100）。
- 打 Alakazam 15/16，但打 Dragapult 只有 5/15。
- **沒選的原因**：傷害靠很多卡的配合（場上 Team Rocket 寶可夢的數量、這回合有沒有先出 Team Rocket 支援者），規則型程式比較難開好；而且被 Dragapult 剋。

## Alakazam（最多人用，最弱）
- 核心：Abra → Kadabra → Alakazam（Rare Candy 跳階），主力招式 Powerful Hand（傷害看手牌數量，實測平均 175～260）。
- 進化時可以抽牌（`(9, 43)` 是非題就是這個）。
- 弱點：Abra 只有 30 HP，很怕 Phantom Dive 的備戰區傷害；也怕 Budew 鎖物品卡（Rare Candy、Poké Pad 都是物品）。
