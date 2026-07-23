# Tests

```bash
cd tests && python3 -m unittest discover     # stdlib, no install needed
pytest tests/                                 # also works if you prefer pytest
```

No network, no GPU, no API keys. Runs in ~20 ms.

## What is covered, and why

Every test here exists because something actually broke. The harness's published
retractions were harness bugs, not model behaviour, so these pin the contracts that
went wrong rather than aiming at coverage.

| file | pins |
|---|---|
| `test_pocketpal_replicas.py` | `to_plain_text`, `truncate_on_word_boundary`, `estimate_tokens` — the functions that replicate PocketPal PR #808. If they drift, published numbers stop describing the app. |
| `test_seed_and_cache_contracts.py` | `cfg.gen.seed` is the only sampling seed (the `--seed` flag drives nonces only, which is why 206 runs contained no true replicate); `cache_key` stability, key-order and secret redaction; the pinned `frozen` config hash. |
| `test_agent_loop.py` | Every termination path (no calls, turn cap, forced final without tools, LLM error), tool-error handling, disabled-tool refusal, both canaries (schema-not-rendered, answer-in-reasoning), tool-call id backfill, and the fact that `n_searches` counts provider calls rather than model attempts. |
| `test_run_manifest_contract.py` | Run dirs carry the keys `judge.py` and `aggregate.py` read without a default. Validates the live `runs/` tree; skips cleanly when absent. |

## Adding one

If you fix a harness bug, add the test that would have caught it, and say in the
docstring what broke. That is the convention the codebase already follows in its
comments — keep it.

Changing a pinned value (`frozen` config hash, a golden `cache_key`) is a contract
change, not a test fix: update `harness/CONTRACT.md` in the same commit and say why.
