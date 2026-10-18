# 對局筆記

實戰敗局整理（2026-10-18，Codex 唯讀分析＋Claude 驗證）。數字來自 data/runs 的實戰紀錄，樣本小，只當方向。

## N's Zoroark ex（cinderfox）

- N's Zoroark ex 280 HP、弱草；Night Joker（惡＋惡）複製備戰區 N's 寶可夢的招式，供招式者不用能量 → 拆 Reshiram 的能量擋不住。
- 危險的供招式者：Reshiram（Virtuous Flame 170；Powerful Rage 依自身傷害，打過 400）、Zekrom（70／250）。
- 我們輸的主因：主攻手卡在戰鬥場換不出來（Meowth ex 付不起撤退費）、最後一隻 Drakloak 被進化掉、缺火能量。對應修正見 commit 9b73292。

## 第三輪：Marnie's Grimmsnarl ex／Mega Starmie／Teal Mask Ogerpon ex

- **Marnie’s Grimmsnarl ex：180＋30 的雙線取獎，Morpeko 也能先開獎**
  
  Grimmsnarl **320 HP、弱草、無抗性**。Shadow Bullet 花兩惡，打前排 180、備戰一隻 30。Morpeko **70 HP、弱草、零撤退**；Spiky Wheel 為 `20＋40×身上惡能量數`。
  
  `5b53aaa5` 的 Morpeko 帶五惡，打出 220，先收鳥。其餘常見路線是前排打主力，備戰順便收 Budew。猴弱惡，Shadow Bullet 對它是 **360**。我們的三場 Phantom Dive 分別拖到 T8、T8、T10，另三場完全沒打出。

  | matchId | 結果 | 首次 Phantom Dive | 對手首次擊倒 | 我方被擊倒；對手獎賞 |
  |---|---|---|---|---|
  | `5b53aaa5` | 敗 | T8／65 | T5／44 | 鳥、Budew×2、Pult；6 |
  | `fc2acf97` | 敗 | T10／64 | T15／108 | Dreepy、Pult、Budew×2、猴；6 |
  | `ff92ad28` | 勝 | T8／94 | T5／63 | Drak、Budew×2；3 |
  | `ca4848f4` | 敗 | 無 | T5／39 | Budew×2、Drak×2、猴；4 |
  | `60c06996` | 敗 | 無 | T5／55 | Drak、Budew×2、Pult、Dreepy；6 |
  | `373cfe84` | 敗 | 無 | T7／44 | Budew×2、Pult、Drak×2；6 |

- **Mega Starmie：一水就能拿獎，50 點備戰傷害切斷進化線**
  
  Mega Starmie **330 HP、弱雷、無抗性，倒下送三獎**。這五場使用的主攻都是 Jetting Blow：一水打前排 120、備戰一隻 50。另有三無色的 Nebula Beam 210。
  
  最快 T2 就開始拿獎。`49b04e7c` T4 同時失去 Drak 和 Budew；`ea7b1cbc` T4 也一次掉兩隻。能打出 Phantom Dive 的三場，首發都到 T7。對手則可輪替兩隻海星，分散我們的正面傷害。

  | matchId | 結果 | 首次 Phantom Dive | 對手首次擊倒 | 我方被擊倒；對手獎賞 |
  |---|---|---|---|---|
  | `ccdc2de6` | 勝 | T7／70 | T6／60 | Budew、Drak；2 |
  | `80699533` | 敗 | 無 | T4／35 | Dreepy、貓；1 |
  | `0ac2a552` | 敗 | 無 | T6／29 | 貓；0 |
  | `49b04e7c` | 敗 | T7／85 | T2／18 | 猴、Drak、Budew×2、Pult；6 |
  | `ea7b1cbc` | 敗 | T7／47 | T4／29 | Drak、Budew、Dreepy、猴、Pult；6 |

- **Teal Mask Ogerpon：能量越滾越大，早期送掉帶能量的 Drak 很傷**
  
  Ogerpon **210 HP、弱火、無抗性**。Myriad Leaf Shower 為 `30＋30×雙方戰鬥寶可夢能量總數`。盤面搭配 Meganium，後期傷害可超過滿血 Pult 的 320。Hydrapple ex 則有 **330 HP、弱火**，Syrup Storm 隨己方全場草能量增加傷害。
  
  Dragapult 是龍屬性，貼火能量也不會打到火弱點。Phantom Dive 的正面 200，對滿血 Ogerpon 剛好差 10。四場正常敗局都在 T4 先送一獎；其中三場首先倒下的是 Drak，連同能量一起失去。

  | matchId | 結果 | 首次 Phantom Dive | 對手首次擊倒 | 我方被擊倒；對手獎賞 |
  |---|---|---|---|---|
  | `8028e5a0` | 敗 | T11／139 | T4／43 | Budew×2、Pult×2；6 |
  | `bcf64b50` | 超時勝 | 無 | T6／57 | Drak、猴；2 |
  | `f53c9217` | 敗 | T9／113 | T4／50 | Drak、Budew、猴、Pult×2；6 |
  | `fd138f20` | 超時勝 | T5／48 | T8／95 | Pult、Drak、Budew；4 |
  | `c0e4aafc` | 敗 | 無 | T4／40 | Drak、Budew×2、Pult、猴；6 |
  | `210c087e` | 敗 | T7／82 | T4／49 | Drak、Pult×2、Budew；6 |
  | `6964d9e8` | 超時勝 | T5／53 | 無 | 無；0 |
  | `27c01ba8` | 勝 | T11／76 | 無 | 無；0 |


對應修正見 commit 22e50d3（快被打倒時換健康的主攻手、接替戰鬥寶可夢先看戰力）。

## 整體統計（2026-10-18，80 場，Codex 整理）

| 指標 | 勝局 | 敗局 |
|---|---:|---:|
| 打出過 Phantom Dive | 41/43 | 19/37 |
| 我方第 2 回合已有 Drakloak | 36/43 | 20/37 |
| 前 3 回合鋪出的 Dreepy（平均） | 3.12 | 2.95 |
| 首次被打倒的是 Dreepy／Drakloak | 10/43 | 15/37 |

勝負的分水嶺是「引擎有沒有轉起來」：敗局有 18/37 整場打不出 Phantom Dive；有打出的對局，首次使用的回合中位數勝敗都是 T7。多鋪 Dreepy 的差異很小。相關性，不是因果。

## 對手研究（2026-10-18，公開對戰）

資料：`data/raw/scout/*.json`，共 145 場不重複對局。同一對手也納入其他 `scouted` 檔中的出場，因此 usecommitt 共 33 場、jade_yak_3292 共 30 場。五副牌皆重建到 60 張：後手 serial 減 60 後合併公開卡位，各副牌均無卡位衝突。

以下勝敗均從該對手視角記錄。T 是紀錄中的雙方累計回合；主攻起動中位數只計算有使用主力招式的對局。matchId 簡寫前八碼。規則屬待測候選；本次全程唯讀，未修改策略或重跑對戰。

### raps：Crustle／Mega Kangaskhan ex（12 勝 18 敗）

- **寶可夢／能量，23 張**：Dwebble×3、Crustle×3、Mega Kangaskhan ex×4；基本草×1、Mist Energy×4、Spiky Energy×4、Grow Grass Energy×4。
- **訓練家，37 張**：Buddy-Buddy Poffin×4、Crushing Hammer×4、Pokégear 3.0×4、Switch×4、Jumbo Ice Cream×4、Hero’s Cape×1、Boss’s Orders×2、Xerosic’s Machinations×4、Hilda×4、Lillie's Determination×4、Battle Cage×2。
- **開局與速度**：19/30 場由 Dwebble 起手，其餘是袋獸。Poffin／Hilda 協助鋪場。最快 T2 用 Ascension；主攻最快 T5，中位 T9.5。
- **攻擊與消耗**：Crustle 的 Superb Scissors 打 120。袋獸的 Rapid-Fire Combo 基礎 200，每次正面再加 50。Hammer 拆能、Xerosic 削手牌；Battle Cage 封備戰指示物。Ice Cream 回復，觀察到單次回 80。
- **怎麼輸**：18 敗含清場 9、取完獎賞 8、牌庫耗盡 1。非 ex Alakazam 能正面拆牆；`54ce1888` 的 Lucario 則擊倒兩隻袋獸，直接拿六獎。
- **對 Dragapult：1 勝 0 敗，全為 ross**。`52eaa69a` 我們先用 Drakloak 打傷 Crustle，再累積袋獸傷害。T15 Boss 收袋獸拿三獎，但 Battle Cage 留場，後續四次 Phantom Dive 正面皆為零，最後抽光。此批沒有 Dragapult 勝例。
- **規則候選：解除封鎖要有收益**。本回合能打 Phantom Dive，且後排有可受指示物目標，才為此用 Jamming Tower 蓋 Battle Cage。反例：只剩單隻 Crustle，或後排全部有 Mist；解除備戰封鎖仍無輸出。
- **規則候選：雙封時保留非 ex 路線**。Crustle＋Battle Cage、無有效 Boss 目標時，保留並補能 Drakloak。反例：已有可收獎目標，或 Phantom Dive 的備戰指示物仍有效，不應一律禁止進化。

### usecommitt：Mega Starmie（16 勝 17 敗）

- **寶可夢／能量，27 張**：Staryu×4、Mega Starmie ex×4、Budew×2、Cinderace×2；基本水×12、Ignition Energy×3。
- **訓練家，33 張**：Buddy-Buddy Poffin×4、Night Stretcher×2、Crushing Hammer×2、Ultra Ball×3、Pokégear 3.0×4、Mega Signal×3、Hero’s Cape×1、Boss’s Orders×3、Salvatore×3、Hilda×2、Lillie's Determination×3、Wally's Compassion×3。
- **開局與速度**：通常 Staryu 起手，搜尋、進化成海星；另有 Budew／Cinderace 起手。小招最快 T2；海星主攻最快及中位數均為 T3，30/33 場有打出主力招式。
- **攻擊與回復**：Jetting Blow 一水打前排 120、備戰 50；Nebula Beam 三無色打 210。Boss 收尾、Hammer 拆能。Wally's Compassion 有大幅回復，紀錄出現單次回 240；另有 Night Stretcher 回收。
- **怎麼輸**：17 敗含取完獎賞 11、清場 6。對手持續擊倒海星，三獎交換壓力大；部分敗局則卡在缺能或副攻路線，未形成連續海星攻勢。
- **對 Dragapult 系：2 勝 2 敗**。贏 reichelligahh 兩場；輸 ross、frost_otter_2807 各一場。排除以火系主攻、僅帶 Drakloak 的 nyxriver。`fe5e2569` ross 拆能，T6／T8 Boss 收 Staryu，再以猴移傷收 Budew、Phantom Dive 收海星。`95bc0b5f` 的海星長期無能，frost 到 T14 才首次 Dive 仍贏。
- **規則候選：小招也能斷進化**。缺超能、只能打 70 時，若 Boss 可收 Staryu 且不犧牲本回合必要補能，就拉。反例：Crispin 能立即湊出 Phantom Dive 並取得更多獎賞，不為一獎耗掉支援者額度。
- **規則候選：拆能看完整招式費用**。優先拆掉海星唯一水能，削弱 Jetting Blow。反例：仍能打 Nebula Beam、另一海星已就緒，或下一回合可補水；不能把一次 Hammer 當作必定停攻。
- **規則候選：先算三獎擊倒線**。可移傷量足以把海星壓到 200 以下，且本回合能攻擊／必要時 Boss，就先移傷再收三獎。反例：猴無惡能、沒有可移傷害，或 Boss 與必要 Crispin 衝突。

### levi：Marnie's Grimmsnarl ex（10 勝 20 敗）

- **寶可夢／能量，30 張**：Marnie's Impidimp×4、Marnie's Morgrem×3、Marnie's Grimmsnarl ex×3、Marnie's Morpeko×4、Fezandipiti ex×2；基本惡×14。
- **訓練家，30 張**：Rare Candy×4、Buddy-Buddy Poffin×4、Night Stretcher×2、Ultra Ball×4、Switch×2、Master Ball×1、Team Rocket's Great Ball×1、Poké Pad×2、Boss’s Orders×2、Crispin×4、Lillie's Determination×3、Jamming Tower×1。
- **開局與速度**：主要 Impidimp 起手，備戰鋪 Morpeko。Rare Candy 跳階、Crispin 補能。小招最快 T2；主攻最快 T3，中位 T5。
- **攻擊與干擾**：Shadow Bullet 兩惡打 180＋備戰 30；對 Munkidori 因弱點打 360。Morpeko 的 Spiky Wheel 為 `20＋40×惡能數`。Boss 揪目標、Jamming Tower 封道具；Night Stretcher 回收，未觀察到回血。
- **怎麼輸**：20 敗含取完獎賞 11、清場 8、超時 1。尚未完成進化就被拆掉小怪，或對手避開滿血 Grimmsnarl，改收 Fezandipiti／Morpeko。
- **對 Dragapult：1 勝 2 敗，均對 frost_otter_2807；沒有 ross 樣本**。`d4a85f84` 勝方 T4 收 Impidimp、T6 開 Dive，主要向鳥與 Morpeko 取獎。`6e113676` 則先用 Chi-Yu 拆進化線，最後清場；我們固定牌表沒有 Chi-Yu，不能照搬。敗方 `03b38c55` 到 T8 才 Dive，levi 已從 T3 開始 Shadow Bullet。
- **規則候選：可收進化線才集中指示物**。若現有傷害＋本回合可用猴移傷＋Dive 60 足以收 Impidimp／Morgrem，優先斷線。反例：滿血 70 HP Impidimp，只有 Dive 60 時不能算已解決威脅。
- **規則候選：避免送弱點盾**。對方已能用 Shadow Bullet 時，不把 Munkidori 當能扛 180 的替補，也不額外鋪第二隻 Budew 供備戰 30 收獎。反例：不鋪就會因場上無寶可夢而輸，或猴能立即移傷取勝。

### jade_yak_3292：Mega Lucario（12 勝 18 敗）

- **寶可夢／能量，34 張**：Riolu×4、Mega Lucario ex×4、Makuhita×2、Hariyama×2、Lunatone×3、Solrock×3；基本鬥×12、Rock Fighting Energy×4。
- **訓練家，26 張**：Buddy-Buddy Poffin×4、Fighting Gong×4、Mega Signal×4、Poké Pad×2、Hero’s Cape×1、Boss’s Orders×3、Xerosic’s Machinations×2、Hilda×2、Lillie's Determination×4。
- **開局與速度**：鋪 Riolu、月石／太陽岩，進化 Lucario。小招最快 T2；Lucario 主攻最快 T3，中位 T4。Aura Jab 回填棄牌鬥能，養備戰攻擊手。
- **攻擊與干擾**：Aura Jab 一鬥打 130；Mega Brave 兩鬥打 270，下回合同隻不能再用。Solrock 可打 70；Hariyama 打 210、自傷 70。Boss 抓獎、Xerosic 削手牌；未觀察到回血，會輪替 Lucario 分散傷害。
- **怎麼輸**：18 敗含取完獎賞 15、清場 2、牌庫耗盡 1。Alakazam 能壓低再收 Lucario；Crustle 對局則常改抓月石／太陽岩等配角，或拖到它抽光。
- **對 Dragapult：2 勝 0 敗，全為 ross；沒有其他 Dragapult 勝例**。`04c0ef37` 我們到 T11 才 Dive，先掉兩隻 Drakloak，鳥再被 Aura Jab 弱點 260 收走。`f80ea76a` 有一隻 140 HP Lucario 留在備戰，但我們打有披風的 440 HP 前排；最後又被 Boss 收走 80 HP Dragapult。
- **規則候選：可立即收三獎就優先 Boss**。備戰 Lucario 的剩餘 HP 不高於本回合實際傷害，且換上後仍能付攻擊費用，就優先收。反例：還需要 Crispin 才能打 Phantom Dive，先 Boss 會讓攻擊落空。
- **規則候選：保護二獎配角**。對方能用 Aura Jab 時，把 Fezandipiti 當作會被一擊拿兩獎的目標。沒有立即抽牌需求就不鋪。反例：必須靠其抽牌才能完成主攻或避免清場。
- **規則候選：分開處理兩種保護**。Phantom Dive 指示物避開有 Rock Fighting Energy 的目標；Jamming Tower 可處理 Hero’s Cape。反例：蓋塔不會解除特殊能量保護，不能因此把備戰指示物算進擊倒線。

### rimeblade：Crustle／Munkidori（13 勝 17 敗）

- **寶可夢／能量，24 張**：Dwebble×4、Crustle×4、Munkidori×2；基本草×1、基本惡×2、Mist Energy×4、Spiky Energy×3、Grow Grass Energy×4。
- **訓練家，36 張**：Buddy-Buddy Poffin×2、Ultra Ball×3、Pokégear 3.0×4、Switch×1、Jumbo Ice Cream×4、Hero’s Cape×1、Boss’s Orders×4、Morty’s Conviction×1、Colress’s Tenacity×2、Xerosic’s Machinations×1、Cook×1、Team Rocket's Petrel×3、Hilda×2、Lillie's Determination×4、Team Rocket's Watchtower×2、Team Rocket's Factory×1。
- **開局與速度**：通常 Dwebble 起手、Ascension 進化，另養 Crustle／惡能猴。最快 T2 Ascension；Superb Scissors 最快 T5，中位 T8.5。
- **攻擊與回復**：主攻固定 120。四張 Boss 反覆抓配角；Spiky 反傷，猴移傷，Ice Cream／Cook 回復。與 raps 不同，這副沒有 Battle Cage；備戰能否放指示物，要逐隻看 Mist。
- **怎麼輸**：17 敗含清場 15、取完獎賞 1、牌庫耗盡 1。非 ex Alakazam／Okidogi 能正面突破；`ee099235` 的海星用無視效果的 Nebula Beam 清掉 Crustle，這招我們沒有。
- **對 Dragapult：1 勝 1 敗**。贏 ross 的 `d6310aa9`：我們兩度 Boss 收猴，但留下 80 HP Dragapult 被打倒，再被 Boss 收猴拿最後一獎。輸 StartupBros 的 `179cb675` 是牌庫耗盡；勝方整場零獎，T49 用 Lillie 將牌庫由 3 補到 19，最後尚餘 13 張。
- **規則候選：先保主力，再 Boss**。前排會被 120 擊倒，且有能扛住、能攻擊的替補時，先撤退再拉目標。反例：本回合已能直接取勝，或替補同樣會倒；不能只因想收猴就留殘血主攻。
- **規則候選：允許淨增牌庫的 Lillie**。可安全拖延、無立即致勝時，若 `手牌數−1 > 抽牌數`，允許洗回；抽牌數為未取獎時 8，否則 6。這需例外放行現行低牌庫禁用條件。反例：小手牌使用後淨減牌庫，或本回合必須保留 Crispin／Boss 才能解危。
## 高手對照資料更新（2026-10-18）

`data/raw/matches/` 從 164 場更新到 464 場（排行榜前 15 名的近期對戰）。新的比較基準：
全部勝方 29,550 個決策點、一致率 52.4%（舊資料 52.9%）；四位 Dragapult 高手（StartupBros、godam、keris、clairenuttall）8,079 點、55.2%（舊資料 57.5%）。
之後的「高手跟舊／新規則各幾次」都用新資料算。目前前 15 名：clairenuttall、kenshintcg、grimm_grinder、solncestoyaniee、antge-poker-bot-01、snowdrift_ai、arena_oracle、StartupBros、ilovecats、sparring、BASILbyte93、tundra_shift、mikeoxlong、nineteenshot、cobrastrike。

## 對手研究（二）：Alakazam 與 Mega Lucario（2026-10-18）

本次全程唯讀，未修改檔案，也未執行對戰程式。最明確的策略缺口是 **Nighttime Mine 的額外攻擊費用**，以及 **Jamming Tower 封住 Hero’s Cape 後的擊倒線**。

### 資料範圍與計數方式

- `data/raw/scout/` 共 287 場，其中 160 場涉及本次六人。補入 `data/raw/matches/` 的 30 場、`data/runs/` 的 13 場，共 **203 場不重複相關對局**。
- 按 `battle.players` 認人，不只讀取檔案的 `scouted` 標籤。牌表以公開卡的 serial 去重，再按玩家位置正規化卡位。**六人皆補齊 60 張，沒有卡位衝突。**
- 以下勝敗均為該對手視角。T 是雙方累計回合；起動中位數只計算用過主攻的對局。攻擊時間採實際提交動作，避免 logs 顯示於下一回合造成偏移。
- Dragapult 樣本包含實際使用 Dragapult ex 的玩家，以及已知固定牌表的 ross。只帶 Drakloak 當引擎的其他牌組不納入。
- 全部本地實戰中，ross 對這四位 Alakazam 為 **6 勝 11 敗**；對這兩位 Lucario 為 **1 勝 3 敗**。這個範圍比題述的近期樣本大。

### 已確認牌表

以下共通牌表加上各人的差額，就是完整 60 張。Alakazam 指卡號 743；Abra／Kadabra 為 741／742，Shaymin 為 343。

**A54：四位 Alakazam 共通的 54 張**

| 類別 | 已確認卡片 |
|---|---|
| 寶可夢，18 張 | Abra×4、Kadabra×4、Alakazam×4、Dunsparce×3、Dudunsparce×2、Fezandipiti ex×1 |
| 訓練家，30 張 | Rare Candy×3、Enhanced Hammer×4、Buddy-Buddy Poffin×4、Night Stretcher×1、Sacred Ash×1、Poké Pad×4、Boss’s Orders×3、Lana’s Aid×1、Xerosic’s Machinations×3、Hilda×3、Dawn×3 |
| 能量，6 張 | 基本超×2、Telepath Psychic Energy×4 |

**L60：hailstorm_ex 與 catnapper 完全相同的 60 張**

| 類別 | 已確認卡片 |
|---|---|
| 寶可夢，14 張 | Riolu×4、Mega Lucario ex×4、Lunatone×3、Solrock×3 |
| 訓練家，31 張 | Buddy-Buddy Poffin×4、Hand Trimmer×2、Night Stretcher×1、Switch×1、Fighting Gong×4、Mega Signal×4、Poké Pad×2、Hero’s Cape×1、Boss’s Orders×3、Xerosic’s Machinations×2、Hilda×2、Lillie's Determination×4、Gravity Mountain×1 |
| 能量，15 張 | 基本鬥×11、Rock Fighting Energy×4 |

### cibinesia：Alakazam（17 勝 16 敗）

- **牌表**：A54＋Shaymin×1、Enriching Energy×1、Hilda×1、Dawn×1、Nighttime Mine×2。
- **開局與速度**：Abra／Dunsparce 起手，另有鳥、Shaymin 起手。搜尋與進化抽牌累積手牌；Powerful Hand 最快 T4，中位 T5。
- **攻擊與干擾**：一超放 `20×自己的手牌數` 個傷害點。Mine 增加太晶攻擊費用，Xerosic 削手；Stretcher／Sacred Ash／Lana 回收進化線。
- **怎麼輸**：16 敗含取獎 11、清場 4、抽光 1。`3b5574bb` 的 frost 從 T8 連打三次 Dive，正面收 Alakazam，後排收 Abra，再收 Dudunsparce／Dunsparce。
- **對 Dragapult：4 勝 4 敗**。對 ross 為 4 勝 3 敗，另輸 frost。ross 的 `e2f35b50` 先 Stamp，再於 T6／8／10 連打 Dive；另兩勝是早期清場。敗局 `5484d545` 則整場沒有 Dive。
- **具體規則**：Mine 在場、Pult 已有火超各一，第三能或蓋塔能開 Dive時，優先解費用。反例：Alakazam 本身不是太晶，不應替它加費。

### allinwolf2：Alakazam（19 勝 20 敗）

- **牌表**：A54＋Night Stretcher×1、Colress’s Tenacity×2、Neutralization Zone×1、Nighttime Mine×1、基本超×1。
- **開局與速度**：主要 Abra／Dunsparce 起手，Telepath 協助鋪超系基本。小招最快 T2；Powerful Hand 最快 T3，中位 T5。
- **攻擊與干擾**：依手牌數放指示物，搭配三張 Xerosic、三張 Boss。Zone 擋 ex 正面傷害；Mine 加費。回收牌讓進化線能重建。
- **怎麼輸**：20 敗含取獎 17、清場 2、抽光 1。`40c77989` 的 StartupBros 先用 Budew，T6／8／10 連打 Dive；收 Abra、蓋塔、Stamp，最後 Boss 收鳥。
- **對 Dragapult：3 勝 2 敗**。對 ross 為 3 勝 1 敗，另輸 StartupBros。ross 的 `0c9c9351` 到 T9 才 Dive；`553cceb5` 雖 T6 起攻，後續沒能連打。勝局 `246259b4` 是 T3 用 Drakloak 收唯一 Abra。
- **具體規則**：Zone 正在擋正面傷害，而且蓋塔後能有效攻擊，就先解除。反例：仍缺必要能量，且蓋塔後也無有效攻擊，不把蓋塔當成完成解場。

### gastonhoma：Alakazam（18 勝 28 敗）

- **牌表**：A54＋Shaymin×1、Enriching Energy×1、Hilda×1、Dawn×1、基本超×2；**沒有競技場**。
- **開局與速度**：較常 Dunsparce 起手，再鋪 Abra、走進化抽牌。Powerful Hand 最快 T3，中位 T6。
- **攻擊與干擾**：同樣靠大手牌輸出，Enhanced Hammer／Xerosic 干擾；Stretcher、Sacred Ash、Lana 回收。沒有 Mine／Zone 封鎖。
- **怎麼輸**：28 敗含取獎 13、清場 5、棄權 9、超時 1。棄權不能當戰術勝例。`16f19897` 的 keris 連續五次 Dive，配合 Judge，正面收進化型並拆後排。
- **對 Dragapult：3 勝 4 敗**。對 ross 為 3 勝 1 敗；另輸 keris、clurit、antge。ross 勝局 `f11974a7` 在 T5 一次 Dive 收前排 Kadabra、後排 Abra，直接清場。
- **具體規則**：Dive 可用、後排 Abra 剩餘 HP≤60 時，集中收掉進化起點。反例：滿血 Kadabra 為 80 HP，只有 60 指示物不能算已斷線。

### blazewolf：Alakazam（15 勝 21 敗）

- **牌表**：與 allinwolf2 相同，都是 A54＋Stretcher×1、Colress×2、Zone×1、Mine×1、基本超×1。
- **開局與速度**：Abra／Dunsparce 起手，搜尋後進化。小招最快 T2；Powerful Hand 最快 T3，中位 T5。
- **攻擊與消耗**：大手牌指示物、Boss／Xerosic，另有 Zone／Mine。回收牌支持持續重建。
- **怎麼輸**：21 敗含取獎 14、清場 4、抽光 3。`0d8ff5b6` 的 antge 用 Stamp、Judge 壓手，持續 Dive 收進化線。
- **對 Dragapult：1 勝 2 敗**。對 ross 為 1 勝 1 敗，另輸 antge。ross 兩場都 T5 首次 Dive，起攻時間不足以解釋勝負；勝局 `92bd007a` 後段用 Judge 把 23 張手牌壓到 4，再由非 ex 猴收最後一獎。
- **具體規則**：Zone 留場時，若非 ex 猴／Drak 能收目前目標，且換位後仍能攻擊，就切換。反例：非 ex 傷害仍不足，或換位路線無法完成，不為繞牆盲目撤退。

### hailstorm_ex：Mega Lucario（14 勝 16 敗）

- **牌表**：L60。與 jade_yak_3292 相比，沒有 Hariyama 線，加入 Hand Trimmer、Switch、Stretcher、Gravity Mountain。
- **開局與速度**：多由 Riolu 起手，鋪月石／太陽岩，搜尋 Mega 進化。小招最快 T2；Lucario 主攻最快 T3，中位 T4。
- **攻擊與干擾**：Aura Jab 一鬥 130，並回填最多三張棄牌基本鬥；Mega Brave 兩鬥 270，同隻下回合不能再用。Boss 抓獎、削手、輪替 Lucario；沒有專用回血卡。
- **怎麼輸**：16 敗含取獎 12、抽光 3、清場 1。敗局有被拆兩隻 Mega，也有對手改收月石／太陽岩；不能一律照抄正面互打。
- **對 Dragapult：2 勝 1 敗，全對 ross**。勝方 `a2a5ce50` 在 T7／9／11 連打 Dive，先處理月石，再集中傷害於可受指示物的殘血 Lucario；T13 猴以弱點 120 收最後 80 HP。敗局則曾早掉鳥或帶能 Drak。
- **具體規則**：後排 Lucario 的 Rock Fighting Energy 還在時，不分配 Dive 指示物；正面傷害仍可計算。反例：岩鬥已離場，就重新納入指示物目標。

### catnapper：Mega Lucario（14 勝 16 敗）

- **牌表**：L60，與 hailstorm_ex 的 60 張完全一致。
- **開局與速度**：Riolu、月石、太陽岩皆會起手，接搜尋與 Mega 進化。小招最快 T2；Lucario 主攻最快 T3，中位 T4。
- **攻擊與干擾**：Aura Jab 養第二隻，交替 Mega Brave／Aura Jab；三張 Boss、Hand Trimmer／Xerosic 干擾。靠輪替與 Stretcher 回收，沒有專用回血卡。
- **怎麼輸**：16 敗含取獎 14、抽光 1、清場 1。`0ad1d246` 的 Alakazam 主要拆月石／太陽岩；`4af30535` 的鏡像則擊倒兩隻 Mega 取六獎。
- **對 Dragapult：1 勝 0 敗，只有 ross**。`edebc9bd` 我們 T4 先掉帶火超的 Drak，直到 T15 才 Dive；當時對面披風 Lucario 剩 290 HP，手上有塔卻直接打 200。沒有其他 Dragapult 勝例。
- **具體規則**：封披風後，本回合可從打不倒變成擊倒，就先塔後攻。反例：滿血 440→340，仍超過 200，不能當成立即三獎。

### 所有玩家適用的共通對策

**兩派都適用**

- **有擊倒線才為斷進化投入 Boss。** Drakloak 的 70 可收 Abra／Riolu；Dive 後排 60 可收滿血 Abra，收不了滿血 70 HP Riolu。若必須先 Crispin 才能攻擊，就不能先耗掉支援者額度。
- **避免無收益地鋪二獎配角。** 主攻與引擎已齊、當下不需要特性時，保留鳥／Meowth。例外是不鋪會被清場，或必須靠其特性完成本回合攻擊。
- **維持連續攻擊。** 這批 Dragapult 勝例常見連續 Dive。只有首次起攻早還不夠；blazewolf 的兩場 ross 對局就是反例。

**四位 Alakazam 共通**

- Powerful Hand 是**每張自己的手牌放兩個指示物**。16 張就是 320，不套弱點／抗性。Judge／Stamp 同時削手與降火力。
- 判斷下一擊至少加上回合抽牌。Judge 壓到 4 後，對手開回合已有 5 張；進化抽牌還能繼續增加。不能把下一擊固定當成 80。
- 正面 Alakazam 140 HP 可被 Dive 收走；後排 Abra 50 HP 可順便斷線。Shaymin 防的是招式「傷害」，不擋 Dive 的指示物。
- **Mine／Zone 不是四人共通配置。** gastonhoma 沒有競技場；cibinesia 沒有 Zone。規則應辨識盤面效果。

**Lucario 共通，包含已研究的 jade_yak_3292**

- Mega Lucario 倒下送三獎，但滿血 340 超過一次 Dive。優先比較「收殘血 Mega」與「正面打滿血 Mega」的收益。
- **分開判斷岩鬥與披風。** 岩鬥擋對鬥系持有者的招式效果，不擋正面傷害；塔封的是道具，不能解除岩鬥。猴的移傷是特性，也不能混成 Dive 一起封掉。
- 鳥弱鬥，Aura Jab 可打 260。對方已有可攻擊 Lucario 時，不為沒有立即收益的抽牌能力增加二獎目標。
- Aura Jab 能養備戰攻擊手。拆掉前排一顆能量，不代表下一回合一定停攻；還要看手貼與候補。
- 新兩人的 Gravity Mountain 會讓 Pult 少 30 HP。這張不是 jade 牌表的共通項目。

### 現行 strategy.py 缺少的三項規則

現行已處理 Judge 防致命手牌傷害、Stamp 優先、Boss 收殘血三獎、岩鬥指示物免疫。以下三項才是本次確認的新缺口。

| 規則／函式 | 觸發條件與動作 | 不該觸發的反例 |
|---|---|---|
| **計算 Mine 加費**：新增 `effective_attack_cost()`；接入 `score_attach()`、能量需求與戰力判斷 | Mine 在場、我方為太晶 Pult，Phantom Dive 成本應為火＋超＋無色。已有火超各一、可手貼時，第三顆能量要視為必要補能。本次最小補丁評為 87，保留進化／特性優先 | 非太晶不加費；已有第三顆能量不再補。不能把所有二階寶可夢都套上加費 |
| **蓋 Mine 開啟 Dive**：`score_play_card()` | 塔合法、Mine 在場、前排 Pult 火超已齊，但合法招式沒有 Dive；且沒有本回合直接取勝的攻擊，就提高蓋塔優先度至 69 | 已能合法 Dive，或仍缺火／超時，不因 Mine 名稱就優先蓋塔 |
| **封披風形成擊倒線**：`score_play_card()` | 對面前排有生效披風，`0 < HP−100 ≤ 本回合合法傷害 < HP`，就優先塔；本次評為 94。封披風直接歸零也可納入 | 披風已被封、沒有合法攻擊、封後仍打不倒，均不算立即擊倒；已有直接致勝攻擊則先取勝 |

Mine 的原文是「太晶寶可夢招式多花一無色」，見 `data/raw/cards.json`。目前 `assets/catalog.json` 沒帶 `tera` 旗標，正式實作時須補資料，或先限定固定牌組的 Dragapult ex。

披風扣血也有引擎證據。`0c86d782` 在塔進場後，滿血 Mega Starmie 從 430／430 變為 330／330。這不是只按卡文推算。

### 記憶體重跑證據

讀取 `data/runs/*_obs.jsonl`，依 `(matchId, seq)` 去重。共 **21 場、1,586 個真實決策點**。比較現行 `act()` 與記憶體中的最小評分補丁；沒有改檔或啟動對戰。

| 規則 | 真實決策點 | 現行選擇 → 候選選擇 | 盤面意義 |
|---|---|---|---|
| Mine 第三能 | `5484d545`，T6／seq 50 | `[1]` 貼火給備戰 Drak → `[0]` 貼給前排 Pult | 前排已有火超，但 Mine 下還差一無色。補前排才能開 Dive，擊倒 80 HP Kadabra |
| 蓋 Mine | `469a89f5`，T16／seq 167 | `[1]` Jet Headbutt → `[0]` Jamming Tower | 前排火超齊；原本只有 70。蓋塔後可用 Dive 收 140 HP Alakazam |
| 封披風 | `edebc9bd`，T15／seq 135 | `[3]` Phantom Dive → `[0]` Jamming Tower | Lucario 為 290／440；封披風後 190／340，進入 200 擊倒線。岩鬥不擋這段正面傷害 |

原始紀錄位置：

- Mine 補能：`run_20261018_143215_obs.jsonl`，第 278 行。
- 蓋 Mine：`run_20261018_091809_obs.jsonl`，第 698 行。
- 封披風：`run_20261018_143215_obs.jsonl`，第 619 行。

三項合併後，**14 個快照改選，涉及三場、九個回合**。其中補能改七點、蓋 Mine 改五點、封披風改兩點。所有新選擇都在原始合法動作內；反例條件也已做斷言檢查。

這是同一快照重新選動作，**不是改選後重演整場**。同回合的多個快照也不是獨立收益，不能宣稱三場會翻勝。

### 四位高手對照

使用 `tests/agreement.py --handles StartupBros,godam,keris,clairenuttall` 的資料與相同篩選方式：

| 版本 | 決策點 | 與高手一致 | 一致率 |
|---|---:|---:|---:|
| 現行策略 | 8,079 | 4,457 | 55.17% |
| 三項記憶體補丁合併 | 8,079 | 4,457 | 55.17% |

本次高手資料**沒有產生改選點**。公開手牌遮蔽，也限制了塔的牌名分支判斷。因此這項對照只能說基準沒有變動，不能證明候選更好。採用依據是卡文、引擎實例與上述實戰選擇差異；勝率效果仍待後續對局驗證。