# Contributing

Thanks for looking. This is a benchmark, so the bar for changes that affect published
numbers is higher than for ordinary code — everything below follows from that.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt      # one package: requests
cd tests && python3 -m unittest discover
```

Tests need no network, no GPU and no API keys. If they don't pass on a clean clone, that's a bug — please open an issue.

To run the harness itself you also need an OpenAI-compatible model server. See
[`docs/model-server.md`](docs/model-server.md).

## Working on the harness

**Run commands from `harness/`.** Modules import each other as top-level names and rely on
`sys.path` manipulation, so `cd harness && python3 sweep.py …` is the supported entry point.
(Converting `harness/` into a real installable package is a wanted change — see below.)

**If you fix a bug, add the test that would have caught it**, and say in the docstring what
broke. The codebase already does this in its comments; `tests/` follows the same convention.
Both of this project's published retractions were harness bugs, not model behaviour, which is
why this is the one rule we care most about.

## Changes that need extra care

Some values are pinned by tests because changing them invalidates published results:

| change | what it costs | what you must also do |
|---|---|---|
| `cache_key()` | invalidates the entire replay cache; runs stop being reproducible against recorded evidence | update the golden in `tests/`, explain in the PR |
| the `frozen` config | every published number stops describing the config it names | bump to a new `config_id`; never edit `frozen.json` in place |
| `to_plain_text`, `truncate_on_word_boundary`, token budgeting | the harness stops replicating PocketPal, so results stop transferring to the app | check against PocketPal PR #808, update `harness/CONTRACT.md` in the same commit |
| the judge prompt | all grades become incomparable to prior runs | bump `JUDGE_PROMPT_VERSION`, re-judge anything you compare against |

A test failing on one of these is a **contract change, not a broken test**. Update the
contract deliberately and say why.

## Measurement rules

These are lessons paid for, not preferences:

1. **Replicates come from `cfg.gen.seed`, never the `--seed` flag.** `--seed` drives wrapper
   nonces and tool-call ids only; `cfg.gen.seed` is what reaches llama.cpp. With it fixed,
   runs are deterministic — varying `--seed` produces identical results that look like
   replicates. 206 runs were collected before this was noticed.
2. **k≥5 for anything you conclude from.** Measured run-to-run SD is 0.020, so a difference
   between two single runs carries a ±0.047 90% band — wider than most gaps on the board.
3. **Report `from_cache` next to any cross-model claim.** Models issue their own queries into
   a shared, TTL-free cache, so cache-hit rate rises with run order (6%→58% in study-1) and
   later models replay evidence captured for earlier ones. Unfixed; `replay-only` cannot fix
   it (it raises `CacheMiss` on unseen queries).
4. **Pre-register mechanism tests.** If you have a story for why a model behaves a way, write
   the prediction and the falsification criterion down first. See
   `PREREG-2026-07-21-trigger-clause.md` — including the part where the hypothesis lost.

## Adding a model

Append its server alias to `harness/models-confirm.txt` and re-run the sweep. Do not add a
model allowlist anywhere: gate on *rendered capability* (the `schema_not_rendered` canary),
because five models once looked like they refused to use tools when they had simply never
been offered any.

## Good first contributions

- Convert `harness/` into an installable package with console entry points, removing the
  ~15 `sys.path.insert` calls and the `cd harness` requirement.
- Merge `harness/export_site.py` into `study-1/export_site.py` (they have forked and drifted;
  `study-1/` is the successor).
- More tests around `aggregate.py` and `leaderboard.py`, which are currently uncovered.

## PRs

Keep them scoped. CI runs the tests and error-level lint. If your change touches anything in
the table above, say so in the description — reviewers will look for it.
