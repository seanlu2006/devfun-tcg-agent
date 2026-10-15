# devfun-tcg-agent

A Pokémon TCG agent for the [dev.fun Arena](https://arena.dev.fun) **TCG Playground S3** — a hosted-bundle competition where AI agents play each other and a 1,250 USDC pool goes to the top of the board.

The platform runs our code in an offline Python 3.11 sandbox and calls `act(context)` at every decision point. There is no public game engine, so this repo builds its own safety net from the public match logs.

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

python3 tools/arena_client.py register                # once; stores the API key in .arena-credentials
python3 tools/arena_client.py submit                  # upload dist/bundle.zip
python3 tools/arena_client.py status                  # versions, matches used, rank
python3 tools/arena_client.py stop                    # pause the latest version to save allowance
```

The match allowance is per agent and can be spent in under 30 minutes, so test locally before every submit.

## Status

- [x] Bundle pipeline, replay tests, deck validator
- [x] Protocol notes for option, select, area and log codes
- [ ] Real strategy (v0 is a priority list: evolve → energy → bench → trainers → attack)
- [ ] Tuned deck (the starter deck exists to test the pipeline)
