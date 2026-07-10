# Datasets — curation & refresh protocol

## Structure

Each version lives in `datasets/v<N>/`:

- `questions.jsonl` — the assembled, validated question set (this is what runs pin by sha256)
- `meta.json` — `{version, anchor_date, created, counts, sha256}`
- `staging/` — per-split source files merged by `assemble.py`

Question schema:

```json
{"id": "fr-news-01", "split": "fresh|stable|no_search", "question": "...", "gold_answer": "...|null",
 "acceptable_answers": ["..."], "category": "...", "difficulty": "easy|medium|hard",
 "event_date": "YYYY-MM-DD (fresh only)", "source_urls": ["... (fresh only)"], "notes": "..."}
```

## Splits and what they measure

| Split | Size (v1) | Purpose |
|---|---|---|
| `fresh` | ~40 | Events/facts that post-date small-model training cutoffs (curation window ends at `anchor_date`) — retrieval required by construction; the config/model signal lives here |
| `stable` | 30 | Timeless facts — measures whether the search loop *hurts* memory-answerable questions, and feeds the floor comparison |
| `no_search` | 15 | Questions where searching is unnecessary/wrong — measures false-positive tool firing (mechanical only, excluded from correctness) |

## Fresh-split curation rules

1. Window: events settled between (anchor_date − ~8 weeks) and (anchor_date − 2 days).
2. Answer must be a single, short, unambiguous fact that can never change later (finished events; no live prices/standings).
3. Phone-user phrasing; the question must not contain the answer.
4. Gold answer verified against ≥2 independent sources or 1 authoritative one; `source_urls` recorded.
5. Difficulty mix per curator beat: ~1/3 easy (headline), ~1/2 medium (specific detail), ~1/5 hard (answer in article body, not snippets).
6. Beats: (a) world news/politics, (b) sports/entertainment, (c) tech/science/business — 15 candidates each, merged and deduped.
7. Curation is agent-driven (LLM with live web access executing the rules above); the assembled set is validated by `validate.py` and floor-checked (rule 8).
8. **Floor demotion**: after assembly, run the no-tool floor with a dev model; any `fresh` question the floor answers correctly is flagged for review (likely leaked into parametric memory or guessable) — demote to `stable` or drop.

## Refresh protocol (fresh questions go stale)

Fresh questions stop being "post-cutoff" as newer models arrive, and the replay cache ages. To refresh:

1. Create `datasets/v<N+1>/staging/` and re-run the fresh-split curation (rules above) with a new window ending at the new `anchor_date`. Keep `stable`/`no_search` unless flagged.
2. Run `python3 assemble.py v<N+1>` → validates, assigns ids, writes `questions.jsonl` + `meta.json` with the new hash.
3. Capture a fresh replay cache: run the reference sweep with `--http-mode live` once, then everything else replays.
4. **Re-anchoring rule**: scores across dataset versions are NOT comparable. After a refresh, re-run the reference models (see harness README) on the new version before comparing any new model against the leaderboard; the leaderboard keys rows by `dataset_version`.

## Validation

Validation is built into assembly: `python3 assemble.py v1 --anchor-date YYYY-MM-DD` checks schema completeness, id uniqueness, near-duplicate questions (fuzzy), fresh items' event_date + source_urls + gold answers, then writes `questions.jsonl` and `meta.json` with the content hash. Errors block assembly; warnings print for review.
