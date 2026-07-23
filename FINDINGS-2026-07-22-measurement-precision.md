# Measurement precision — and three retracted mechanisms (2026-07-22)

Supersedes nothing; adds the error bar that every prior result in this repo lacked.

## 1. Run-to-run noise, measured for the first time

Study-1 is single-draw throughout, and the harness `--seed` flag could never have produced replicates: it feeds `random.Random()` for wrapper nonces only, while `cfg.gen.seed` (hardcoded 42) is what reaches llama.cpp. Varying `--seed` leaves turn-0 decisions bit-identical.

Varying `cfg.gen.seed` instead — 5 seeds x 5 models, `frozen` config, 209-item slice, all 80 fresh facts:

| model | k | mean | SD | min–max |
|---|---|---|---|---|
| qwen35-4b | 5 | 0.882 | 0.026 | 0.850–0.906 |
| ministral-3-3b | 5 | 0.863 | 0.008 | 0.856–0.875 |
| gemma-4-e2b | 5 | 0.854 | 0.028 | 0.831–0.900 |
| bonsai-27b-q1 | 5 | 0.850 | 0.014 | 0.831–0.869 |
| qwen35-2b | 5 | 0.834 | 0.020 | 0.806–0.863 |

**Pooled within-model SD = 0.0203 (df=20).** Per-run 90% band ±0.033; on a *difference of two single runs* — study-1's unit — **±0.047**.

Study-1's published gaps: #1 vs #2 = 0.031, #1 vs #4 = 0.040. Both inside that band.

Welch t on seed means vs qwen35-4b, Bonferroni over 4 comparisons:

| comparison | Δ | corrected p | verdict |
|---|---|---|---|
| ministral-3-3b | +0.020 | 0.630 | not separated |
| gemma-4-e2b | +0.029 | 0.503 | not separated |
| bonsai-27b-q1 | +0.032 | 0.181 | not separated |
| qwen35-2b | +0.049 | **0.043** | separated |

**The top four are one band.** Only qwen35-2b separates. The ordering reproduced exactly, so the differences may be real — but they are not resolvable at n=80 facts with a single draw.

Note: these levels are not comparable to study-1's published values. This slice caps variants at ≤2 per fact (study-1 has up to 34), which changes the estimand. What transfers is the variance and the ordering, not the absolute scores.

Caveat: one variance estimate, 5 models, k=5. Treat ±0.047 as the working figure, not a constant.

## 2. Three mechanisms tested, three retracted

Each was a plausible story fitted to a single-run difference. Each failed replication.

**Trigger clause → bonsai's under-searching.** Two rewrites of the `web_search` description moved fresh search propensity from 95.8% to 95.3% and 95.3%. See `PREREG-2026-07-21-trigger-clause.md`. Skips are stochastic (2 of 13 skipped items were consistent across 8 cells), not wording-driven.

**Reading ability → gemma-4-e2b's deficit.** An evidence-swap matrix (cell *(i,j)* = model *j* answering from model *i*'s retrieved evidence, 80 facts, zero HTTP) found reading differences of 0.025 across three models, none significant. gemma-4-e2b was numerically the *best* reader (0.892) and hedged least. The k=5 test says its gap to qwen35-4b is not significant in the first place.

**`read_url` → ministral's evidence quality.** Disabling it made ministral *worse* (0.887 → 0.831, p≈0.12). The decisive evidence is an internal control: the gap is the same on facts where `read_url` was never called (+0.059) as on facts where it was (+0.048). A tool that is not invoked cannot affect those items, so the difference is run variance, not the tool. **Leave `read_url_policy` alone.**

The swap's row effect that motivated this test (ministral evidence 0.833 vs qwen35-4b 0.908) also failed to hold: a same-day rerun of ministral scored 0.887. That row effect was an artifact of the single July-17 run used as evidence source.

## 3. What did replicate

- **bonsai-27b-q1 under-searches ~5% of fresh items** — SD 1.0 pt across seeds, stable across three prompt variants. Real, and not prompt-fixable.
- **qwen35-2b fires a paid search on 46.7% of chit-chat** (others 7.5–12.5%), across 5 seeds. Product-relevant and absent from the published board.
- **Query formulation is near-saturated**: first-query token Jaccard between model pairs 0.78–0.83; 54% of retrieval failures are shared by all four models — a dataset/engine ceiling, not a model property.

## 4. Corrections to published artifacts

- `study-1/LEADERBOARD.md` gate-failure `fresh` column reads `0.00` for all five models. Actual fact-level values: hermes-3-3b **0.073**, smollm3-3b **0.055**, gemma-3-1b-q4 **0.023**, phi-4-mini **0.017**, gemma-3-4b **0.005**. The column is hand-entered; `export_site.py` emits no `fresh` field for gate-failures.
- `study-1/page_content.json` says "5 of 9 packages never received the search tools". The roster is 9 passers + 5 failures = **14**.
- `study-1/LEADERBOARD.md` states golds are "disjoint from judge". True of the *verification* step only: `study-1/generate.py:50` sets the eval judge (deepseek-v4-flash) as the primary drafter of questions and golds.

## 5. Method notes for study-2

1. Replicates require `cfg.gen.seed`, never `--seed`. Add a regression test.
2. k≥5 on anything a conclusion depends on. Nothing at n=80 facts, single draw, resolves a 3-point difference.
3. Report `from_cache` per cell. Cross-model evidence asymmetry (6%→58% by run order in study-1; 66%→94% here) remains unfixed and cannot be fixed by `replay-only`, which raises `CacheMiss` on any query not already recorded.
4. Restate the leaderboard as bands, as `export_site.py:268` already instructs ("render groupings, not medal positions").
