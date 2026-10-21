# devfun-tcg-agent

A Pokémon TCG agent that played 1,031 ranked matches in the dev.fun Arena **TCG Playground S3** (Oct 17–20, 2026). It never cracked the top 10. What it did produce is a working answer to a harder question: how do you improve a game-playing agent when the engine is closed, the opponents change under you, and ten games tell you almost nothing?

| | |
|---|---|
| Matches played | 1,031 (481 wins) |
| Best rank | 62 of ~123 agents (Oct 19) |
| Final rank | 81 of 126, score 475 (top-10 cutoff: 693) |
| Strategy code | `harness/strategy.py`, 2,234 lines, stdlib only |
| Commits | 76, each one tested against 56,743 public decision points |

## Why I built this

I didn't start from Pokémon. In the fall I was surveying ways to earn money with under $500 of capital: prediction markets, DeFi points, airdrops, and app leaderboards on Solana. The conclusion of that research was unflattering. At my budget, almost every option capped out at $15–85 a year, and many were funnels that paid out less than players spent. The only items worth my time were the ones that cost $0 and left something behind.

The dev.fun Arena was one of them. Entry was free, the season had a 1,250 USDC prize pool, and the task was to write an agent that plays a real card game against other people's agents. I wrote down at the time that its portfolio value was higher than its prize value, and I still think that was right. The prize rules were never published (the official docs even contradict each other on whether the board is ranked for reward), so I treated the money as a bonus.

There was a second reason. I wanted to learn how to design decision-making systems under real constraints, not toy ones:

- **The engine is closed.** There is no simulator. The API sends numeric option codes with no documentation.
- **Information is hidden.** Public match logs mask every player's hand, so you can't learn directly from the best players.
- **The deck locks on the first join.** One choice, for the whole season.
- **Everything is live.** Every experiment costs ranked games against agents that are also improving.

## How it was built

I ran this as the person directing AI coding agents. Claude Code (Anthropic) wrote most of the code: the runner, the test harness, the strategy, the planner. OpenAI Codex worked as a read-only analyst on lost games. My job was the decisions: which deck to lock, when to trust a proposed rule, when an experiment was worth the ranked games it cost, when to change the method, and when to stop. Every rule had to pass the same gate no matter who proposed it, and several Codex proposals were rejected by the data (see below).

## What I found

### 1. Win rate over a batch is mostly noise

For the first two days the loop was: play 10 games, review the losses, add a rule, repeat. A full audit on day three showed that loop could not have worked. To measure it, I ran an A/B test: two versions alternating match by match, identical except for the rules that only fire against one deck (Crustle). In the 155 games without Crustle, both versions made the same moves. Their win rates were 36% and 47%. At 35 games each, the gap was 31% vs 49%.

So two identical strategies drifted 11 to 17 points apart on luck alone. Every "this version went 6–4, that one went 4–6" comparison from the first two days was reading tea leaves.

### 2. Matchmaking hides progress

The arena pairs agents by strength. As we climbed, the median opponent's score rose from about 350 to about 520, and raw win rate stayed flat. Splitting results by opponent rank showed what was really happening: we improved a lot against agents ranked 91st and below (51% → ~73%) and not at all against the top 60 (33–37% throughout).

### 3. The agent wasn't too passive

When the goal moved to "top 10," the obvious idea was an aggressive, attack-first strategy. I measured it against the two Dragapult players in the top 10 before building anything:

| | This agent | StartupBros (#9) | antge-poker-bot-01 (#3) |
|---|---|---|---|
| First Phantom Dive (median turn) | 7 | 7 | 7 |
| Attacked when an attack was available | 98% | 94% | 95% |
| Win rate in games where Phantom Dive happened | **48%** | **66%** | **76%** |

We were already as fast and more aggressive. The gap was in what happened around the attacks, so I built a planner instead.

### 4. A turn planner, kept on a short leash

The original strategy scores each option on its own. That misses lines that only work as a sequence. The clearest case: two prizes from winning, Boss's Orders in hand, a 180-HP target on the opponent's bench. The winning line was *retreat → Boss's Orders → Phantom Dive*. Scored one step at a time, retreat looked useless, so the agent ended its turn three times in a row and then decked out.

The planner simulates the tactical skeleton of a turn (evolve, attach, retreat, Boss's Orders, attack) on a copy of the board and scores where each line ends up. Calibration changed its role:

- Allowed to make every attack/retreat decision, it agreed with the experts **less** than the old rules did (245 vs 249 of 452 decisions, across 24 weight settings). Strong players take hits to keep attacking, and my exposure penalty was too cautious.
- So it only overrides the old rules when a line **takes more prizes this turn** or **escapes a loss next turn**. At that setting it ties the old rules on expert agreement.

In live play over 40 games it overrode 12 times and predicted 11 prizes. All 11 were taken; the two lines that looked like misses in the logs had simply ended the game. Two real bugs surfaced along the way and were fixed, including one where an item card shuffled away the Boss's Orders the plan depended on.

### 5. Some losses were the deck, not the play

Against Crustle (a wall that takes no damage from ex Pokémon), the agent won 33% over 212 games. StartupBros plays nearly the same 60 cards and went 4–5 against Crustle in the public logs. antge went 12–4, but antge's list runs Blaziken ex, a second attacker that can hurt the wall. My deck was locked on day one and couldn't add it.

## What I'd do differently

- **Pick the measurement before the first change.** A/B testing came on day three. It should have been the starting point, with batch win rates ignored.
- **Treat small rules as unmeasurable by outcome.** A rule that changes 8 of 40,000 decisions will never show up in win rate. Judge it by replaying real decision points and comparing against expert choices.
- **Check the meta before locking the deck.** I picked Dragapult because it led the board when I joined. Crustle's share of the field grew afterwards, and I never asked how a locked list would fare if a wall deck rose.
- **Get the prize rules in writing first.** I stopped on Oct 20 because top 10 looked out of reach with this deck and the payout structure was never published.

## How it works

```
arena ◄──► tools/run_agent.py ──► harness/strategy.py ──► act(observation) → action
                │                       │
                │ logs every board       ├─ per-option scores (rules, each with a regression test)
                ▼                       └─ turn planner (multi-step lines, override-only)
        data/runs/*_obs.jsonl
                │
                ├──► tests/replay_test.py    replay 56,743 public decisions: legal moves, no crashes
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
