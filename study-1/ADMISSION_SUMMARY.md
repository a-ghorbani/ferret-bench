# study-1 — ADMISSION SUMMARY

Anchor 2026-07-14. Curator panel: openrouter:anthropic/claude-sonnet-5, openrouter:openai/gpt-5.6-sol. Provider: brave. Freshness window: 60d.

## Verdicts per split

| split | admit | drop | needs_human | total |
|---|---|---|---|---|
| fresh | 70 | 0 | 15 | 85 |
| stable | 30 | 0 | 0 | 30 |
| unanswerable | 0 | 0 | 13 | 13 |
| no_search | 15 | 0 | 0 | 15 |
| **all** | **115** | **0** | **28** | **143** |

## Splits (admit items only, split by fact_id)

- distinct admitted fact_ids: 81
- dev: 81 items / 57 facts
- holdout.sealed: 34 items / 24 facts
- no fact_id appears in both (partitioned by fact_id).

## Dropped items (0)


## needs_human queue composition

- total needs_human: 28
  - unanswerable_confirmed_awaiting_negative_signoff: 13
  - recurring_needs_valid_until: 9
  - gold_disputed_panel_agrees_other: 5
  - gold_uncertain_panel_split: 1

- ambiguous fact-cluster pairs: 0
- multi-item fact clusters (auto-merged, confirm): 15

See HUMAN_QUEUE.md for the actionable per-item list.
