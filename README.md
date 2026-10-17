# devfun-tcg-agent

A Pokémon TCG agent for the [dev.fun Arena](https://arena.dev.fun) **TCG Playground S3**, where AI agents play each other and a 1,250 USDC pool goes to the top of the board.

The season is **owner-hosted** (`executionMode: remote`): our own process polls the arena for decision points, calls `act(context)` from `harness/strategy.py`, and posts the action back. The deck is locked for the whole season on the first join. There is no public game engine, so this repo builds its own safety net from the public match logs and a local mock arena.

## How it works

```
data/raw/ (public matches) ──► tests/replay_test.py ──► harness/strategy.py ──► dist/bundle.zip
            │                                                 ▲
            └──► tools/explore_options.py ──► docs/protocol.md┘
```

- **`harness/strategy.py`** — the agent. A crash-proof `act()` shell, a `Board` helper that decodes the numeric observation format, and the strategy functions (`score_main_option`, `choose_other`).
- **`docs/protocol.md`** — the decision-point format, reverse-engineered from ~2,500 public decisions because the API does not document the option codes.
- **`tests/replay_test.py`** — replays every public decision point through the agent and fails on any illegal action, uncaught exception, Python 3.12+ syntax, or non-stdlib import.
- **`tools/build_bundle.py`** — validates the deck, then builds the zip and smoke-tests it by extracting it into an empty directory and calling `act()` under `python3 -I -S`.

## Usage

```bash
python3 tools/fetch_public.py 20                      # download catalog + 20 recent matches
python3 tools/build_assets.py                         # trim the catalog into assets/catalog.json
python3 tests/replay_test.py                          # must print PASS
python3 tools/validate_deck.py decks/starter_dark.json
python3 tools/build_bundle.py decks/starter_dark.json # -> dist/bundle.zip

python3 tests/runner_e2e.py                           # runner vs local mock arena; must print PASS

python3 tools/arena_client.py register <handle> "<name>" "<quote>"   # once; stores the API key in .arena-credentials
python3 tools/arena_client.py claim                   # X verification link / status
python3 tools/run_agent.py --deck decks/<deck>.json --max-matches 3  # first join LOCKS the deck for the season
python3 tools/run_agent.py --max-matches 10           # later runs; Ctrl-C once = stop after the current match
```

Earlier versions assumed a hosted-bundle season; `tools/build_bundle.py` and `arena_client.py submit` are kept for hosted seasons but the server rejects bundles for this one.

## Status

- [x] Bundle pipeline, replay tests, deck validator
- [x] Protocol notes for option, select, area and log codes
- [ ] Real strategy (v0 is a priority list: evolve → energy → bench → trainers → attack)
- [ ] Tuned deck (the starter deck exists to test the pipeline)
