# study-1 — RESOLUTION SUMMARY

Anchor 2026-07-14. Auto-resolution of the 28 `needs_human` items — NO human review (owner rule: anything that does not cleanly settle is DROPPED). Panel (agentic, search+read) = openrouter:anthropic/claude-sonnet-5 + openrouter:openai/gpt-5.6-sol; equality/credibility judge = openrouter:openai/gpt-4o-mini.

## Resolved per queue category

| category | admit | drop |
|---|---|---|
| disputed | 5 | 1 |
| recurring | 9 | 0 |
| unanswerable | 13 | 0 |

**Total: 27 resolved-admit, 1 dropped.**

## Golds overwritten (panel is the oracle) — audited & trimmed

The panel adopted its full verbose sentence as the new gold, which is too wordy for judging.
Each overwrite was audited: all five were the SAME fact as the original, merely wordier, so the
crisp original gold was kept and the verbose form preserved on the receipt as `resolved_gold_verbatim`.
Format below: `original` -> (verbatim panel form) -> **gold used in dataset**.

- **fr2-news-02**: `Evian-les-Bains, France` -> (`Évian-les-Bains, France`) -> **`Evian-les-Bains, France`** (same fact, diacritic only)
- **fr2-tech-08**: `$91 billion` -> (`$91.0 billion, plus or minus 2%`) -> **`$91 billion`** (same number, wordier)
- **fr2-tech-14**: `Salesforce's Fin acquisition` -> (`Salesforce buying Fin`) -> **`Salesforce's Fin acquisition`** (same fact, rephrased)
- **fr3-col-02**: `Google Gemini` -> (`Siri AI powered by Apple and Google Gemini`) -> **`Google Gemini`** (same core fact, added context)
- **fr3-und-11**: `macOS Golden Gate` -> (`macOS 27 Golden Gate`) -> **`macOS Golden Gate`** (same name, added version)

None were judged a genuinely different fact; no new value was adopted.

## Dropped items

- **fr2-news-08** (gold_disputed_panel_agrees_other): agentic panel did not both produce a specific answer (a='', b='It was **Syria**. President **Ahmed al-S') -> drop

## Splits (rebuilt from ALL admitted items, split by fact_id)

- total admitted items: 142
- dev: 96 items / 67 facts
- holdout.sealed: 46 items / 28 facts
- no fact_id appears in both (partitioned by fact_id).
- (splits re-clustered after the gold-trim audit; clustering keys partly on gold text, so counts shifted from the pre-audit 93/49 while total items stayed 142.)

