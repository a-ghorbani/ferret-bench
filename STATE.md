# Live status

Updated 2026-07-22. This is the one file tracking where the project is. Everything else is spec or history — see the repository map in `README.md`.

## Current

**study-1** is the active study: 9-model leaderboard on a validator-built dataset, dev split only.
**Disposition: exploratory, not confirmed.** The sealed holdout has never been run.

- Leaderboard: `study-1/LEADERBOARD.md` — **read as bands, not ranks** (ranks 1–4 are one statistical band)
- Dataset: 193 facts admitted; dev 131 / holdout.sealed 56, zero fact overlap
- Config: `frozen` (`harness/configs/frozen.json`, hash `bbb5cdbf1e9f18d7`)

## Open

| item | status |
|---|---|
| Holdout confirmation run | never run — one-shot resource, do not spend on the current design |
| Evidence-freezing (cross-model cache asymmetry) | unfixed; `replay-only` cannot fix it (`CacheMiss` on unseen queries) |
| Human ground truth | none in study-1; golds drafted and graded by LLMs |
| Fact clusters over-merged | union-find groups unrelated facts (`fact_007` spans 3 topics); sizes 1–34 |
| Dataset below target | 193 facts vs ~400 declared |
| False-search column | measured but unpublished (qwen35-2b 46.7% on chit-chat) |
| v2/v3 pages in `README.md` / `report.md` | superseded by study-1; withdrawal notice still needed |

## Recently closed

- **Measurement precision** — run-to-run SD measured (0.020, k=5) → `FINDINGS-2026-07-22-measurement-precision.md`
- **Trigger-clause hypothesis** — falsified → `PREREG-2026-07-21-trigger-clause.md`
- **`read_url` hypothesis** — falsified by internal control; leave `read_url_policy` alone
- **Gate-failure `0.00` column, "5 of 9" roster count, judge/drafter claim** — corrected 2026-07-22

## Next

1. Restate remaining artifacts as bands; withdrawal notice on v2/v3 pages
2. Contributor packaging: untrack `cache/`, tests + CI, `pyproject.toml`, `CONTRIBUTING.md`, README repo-map
3. Only then: holdout confirmation, with evidence freezing fixed and k≥5
