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
