# study-1 — ADMISSION SUMMARY

Anchor 2026-07-14. Curator panel: openrouter:z-ai/glm-5.2, openrouter:openai/gpt-5.6-luna. Provider: brave. Freshness window: 60d.

## Verdicts per split

| split | admit | drop | needs_human | total |
|---|---|---|---|---|
| fresh | 507 | 0 | 268 | 775 |
| stable | 43 | 0 | 2 | 45 |
| unanswerable | 0 | 5 | 11 | 16 |
| no_search | 35 | 0 | 0 | 35 |
| **all** | **585** | **5** | **281** | **871** |

## Splits (admit items only, split by fact_id)

- distinct admitted fact_ids: 187
- dev: 420 items / 131 facts
- holdout.sealed: 165 items / 56 facts
- no fact_id appears in both (partitioned by fact_id).

## Dropped items (5)

- **g1u-01** (unanswerable): panel_found_confident_answer_item_is_answerable
- **g1u-02** (unanswerable): panel_found_confident_answer_item_is_answerable
- **g1u-06** (unanswerable): panel_found_confident_answer_item_is_answerable
- **g1u-13** (unanswerable): panel_found_confident_answer_item_is_answerable
- **g1u-14** (unanswerable): panel_found_confident_answer_item_is_answerable

## needs_human queue composition

- total needs_human: 281
  - gold_disputed_panel_agrees_other: 163
  - gold_uncertain_panel_split: 74
  - recurring_needs_valid_until: 33
  - unanswerable_confirmed_awaiting_negative_signoff: 11

- ambiguous fact-cluster pairs: 2
- multi-item fact clusters (auto-merged, confirm): 99

See HUMAN_QUEUE.md for the actionable per-item list.
