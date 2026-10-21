# devfun-tcg-agent

A Pokémon TCG agent that played 1,031 ranked matches in the dev.fun Arena **TCG Playground S3** (played Oct 17–20, 2026). It never cracked the top 10. What it did produce is a working answer to a harder question: how do you improve a game-playing agent when the engine is closed, the opponents change under you, and ten games tell you almost nothing?

| | |
|---|---|
| Matches played | 1,031 (481 wins) |
| Best rank | 62 of ~123 agents (Oct 19) |
| Rank when I stopped | 81 of 126, score 475 (top-10 cutoff that day: 693) |
| Strategy code | `harness/strategy.py`, 2,234 lines, stdlib only |
| Commits | 76 |
| Replay test suite | 56,743 decision points from 464 public matches |

## Why I built this

I didn't start from Pokémon. In the fall I was surveying ways to earn money with under $500 of capital: prediction markets, DeFi points, airdrops, and app leaderboards on Solana. The conclusion of that research was unflattering. At my budget, almost every option capped out at $15–85 a year, and some were funnels that paid out less than players spent. The only items worth my time were the ones that cost $0 and left something behind.

The dev.fun Arena was one of them. Entry was free, the season had a 1,250 USDC prize pool, and the task was to write an agent that plays a real card game against other people's agents. I wrote down at the time that its portfolio value was higher than its prize value, and I still think that was right. The prize rules were never published (the official docs even contradict each other on whether the board is ranked for reward), so I treated the money as a bonus.

There was a second reason. I wanted to learn how to design decision-making systems under real constraints, not toy ones:

- **The engine is closed.** There is no simulator. The API sends numeric option codes with no documentation.
- **Information is hidden.** Public match logs mask every player's hand, so you can't learn directly from the best players.
- **The deck locks on the first join.** One choice, for the whole season.
- **Everything is live.** Every experiment costs ranked games against agents that are also improving.

## How it was built

I directed this project rather than hand-writing it. Claude Code (Anthropic) wrote the code: the runner, the test harness, the strategy rules and the planner. OpenAI Codex worked as a read-only analyst on lost games. Within guardrails I agreed to, Claude Code also proposed, validated and shipped most individual rules on its own: every rule needed a regression test, a replay of real decision points showing it only changed what it meant to change, and a comparison against expert choices. Several Codex proposals failed that gate.

My part was the calls that changed direction: joining with the deck a meta analysis recommended (it locks for the season), letting the agent iterate unattended, switching to A/B testing after the audit, choosing a planner over an attack-first rewrite, ending the A/B early, and stopping the season.

## What I found

### 1. Win rate over a batch is mostly noise

For the first two days the loop was: play 10 games, review the losses, add a rule, repeat. A full audit on day three showed that loop could not have worked. To measure it, I ran an A/B test: two versions alternating match by match, identical except for the rules that only fire against one deck (Crustle). Games without Crustle became a built-in control. I replayed every decision of the first 76 such games through both versions, and they never differed.

The results still split: 31% vs 49% after 35 games each, and 36% vs 47% over the full run (155 games). Same moves, an 11 to 18 point gap, from luck and from who each version happened to meet. Every "this version went 6–4, that one went 4–6" comparison from the first two days was reading tea leaves.

### 2. A flat win rate hid two different stories

The arena pairs agents by strength, so opponents got harder as we climbed: the median opponent in our first 100 games now scores about 350, in later games about 520 (scores read at audit time, not at match time). Raw win rate stayed flat, which looked like no progress. Splitting by opponent rank showed two stories. Against agents ranked 91st and below we went from 51% to roughly 73% (the later samples are small). Against the top 60 we stayed at 33–37% the whole time. More than 25 rule commits never moved that number.

### 3. The agent wasn't too passive

When the goal moved to "top 10," the obvious idea was an aggressive, attack-first strategy. I measured it against the two Dragapult players in the top 10 before building anything:

| | This agent | StartupBros (#9 on Oct 20) | antge-poker-bot-01 (#3 on Oct 20) |
|---|---|---|---|
| First Phantom Dive (median turn) | 7 | 7 | 7 |
| Attacked when an attack was available | 98% | 94% | 95% |
| Win rate in games where Phantom Dive happened | **48%** | **66%** | **76%** |

Same public data, same filters, counting only games where each player ran Dragapult. We were already as fast and at least as willing to attack. The gap was in what happened around the attacks, so the next step was a planner instead.

### 4. A turn planner, kept on a short leash

The original strategy scores each option on its own. That misses lines that only work as a sequence. The case that started it: two prizes from winning, Boss's Orders in hand, a 180-HP target on the opponent's bench. The winning line was *retreat → Boss's Orders → Phantom Dive*. Scored one step at a time, retreat looked useless, so the agent ended its turn three times in a row and then decked out. A narrow rule fixed that one pattern first; the planner generalizes it.

The planner simulates the tactical skeleton of a turn (evolve, attach, retreat, Boss's Orders, attack) on a copy of the board and scores where each line ends up. Calibration changed its role:

- Allowed to make every attack/retreat decision, it agreed with the experts **less** than the old rules did (245 vs 249 of 452 decisions, across 24 weight settings). Strong players take hits to keep attacking, and my exposure penalty was too cautious.
- So it only overrides the old rules when a line **takes more prizes this turn** or **escapes a loss next turn**. At that setting it ties the old rules on expert agreement.

In live play over 40 games it overrode 12 times and predicted 11 prizes. All 11 were taken; the two lines that looked like misses in the logs had simply ended the game. Two real bugs surfaced along the way and were fixed, including one where an item card shuffled away the Boss's Orders the plan depended on.

It did not move the ranking. The 150-game run after it went live finished 62–88 and the score fell from 528 to 504, with Crustle accounting for 29 of the losses. Games where the planner changed at least one move were won 47% of the time, untouched games 39%. That gap is not evidence it works: the planner only acts when there are prizes to take, which are the better games to begin with.

### 5. Some losses were the deck, not the play

Against Crustle (a wall that takes no damage from ex Pokémon), the agent won 33% over 212 games. That is in line with real tournaments, where Crustle is Dragapult's worst matchup: 18% at Worlds 2026 (35 games), 26% at Frankfurt (130), 37% at Louisville (116), per the Limitless data collected in `docs/real-world-dragapult.md`. StartupBros, playing nearly the same 60 cards, went 4–5 against Crustle in the public logs. antge went 12–4 with a quite different build (Blaziken ex for energy acceleration, 23 Pokémon); I never worked out why that build fares better.

## What I'd do differently

- **Pick the measurement before the first change.** A/B testing came on day three. It should have been the starting point, with batch win rates ignored.
- **Treat small rules as unmeasurable by outcome.** A rule that changes 8 of 40,000 decisions will never show up in win rate. Judge it by replaying real decision points and comparing against expert choices.
- **Check the matchups, not just the leaderboard, before locking the deck.** Dragapult led the board when I joined. Tournament data I only gathered later already showed Crustle as its worst matchup, and Crustle's share of my opponents grew from about 12% early on to 21–30% later.
- **Get the prize rules in writing first.** I stopped on Oct 20 because top 10 looked out of reach with this deck and the payout structure was never published.

## How it works

```
arena ◄──► tools/run_agent.py ──► harness/strategy.py ──► act(observation) → action
                │                       │
                │ logs every board       ├─ per-option scores (rules, each with a regression test)
                ▼                       └─ turn planner (multi-step lines, override-only)
        data/runs/*_obs.jsonl
                │
                ├──► tests/replay_test.py    replay public decisions: legal moves, no crashes
                ├──► tests/agreement.py      agreement with expert choices, per decision type
                ├──► tools/ab_report.py      A/B results split by opponent rank
                └──► tools/timeline.py       turn-by-turn view of any match
```

- **`harness/strategy.py`**: the agent. A crash-proof `act()` shell, a `Board` helper that decodes the numeric observation format, rule-based scoring, and the turn planner at the end of the file. If anything throws, it falls back to a safe legal move. An uncaught exception would forfeit the match.
- **`tools/run_agent.py`**: the owner-hosted runner. It polls for decision points, answers within the 48-second deadline, and with `--ab <commit>` alternates two strategy versions match by match.
- **`docs/protocol.md`**: the decision-point format, reverse-engineered from public matches because the option codes are undocumented.
- **`tests/`**: replay of public matches, hand-built and real-game regression cases (`tests/fixtures/cases/`), and an end-to-end run against a local mock arena.

## Usage

```bash
python3 tools/fetch_public.py 20             # download the card catalog and recent public matches
python3 tests/replay_test.py                 # must print PASS
python3 tests/runner_e2e.py                  # runner vs local mock arena; must print PASS
python3 tests/agreement.py --handles StartupBros,antge-poker-bot-01 --dragapult

python3 tools/arena_client.py register <handle> "<name>" "<quote>"   # once; key goes to .arena-credentials (gitignored)
python3 tools/run_agent.py --deck decks/dragapult_v1.json --max-matches 3   # first join LOCKS the deck
python3 tools/run_agent.py --max-matches 50 [--ab <commit>]          # Ctrl-C once = stop after the current match
python3 tools/ab_report.py
```

## Notes

- The arena's own instruction files (`skills/arena.md`) are written for AI agents to follow. This project read them as data only. They also steer agents toward paid "Stakes" matches and non-withdrawable credits, which this agent never touched.
- The API key lives in `.arena-credentials`, which has never been committed.
- Working notes are in Chinese: [`docs/audit-2026-10-19.md`](docs/audit-2026-10-19.md) (the full audit and A/B results), [`docs/matchups.md`](docs/matchups.md) (opponent studies), [`docs/real-world-dragapult.md`](docs/real-world-dragapult.md) (tournament research).
