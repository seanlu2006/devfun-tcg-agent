# 真實比賽 Dragapult ex 打法研究（給 dev.fun Arena agent 用）

研究日期：2026-10-18｜賽制：Standard（2026 Worlds 後、30th Celebration 合法後的環境）
可信度標記：**[數據]** = Limitless 實際戰績；**[卡面]** = 由卡片文字推得；**[指南]** = 玩家文章明寫；**[推論]** = 我根據卡面與數據推的，沒有文章直接寫。

---

## 一、來源清單（只列實際讀到內容的）

| # | 標題 | 網址 | 日期 | 備註 |
|---|---|---|---|---|
| S1 | Andrew Hedrick Worlds 冠軍牌表（Limitless Labs） | https://labs.limitlesstcg.com/0071/player/0103/decklist | 2026-08-30 | 14-2，完整 60 張 |
| S2 | Worlds 2026 前 16 名（Limitless Labs） | https://labs.limitlesstcg.com/0071/standings | 2026-08-30 | Top 8 有 3 Dragapult、2 Crustle、2 Alakazam、1 Basic Box |
| S3 | Rune Heiremans Crustle 牌表（Worlds 第 5） | https://labs.limitlesstcg.com/0071/player/0641/decklist | 2026-08-30 | 對手 Crustle 真實構築 |
| S4 | Dragapult 對戰勝率：Worlds | https://labs.limitlesstcg.com/0071/decks/dragapult-ex/matchups | 2026-08 | 見第四節 |
| S5 | Dragapult 對戰勝率：Frankfurt Regional | https://labs.limitlesstcg.com/0074/decks/dragapult-ex/matchups | 2026-09-26~27 | |
| S6 | Dragapult 對戰勝率：Louisville Regional | https://labs.limitlesstcg.com/0076/decks/dragapult-ex/matchups | 2026-10-09~11 | |
| S7 | Limitless Dragapult 牌型頁 | https://limitlesstcg.com/decks/284 | 讀取於 2026-10-18 | 最近結果 |
| S8 | Limitless Dragapult 平均卡片張數（476 份牌表） | https://limitlesstcg.com/decks/284/cards | TEF–30C 環境 | 第五節差異比對的主依據 |
| S9 | Demi Eaton Dragapult 牌表（Frankfurt） | https://limitlesstcg.com/decks/list/29678 | 2026-09 | |
| S10 | Ian Robb, "Some Quick Thoughts on Dragapult ex" | https://ianrobb.substack.com/p/some-quick-thoughts-on-dragapult | 2026-09-11 | 知名玩家，談換獎與干擾時機 |
| S11 | litian80/ptcg-analysis `dragapult-ex.md`（社群對局手冊，依 Limitless/RK9 戰績產生） | https://raw.githubusercontent.com/litian80/ptcg-analysis/main/data/matchups/dragapult-ex.md | 2026（日期未標） | **非官方**，但每個對局附場數與勝率 |
| S12 | 同 repo PR #21：NAIC 2026 青少年組決賽 Dragapult 2-0 Alakazam | https://github.com/litian80/ptcg-analysis/pull/21 | 2026 | 社群分析 |
| S13 | Ultimate Guard, "Pokémon Worlds 2026: All hail the dragon king!" | https://ultimateguard.com/fr/blog/pokemon-worlds-2026-all-hail-the-dragon-king | 2026-09-02 | 決賽 vs Alakazam 以牌庫抽光獲勝 |
| S14 | Samurai Sword Tokyo, Worlds 2026 results | https://samuraiswordtokyo.com/blogs/news/pokemon-worlds-2026-results-winning-decks | 2026-09-01 | Worlds 佔比 Dragapult 系約 42% |
| S15 | Gamertag Mythras, Dragapult ex deck guide | https://gamertagmythras.com/blog/pokemon-tcg/pokemon-tcg-dragapult-ex-deck-guide | 2026-09-21 | 內容淺，只取牌表與變體比較 |
| S16 | Thornberry Media, Dragapult ex Deck List (2026) | https://www.thornberrymedia.com/post/dragapult-ex-deck-list | 2026-09-02 | 指示物「要有目的地放」 |
| S17 | Monster Card Corner, Dragapult ex Deck Guide 2026 | https://monstercardcorner.co.uk/pages/competitive-dragapult-ex | 2026-10 | 核心卡 90%+ 清單 |
| S18 | Wargamer, Dragapult NAIC 2026 | https://www.wargamer.com/pokemon-trading-card-game/dragapult-ex-NAIC-2026 | 2026-06-06 | 只有背景 |
| S19 | Going Second, "Dragapult: Spreading with Phantom Dive" | https://goingsecond.substack.com/p/dragapult-phantom-diving-to-victory | 2025-04-24 | **舊環境**，只取「錯誤」類通則 |
| S20 | Ultimate Guard, Budew Itchy Pollen | https://ultimateguard.com/en/blog/budew-itchy-pollen-impact-meta-pokemon | 2025-02-11 | **舊環境** |
| S21 | Metafy, Hammers Dragapult Guide（TodTebyn3） | https://metafy.gg/guides/view/hammers-dragapult-guide-SlRhkSfzuTN | 2026-05-20 | **付費牆，只看到目錄**，內容未取得 |

卡面文字（多為搜尋結果中的 Bulbapedia／Scrydex 摘要，未逐頁打開）：Dragapult ex（Tera：在備戰區時不受攻擊傷害；Phantom Dive [火][超] 200＋6 指示物到對手備戰區；Jet Headbutt [無] 70）、Munkidori（超屬性 110HP、弱點惡；Adrena-Brain 需貼惡能，從我方移最多 3 指示物到對手任一隻；Mind Bend [超][無] 60＋混亂）、Meowth ex（從手牌放上備戰區時搜一張支援者；Tuck Tail 60 並回手）、Fezandipiti ex（上回合我方被擊倒才可抽 3；Cruel Arrow [無無無] 100 打任意一隻）、Budew（30HP 草、撤退 0；Itchy Pollen 10，對手下回合不能用物品）、Crustle（Mysterious Rock Inn：不受對手 ex 攻擊傷害；Superb Scissors [草][無][無] 120）、Mist Energy（擋對手攻擊的「效果」，攻擊放的指示物屬於效果——Temporal Forces 官方 FAQ）、Battle Cage（雙方備戰區不能被對手的攻擊或特性放指示物；Munkidori 移到備戰區會直接消失）、Jamming Tower（雙方道具無效）、Lillie's Determination（洗回手牌抽 6，剩 6 張獎賞卡時抽 8）、Mega Lucario ex（340HP、弱超、Mega Brave 270 不能連用）、Mega Starmie ex（330HP；Jetting Blow 120＋備戰區 50；Nebula Beam 210）、Alakazam（140HP；Powerful Hand [超]：依自己手牌張數每張放 2 指示物到對手**戰鬥寶可夢**）。

**讀不到／失敗的**：pokemon.com 2026 Power Rankings（404）、TCGplayer 月度最強牌組（內容空白）、PokeBeach 文章（403）、pokemoncard.io Ultimate Guide（403）、tcgcontender 勝率頁（403）、Deltia's Gaming（403）、Metafy 各付費指南內文。YouTube 影片只看到標題。note.com pokemimi 文章（2026-05-23）讀了但內容錯誤多（混入別的卡與錯誤攻擊敘述），**未採用**。

**查不到**：真實比賽中明確列出的「Dragapult 常見錯誤清單」沒有找到專文；第七節是從各來源零散說法彙整。Mega Starmie ex 對 Dragapult 沒有任何對局文章，只有很小樣本的勝率。

---

## 二、可直接寫成規則（依重要性排序，共 15 條）

### R1. 對 Crustle：Crushing Hammer 優先打 Crustle 身上的能量，把它卡在 3 能量以下
- **規則**：對手場上有 Crustle／Dwebble 時，Crushing Hammer 的目標排序 = 能量數最接近（或剛好）3 的 Crustle > 其他 Crustle > 其他。拿到正面就讓它下回合無法使用 Superb Scissors。
- **觸發**：對手是 Crustle 牌型（偵測到 Dwebble／Crustle／Mist Energy）。
- **反例**：對手 Crustle 已經 4 能量以上且我方只有 1 張 Hammer → 打掉一張也還能攻擊，Hammer 改留到能讓它跌破 3 的時候。
- **來源**：S11（「Crushing Hammer ×4 是最好的答案，因為 Crustle 要 3 能量才能攻擊」；Hero's Cape、Jumbo Ice Cream 會拖延這個計畫）；卡面 Superb Scissors 草＋無＋無。
- **關係**：**新增**（現有只寫「Hammer 攻擊前用」與「對 Crustle 用非 ex 攻擊」，沒寫目標選擇）。
- **補充數據**：這是真實比賽中 Dragapult **最差的對局**：Worlds 18%（35 場）、Frankfurt 26%（130 場）、Louisville 37%（116 場）[數據 S4–S6]；Worlds Top 8 有 2 副 Crustle [S2]。

### R2. Phantom Dive 的 6 個指示物**不要放在貼 Mist Energy 的寶可夢上**；改用 Munkidori 特性移過去
- **規則**：分配 Phantom Dive 指示物時，排除所有貼有 Mist Energy 的對手備戰寶可夢（會被擋掉＝浪費）。若要在那隻身上累積傷害，用 Munkidori 的 Adrena-Brain（特性不是攻擊效果，Mist 擋不到）。
- **觸發**：對手任一隻備戰寶可夢貼 Mist Energy（Crustle 牌型標配 4 張，Alakazam 也常用）。
- **反例**：Battle Cage 在場時 Munkidori 也不能移到備戰區（見 R3）。
- **來源**：卡面（Mist Energy ＋ Temporal Forces FAQ：攻擊放的指示物屬於「效果」）；S3（Crustle 冠軍級牌表 4 Mist Energy）；S11 對 Crustle 建議「用 Munkidori 與 Phantom Dive 的備戰區指示物」。
- **關係**：**新增**。如果 agent 引擎沒實作 Mist Energy 的阻擋，這條會讓 agent 白丟 6 個指示物。

### R3. 對手有 Battle Cage 時，先打出 Jamming Tower 把它換掉，再 Phantom Dive／Munkidori 移傷
- **規則**：本回合要 Phantom Dive 或用 Munkidori 移到對手備戰區之前，若場上是對手的 Battle Cage，先從手上放 Jamming Tower（場地互換）。手上沒有就考慮用 Ultra Ball／抽牌去找；真的沒有時，Munkidori 只移到對手**戰鬥寶可夢**（Battle Cage 只保護備戰區），Phantom Dive 本體 200 仍有效。
- **觸發**：場地卡＝Battle Cage（Alakazam 常帶 4 張，S13 提到 Worlds 亞軍 Diego 的 Alakazam 帶 4 Battle Cage + 2 Genesect 專門剋 Dragapult）。
- **反例**：本回合不 Phantom Dive 也不移傷 → 先留著 Jamming Tower，不要白換（對手會再蓋回來）。
- **來源**：S11（vs Alakazam：「用 Risky Ruins 與 Boss 控制 Battle Cage 的場地戰」）、S13、卡面。真實牌表用 **Risky Ruins** 搶場地，我們牌表沒有，**Jamming Tower 是我們唯一能蓋掉 Battle Cage 的牌**。
- **關係**：**新增**。

### R4. Jamming Tower 的第二用途：讓對手的道具失效
- **規則**：對手的關鍵寶可夢掛著道具時（Crustle 的 Hero's Cape、Alakazam 的 Lucky Helmet、Genesect 掛道具阻擋 ACE SPEC → 也就是阻擋我們的 Unfair Stamp），放 Jamming Tower。
- **觸發**：對手場上有道具，且該道具正在擋我們的擊倒線或擋 Unfair Stamp。
- **反例**：我方也沒有道具（我們牌表本來就沒有道具），所以 Jamming Tower 對我們沒有副作用；唯一的成本是場地卡會被對手換掉。
- **來源**：S12（Genesect 掛道具擋 Stamp、Lucky Helmet 讓 Alakazam 更強，真實玩家用 Tool Scrapper 處理）；S3（Crustle 帶 Hero's Cape）；Jamming Tower 卡面。
- **關係**：**新增**。

### R5. Boss／指示物優先處理對手的「引擎與倍率卡」，不只看獎賞卡數
- **規則**：Boss 與 Phantom Dive 指示物的目標優先序加一層「威脅值」：
  1. Lillie's Clefairy ex（讓我方龍系受超屬性傷害加倍）→ 出現就 Boss 掉；
  2. 對手的傷害加成／移傷引擎：Pecharunt ex、對手的 Munkidori、Froslass；
  3. 還在進化線底部、下回合會進化成主攻的基礎寶可夢（Dreepy、Duskull、Abra、Torchic、Chikorita／Bayleef、Dwebble）。
- **觸發**：上述寶可夢在對手場上。
- **反例**：本回合能直接拿到最後的獎賞卡 → 永遠優先「打得倒就打、直接贏」。
- **來源**：S11（vs Basic Box：「Clefairy ex 一出現就 Boss」；vs Zoroark：「先清掉 Pecharunt ex 與對手 Munkidori，只清一隻沒用」；vs Dusknoir：先狙 Duskull；vs Blaziken：先狙 Torchic；vs Ogerpon Meganium：先狙 Chikorita／Bayleef）。
- **關係**：**部分衝突**。現有「Boss 拉打得倒且獎賞卡更多的」只看獎賞卡；真實打法會優先拆引擎，即使只拿 1 張獎賞卡。

### R6. 指示物要算「剛好達到擊倒門檻」，而不是一律集中在已受傷的
- **規則**：分配 6 個指示物時依序檢查：
  1. 能不能直接打倒一隻（≤60 剩餘 HP）；
  2. 加上本回合／下回合 Munkidori（每隻 3 個、2 隻共 6 個）能不能打倒；
  3. 能不能讓某隻「下回合被 Boss 拉上來＋200」剛好打倒。
  具體門檻：Teal Mask Ogerpon ex 210HP → 只要先放 1 個以上指示物，下次 Phantom Dive 200 就打倒；N's Zoroark ex 280HP → 先放 60，下回合 200＋Munkidori 30＝290；對手 Dragapult ex 320HP → 先放 60，Boss 上來 200＋兩隻 Munkidori 60＝320；Drakloak（90HP）＝6＋Munkidori 3。
- **觸發**：每次 Phantom Dive 結算。
- **反例**：沒有任何組合能形成擊倒或擊倒預備 → 才退回「集中放在已受傷的」或打斷進化線。
- **來源**：S11（Zoroark 290、鏡像 320 的算法）；S16（「不要只因為可以就放指示物」，要想 Munkidori／Boss 下回合能否收掉）；S19（「規劃獎賞卡，而不是只打大」）。Ogerpon 210、Drakloak 90、Dreepy 70 HP 為 [卡面]，請在引擎裡確認。
- **關係**：**補充／部分衝突**。現有「集中放已受傷的」在多數情況是對的，但真實打法以「門檻」為準，不是以「受傷與否」為準。

### R7. 對手下回合能打倒我們的 Dragapult 時，把干擾牌（Hammer／Stamp／Boss）用在「讓它下回合打不出來」
- **規則**：如果對手的主攻手下回合能打倒我們場上的 Dragapult ex（例如對手已拿到 2 張獎賞卡、手上資源充足），本回合優先：Crushing Hammer 打那隻攻擊手上的能量（剛好讓它少於招式需求）、符合條件時 Unfair Stamp 縮手牌、或 Boss 把沒能量的寶可夢拉上來卡住它。
- **觸發**：對手是快攻型（N's Zoroark、Alakazam、Raging Bolt 類）且已拿到約 2 張獎賞卡（剩 4 張），或估算對手下回合傷害 ≥ 我方戰鬥 Dragapult 剩餘 HP。
- **反例**：本回合能直接擊倒對手唯一的攻擊手 → 直接打，不必花干擾牌。
- **來源**：S10（對 Raging Bolt、N's Zoroark：用 Crushing Hammer 與 Unfair Stamp 讓他們下回合不能攻擊；這些牌型會很快打到剩 4 張獎賞卡，Dragapult 必須活下來）；S11（vs Excadrill：Hammer 把能量壓在 5 以下）。
- **關係**：**補充**現有「Hammer 攻擊前用」：現有只講時機（攻擊前），這條補上「目標與條件」。

### R8. 鏡像戰的干擾牌節奏
- **規則**：
  - Crushing Hammer 是落後時的翻盤工具：領先時可以省，落後時優先用。
  - Boss 可以用來拉對手**還沒貼能量**的寶可夢上來，逼對手浪費一次貼能。
  - Unfair Stamp 留到對手只剩 1～2 張獎賞卡時。
  - **不要在前期打 Judge**（數據顯示減 14.6 個百分點）。
  - 先確保自己的物品能打出去（對手 Budew 會鎖物品），再考慮鎖對手。
- **觸發**：對手也是 Dragapult（含 Dusknoir／Blaziken 變體）。
- **反例**：對手手牌已經很少（≤3）時 Judge 只會幫他補牌（見 R11）。
- **來源**：S10（鏡像：Hammer 是唯一真正的翻盤牌；Boss 可逼對手浪費貼能；比賽常由「一方領先並保持」或「Hammer 讓對方斷能」決定）；S11（鏡像：Budew 決定前期、Stamp 留到對手剩 1–2 張、不要早打 Judge）。
- **關係**：**補充**現有 Stamp／Judge 時機，加入鏡像專屬限制。

### R9. Budew 的價值依先後攻而不同
- **規則**：**後攻**第一回合 Budew 在前場用 Itchy Pollen 價值最高；**先攻**時第一回合不能攻擊，Budew 只是 30HP、送 1 張獎賞卡的靶子（Kadabra 等都能輕鬆打倒），應視為「擋刀保護 Dreepy」而非「鎖物品」。
- **觸發**：開局選戰鬥寶可夢。
- **反例**：先攻但手上只有 Dreepy 和 Budew 可放前場 → 仍放 Budew，保護 Dreepy 比較重要。
- **來源**：S11（「後攻第一回合通常更適合使用」）；S13（雙 Budew 拖慢比賽，好讓自己鋪出 3～4 隻 Drakloak）；S20（Budew 30HP 很容易被打倒，舊環境）。
- **關係**：**部分衝突**。現有「開局 Budew 當戰鬥寶可夢」沒區分先後攻；建議加上「先攻時 Budew 前場的理由是保護 Dreepy，不是鎖物品」，並在後攻時更積極連續 Itchy Pollen。

### R10. 目標在場上維持 3～4 隻 Drakloak；永遠不要只剩 1 隻
- **規則**：前兩回合的鋪場目標是 ≥2 隻 Drakloak，中期 3～4 隻；只剩 1 隻 Drakloak 時，優先再補 Dreepy／進化，而不是全力進攻。
- **觸發**：任何回合結束前檢查 Drakloak 數。
- **反例**：本回合可以直接拿下最後獎賞卡。
- **來源**：S13（Budew 拖節奏是為了鋪 3～4 隻 Drakloak）；S11（vs Alakazam Dusknoir：「不要讓備戰區只剩 1 隻 Drakloak」）；S19（單一 Drakloak 被打掉會讓展開卡死）。
- **關係**：**已有＋強化**（現有「保留最後一隻 Drakloak」；建議把目標數量提到 ≥2～3）。

### R11. 洗手牌類支援者（Judge）的禁忌：對手手牌少時不要打
- **規則**：Judge 會讓雙方洗回再抽 4。對手手牌 ≤3 時打 Judge 等於送牌給對手；只在對手手牌 ≥5、或對手需要特定手牌（例如 Alakazam 靠手牌張數打傷害）時使用。
- **觸發**：準備打 Judge。
- **反例**：我方手牌完全卡死、需要換手 → 可以打，但優先考慮 Lillie's Determination。
- **來源**：S19（作者自己的失誤：本來該打 Arven 找 Counter Catcher，卻在對手手牌 4 張時打 Iono，只是把對手手牌換成另外 3 張新牌，自己沒有得到想要的牌，結果輸掉這場；舊環境但原則通用）；S11（鏡像前期不打 Judge）。
- **關係**：**補充**現有 Judge 時機。

### R12. 對 Alakazam：盯手牌張數，算 Powerful Hand 傷害
- **規則**：Powerful Hand 是「對手手牌張數 × 2 個指示物」放在我們**戰鬥寶可夢**上（不是傷害、不吃弱點抗性）。每回合估算：對手手牌數 × 20 ≥ 我方戰鬥寶可夢剩餘 HP → 預期被打倒。對策：(a) 對手剛靠 Psychic Draw／Kadabra 抽到大手牌時打 Unfair Stamp（符合條件時）或 Judge 壓到 2～4 張；(b) 不要讓已受傷的 Dragapult 留在前場；(c) Alakazam 只有 140HP，Phantom Dive 200 一定打倒，優先 Boss 已進化的 Alakazam；(d) 用指示物狙備戰區的 Abra／Kadabra（先處理 Battle Cage，見 R3）。
- **觸發**：對手是 Alakazam（Abra／Kadabra／Alakazam 出現）。
- **反例**：對手手牌已經很小（≤4）→ 不要洗它的手牌，會讓它重抽。
- **來源**：S11（「留意對手手牌數，Powerful Hand 依手牌張數成長」；Dusknoir 130＋Powerful Hand 可達 330）；S12；卡面。數據：Dragapult 對 Alakazam Dudunsparce 54%／63%／62%（Worlds／Frankfurt／Louisville），對 Alakazam Dusknoir 43%～64% [S4–S6]。
- **關係**：**新增**。

### R13. 對手牌庫很少時，改打「抽光牌庫」：用 Hammer／Stamp 拖
- **規則**：對手牌庫 ≤ 約 8～10 張且對手大量靠特性抽牌（Alakazam、Dudunsparce 類）時，把干擾（Hammer、Boss 拉沒能量的寶可夢、Stamp）用在讓對手無法在牌庫抽光前拿完獎賞卡，而不是硬拚擊倒。
- **觸發**：對手牌庫張數低，且我方不能在 2 回合內拿完獎賞卡。
- **反例**：我方牌庫比對手更少（Crustle 對局常見）→ 這條反過來，換我們省牌庫。
- **來源**：S13、S15（2026 Worlds 決賽 Hedrick 對 Alakazam 以抽光對手牌庫獲勝）；S11（「Hammer 或 Unfair Stamp 可以鎖住牌庫少的對手」）。
- **關係**：**新增**（現有只有「對 Crustle 省牌庫」的防守面，沒有進攻面的抽光勝利條件）。

### R14. 對 Mega ex（Lucario／Starmie）的換獎：Dragapult 能吃一下，用兩次攻擊拿 3 張
- **規則**：Mega ex 被打倒給 3 張獎賞卡。Mega Lucario ex 的 Mega Brave 270、Mega Starmie ex 的 Nebula Beam 210 都打不穿 Dragapult ex 的 320HP，所以讓 Dragapult 站前場正面交換：第一下 Phantom Dive 200，下回合補刀（Phantom Dive 或 Munkidori 移傷）拿 3 張。Mega 在備戰區時，提前用 Phantom Dive 的指示物＋Munkidori 把它壓到 200 以內，再 Boss 一擊拿 3 張。Mega Brave 不能連用，被打的下一回合是安全窗口。注意：Mega Starmie 的 Jetting Blow 備戰區 50 打不到備戰區的 Dragapult ex（Tera），但打得到 Dreepy／Drakloak。
- **觸發**：對手出現 Mega Lucario ex 或 Mega Starmie ex。
- **反例**：對手有額外傷害加成（例如 Lucario 的 Fighting Coach 類加成）時要重算能不能一擊打倒我們。
- **來源**：[卡面]＋[數據]：Dragapult 對 Mega Lucario 70%（9 場）／54%／58%；對 Mega Starmie 100%（4 場）／45%（14 場）[S4–S6]。**沒有找到任何文字對局攻略**（Metafy 有「Vs Mega Lucario ex」章節但付費 S21）。
- **關係**：**新增**（屬於推論，樣本小）。

### R15. Meowth ex／Fezandipiti ex 只在「當回合就要用到」時才放上備戰區
- **規則**：兩張都是 2 獎的 ex、都是 Poké Pad 和 Buddy-Buddy Poffin 找不到的牌。Meowth ex 用在「本回合需要特定支援者（例如致勝的 Boss）」；Fezandipiti ex 用在「上回合我方被打倒、需要抽 3」。沒有立刻的回報就留在手上，避免送對手一個 Boss 目標或 Phantom Dive 目標。
- **觸發**：手上有 Meowth ex／Fezandipiti ex。
- **反例**：對手是 Crustle（不打 ex 不影響，但對手 Boss 拉它上來卡位）→ 也照這條。
- **來源**：S11（Fezandipiti ex、Meowth ex 都給 2 張獎賞卡）；S15（這兩張大小與規則框讓 Poké Pad／Poffin 拿不到）；S16（Fez 用於被擊倒後補資源、Meowth 找支援者）；S10（環境中 Fezandipiti 是對抗干擾的牌）。
- **關係**：**新增**。

---

## 三、各對手流派打法摘要

**Crustle（最差對局，真實 18～37%）**
- 真實構築（S3，Worlds 第 5）：3 Dwebble／3 Crustle、4 Mega Kangaskhan ex、4 Jumbo Ice Cream、4 Mist／4 Spiky／4 Growing Grass Energy、Hero's Cape、Xerosic、Enhanced Hammer、Special Red Card。
- 計畫：Hammer 把 Crustle 壓在 3 能量以下（R1）；非 ex（Drakloak／Munkidori）打 Crustle；Phantom Dive 打得到 Crustle 以外的目標（Kangaskhan ex、Dwebble），指示物避開 Mist Energy（R2）；Jamming Tower 讓 Hero's Cape 失效（R4）。
- 推論：Dwebble 還沒進化時是唯一不受保護的 Crustle 進化線，值得用指示物／Boss 先處理（沒有文章直接寫，屬於推論）。
- 真實玩家的解法是 Dudunsparce ex 等非 ex 攻擊手（S11 +16.6 個百分點）；我們牌表沒有，所以只能靠 Hammer＋Munkidori＋省牌庫。

**Mega Lucario ex（真實 54～70%，偏有利）**
- 340HP、3 獎；Mega Brave 270 不能連用、Aura Jab 會從棄牌區把能量貼回備戰區 → Hammer 效果較差（能量會回收）。
- Dragapult 320HP 吃得住一下 Mega Brave；兩次攻擊換 3 獎（R14）。用指示物先處理備戰區的 Riolu。
- 文字攻略查不到，以上依卡面推論。

**Mega Starmie ex（樣本太小：4 場 100%、14 場 45%）**
- 330HP、3 獎；Jetting Blow 會打備戰區 50 → 威脅 Dreepy（70）與 Drakloak（90），所以要多鋪 Drakloak（R10）；備戰區的 Dragapult ex 不受影響（Tera）。
- Nebula Beam 210 打不倒滿血 Dragapult。查不到任何對局文章。

**Alakazam（Powerful Hand，真實 43～64%，Dudunsparce 版偏有利）**
- 盯手牌張數、在對手抽到大手牌後用 Stamp／Judge 縮手牌（R12）；Battle Cage 用 Jamming Tower 換掉（R3）；Alakazam 140HP 一擊必倒。
- 狙 Abra／Kadabra 打斷進化；Dusknoir 版要算 130＋Powerful Hand 可能到 330。
- 對手會大量抽牌 → 抽光牌庫是真實存在的勝利條件（Worlds 決賽，R13）。

**Marnie's Grimmsnarl ex（Froslass 版，真實 54～69%，偏有利）**
- 卡面推論：Froslass 每回合在所有「有特性」的寶可夢上放指示物 → 我們的 Drakloak、Munkidori、Meowth、Fez 都會慢慢掉血，對手再用 Munkidori 移傷。
- 優先用 Phantom Dive 指示物／Boss 清 Froslass 與對手的 Munkidori（R5）；不需要的特性寶可夢不要上場。
- 2026 年的文字攻略查不到（看到的都是 2025 舊環境的）。

**N's Zoroark ex（真實 34～41%，不利）**
- Zoroark ex 280HP：先放 60，下回合 200＋Munkidori 30 打倒（R6）。
- 先清 Pecharunt ex 與對手 Munkidori，而且兩隻都要清（R5）。
- 對手很快打到剩 4 張獎賞卡；這時用 Hammer＋Stamp 讓它下回合打不出來，保住 Dragapult（R7）。S11：Team Rocket's Watchtower 在這個對局反而減分（我們沒帶，不影響）。

**Dragapult 鏡像（約 50%）**
- Budew 決定前期；先保護自己的物品使用（R8、R9）。
- 預先放指示物在對手 Dragapult ex 上 → Boss＋200＋兩隻 Munkidori＝320（R6）。
- Hammer 是落後時的翻盤牌；Stamp 留到對手剩 1～2 張；不早打 Judge（R8）。對 Dusknoir 版先狙 Duskull；對 Blaziken 版先狙 Torchic（R5）。

**Teal Mask Ogerpon ex（Basic Box 44～46% 不利；Ogerpon Meganium Hydrapple 49～64% 有利）**
- Ogerpon ex 210HP：備戰區的 Ogerpon 只要先有 1 個指示物，下次 Phantom Dive 就能打倒 → 每次 Phantom Dive 都在每隻 Ogerpon 上至少放 1～2 個（R6）。
- Lillie's Clefairy ex 一出現就 Boss（龍系受超屬性傷害加倍）（R5）。
- Meganium 版：先狙 Chikorita／Bayleef；Hydrapple ex 在 Meganium 在場時可對 Dragapult 打出 390（S11）。

---

## 四、真實勝率數據（Dragapult ex 對各牌型）

Limitless Labs「matchups」頁（S4–S6）。判讀依據：鏡像那一列勝負場數完全相同、且每列勝＋負＋和＝場數，所以這是 Dragapult 對該牌型的對戰紀錄；勝率中和局算 1/3 勝。

| 對手 | Worlds 2026 | Frankfurt 2026-09 | Louisville 2026-10 |
|---|---|---|---|
| Crustle | 18%（35） | 26%（130） | 37%（116） |
| N's Zoroark | 37%（94） | 41%（227） | 41%（254） |
| Basic Box（Ogerpon/Clefairy） | 46%（130） | 44%（239） | 45%（357） |
| Alakazam Dudunsparce | 54%（110） | 63%（196） | 62%（240） |
| Alakazam Dusknoir | — | 43%（43） | 64%（112） |
| Grimmsnarl Froslass | 69%（12） | 56%（52） | 54%（26） |
| Mega Lucario | 70%（9） | 54%（47） | 58%（41） |
| Mega Starmie | — | 100%（4） | 45%（14） |
| Ogerpon Meganium Hydrapple | 49%（21） | 59%（134） | 64%（167） |

---

## 五、真實牌表 vs 我們的牌表

主要比對基準：S8（476 份 Dragapult 牌表的平均張數）與 S1（Hedrick 冠軍牌表）。

| 卡 | 我們 | 真實平均（S8） | Hedrick（S1） | 說明 |
|---|---|---|---|---|
| Dreepy／Drakloak／Dragapult ex | 4/4/3 | 4/4/2.95 | 4/4/3 | 相同 |
| Munkidori／Budew／Meowth ex／Fez ex | 2/2/1/1 | 1.98/1.91/1.01/1.00 | 2/2/1/1 | 相同 |
| Dunsparce＋Dudunsparce | 0 | 約 1/1（多種版本合計） | 1/1 | **我們沒有**：真實用來多抽牌，並把 Risky Ruins 放到自己身上的指示物回收 |
| Ultra Ball | 4 | 3.12 | 3 | 我們多 1 |
| Crushing Hammer | 4 | 3.85 | 4 | 相同 |
| Lillie's／Poffin／Poké Pad | 4/4/4 | 4/4/4 | 4/4/4 | 相同 |
| Boss's Orders | 3 | 2.99 | 3 | 相同 |
| Night Stretcher | 3 | 2.87 | 3 | 相同 |
| Crispin | 2 | 2.01 | 2 | 相同 |
| Unfair Stamp | 1 | 1.00 | 1 | 相同 |
| Judge | 1 | 0.91 | 0 | 大致相同 |
| **Risky Ruins** | 0 | 1.76 | 2 | **我們沒有**：真實用來搶場地（換掉 Battle Cage）＋讓對手新放上的非惡基礎寶可夢多 2 個指示物 |
| **Jamming Tower** | 2 | 0.07 | 0 | **我們獨有**：場地卡位置對應 Risky Ruins，只有「換掉對手場地＋道具失效」功能，沒有傷害 |
| Rosa's Encouragement | 0 | 0.98 | 1 | 我們沒有 |
| Special Red Card | 0 | 0.37 | 1 | 我們沒有（對手剩 ≤3 張獎賞卡時讓對手洗手剩 3 張） |
| Dawn | 1 | 0.07 | 0 | 我們獨有（真實幾乎不用） |
| 能量 火／超／惡 | 4/4/2（10） | 3.09/3.10/2.25（約 8.5） | 3/3/3（9） | 我們能量多 1～1.5 張、惡能較少 |

變體：Worlds 中 Dragapult 純型 22.2%、Dusknoir 版 10.5%、Blaziken 版 9.8%（S14）。Louisville 冠軍與多數上位也是純型（S7）。

**差異對策略的影響**：
1. 沒有 Risky Ruins → 搶場地全靠 2 張 Jamming Tower，所以 R3 的「先放 Jamming Tower 再 Phantom Dive」很重要，而且 Jamming Tower 不要隨便浪費。
2. 沒有 Dudunsparce → 抽牌比真實牌表少一點，更依賴 Drakloak 數量（R10）。
3. 能量多 1 張 → 斷能風險比真實牌表低；對 Crustle 時牌庫裡非必要的牌稍多。

---

## 六、真實比賽的常見錯誤（零散彙整，沒有找到專文）

1. **沒有計畫就放指示物**（S16）→ R6。
2. **場上只留 1 隻 Drakloak**，被打掉後展開卡死（S11、S19）→ R10。
3. **對手手牌少時打洗手牌支援者**，等於送對手新手牌（S19 作者自己的失誤）→ R11。
4. **鏡像前期打 Judge**（S11：減 14.6 個百分點）→ R8。
5. **擊倒一隻會讓對手拿到資源的戰鬥寶可夢**：S19 作者被迫打倒對手的戰鬥寶可夢，結果讓對手拿到能量與 Boss。原則：可選時用 Boss 拉沒有能量的寶可夢（S19、S10）→ R5、R8。
6. **對手有 Battle Cage 還硬放指示物／移傷到備戰區**，指示物直接消失（卡面）→ R3。
7. **把 Phantom Dive 指示物放到貼 Mist Energy 的寶可夢上**（卡面＋FAQ）→ R2。
