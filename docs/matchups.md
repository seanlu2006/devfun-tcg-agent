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
