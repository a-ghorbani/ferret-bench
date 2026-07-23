# Pre-registration — trigger-clause test (2026-07-21)

Status: **written before any arm was run.** Arm strings, outcomes, predictions and guardrails below are frozen. Amending any of them after seeing data makes this a new test with new predictions, not a continuation.

## Question

study-1 ranked bonsai-27b-q1 4th (fresh 0.83) despite it beating the leader on the subset it actually searched (0.899 vs qwen35-4b 0.894 on the same 376 items). Its entire deficit is 23 fresh items (5.8%) where it never called the tool — schema rendered, no error, one turn, answered confidently from stale parametric memory.

**Hypothesis (H1):** the deficit is caused by the search trigger being conditioned on the model's *self-assessed* knowledge rather than on properties of the *question*. That conditioning is scale-inverted — a model with more parametric knowledge feels "unsure" less often — so the frozen config systematically under-triggers search on large or heavily-quantized models.

Supporting observation: the system prompt and the tool description **disagree**. The system prompt says *"For time-sensitive or factual questions, search first"* (question-side, no self-reference). The tool description says search for things *"you are unsure about"* (self-referential). On the stable split, where the conflict is sharpest, qwen35-4b searches 48.4% and bonsai 12.9% — same instructions, opposite resolutions. Arms B1/B2 do not add an instruction; they remove a contradiction.

## Arms

Single factor: `tool_desc`. `system_prompt` is `shipped` (PR #808 verbatim) in every cell. Within `tool_desc`, only the **tail of the `web_search` description** varies — topic list, query-style guidance, return description and both `read_url` strings are byte-identical across arms.

| arm | `tool_desc` | tail of `web_search` description |
|---|---|---|
| **A** (control) | `enriched` | "…or any fact that **may have changed since your training data** or that **you are unsure about**." |
| **B1** | `no-cutoff` | "…or any fact that **you are unsure about**." |
| **B2** | `parallel` | "…**any fact whose answer can change over time**, or anything **you are unsure about**." |

- **A vs B1** — does the training-cutoff reference contribute anything? (It asks the model to reason about its own cutoff, which small models do badly and often get factually wrong. Worth dropping on reliability grounds independent of this test.)
- **B1 vs B2** — is uncertainty sufficient as the sole catch-all, or does it need a question-side trigger *beside* it? B2 retains the uncertainty clause in full; the volatility criterion fires independently of confidence.

Arm A at seed 42 hashes identically to `frozen` (`bbb5cdbf1e9f18d7`), so the control is provably the exact config study-1 ran.

`guided-v2` was considered as a fourth arm and **dropped**: it varies `system_prompt` rather than `tool_desc` (not a comparable cell), it still contains both the cutoff reference and a confidence escape hatch, and it produced the worst false-search rate in the corpus (qwen3-06b, 53.3%).

## Replication

k=3 per cell, varying **`cfg.gen.seed`** (42/43/44).

Not the harness `--seed` flag: that feeds `random.Random()` for wrapper nonces and tool-call IDs only. `cfg.gen.seed` is passed through to llama.cpp, so with it fixed the turn-0 decision is bit-identical regardless of `--seed`. Varying `--seed` would have produced fake replicates on the primary outcome. This is the likely reason no replicate exists anywhere in the 206 prior runs.

## Sample

`study-1/datasets/dev` restricted to `qids-trigger-test.txt` — 209 items: 150 fresh (**all 80 facts**, ≤2 variants each), plus all 24 `no_search`, 31 `stable`, 4 `unanswerable`. The variant cap also equalises the 1–34 imbalance that makes study-1's fact-level mean an arbitrary weighting.

## Outcomes

**Primary — fresh-split search propensity** (share of fresh items with ≥1 `web_search`).

Chosen because it is the decision the hypothesis is about, and because it is measured at **turn 0, before any search result is seen**. It is therefore immune to the evidence-freezing problem (live-vs-replay, cache staleness, run ordering) that is the largest threat to validity in this corpus, and it requires no judge, so the LLM-graded truth stack is out of the loop.

**Secondary:** stable-split search rate; fresh accuracy (fact-level); searches per answered question.

**Guardrail:** `no_search` false-search rate.

## Predictions

| # | prediction |
|---|---|
| P1 | bonsai, B2: fresh search rate rises from 94.2% to **≥99%** |
| P2 | bonsai, B1: **weaker or no effect** than B2 — B1 keeps the self-assessment gate, which is the clause H1 blames |
| P3 | bonsai, B1 and B2: `no_search` false-search stays **≤15%** (from 8.3%) |
| P4 | qwen35-4b, qwen35-2b: fresh search stays ~100%; fresh accuracy within **±3 pts** of arm A |
| P5 | bonsai, B2: stable-split search rate rises from 12.9% toward qwen35-4b's ~48% (tests the conflict account specifically) |
| P6 | lfm2-2.6b, B2: false-search falls from 88% *(weak prediction — stated for the record, not relied on)* |

**Falsification of H1:** bonsai's fresh search rate does not move materially under either B1 or B2. Then the trigger clause is not the mechanism, the config-class hypothesis dies, and study-2 must look elsewhere. B1 may still be worth shipping on cutoff-reliability grounds.

## Staging

**Stage 1** — bonsai only, 3 arms × 3 seeds = 9 runs (~3.7 h). Decisive: if bonsai does not move, stop.
**Stage 2** — *conditional on stage 1 being positive* — qwen35-4b, qwen35-2b, lfm2-2.6b, 3 arms × 3 seeds = 27 runs (~4.6 h). These answer "does it hurt anyone", worth asking only once something helps.

Staged by model, not by arm: every arm comparison then stays **within one model and one stage**, so the days between stages cannot become an arm effect. Each model carries its own control. Within a model, arms are interleaved within seed (free — one model load) so drift during a run does not align with an arm.

## Analysis

Paired across arms within model, bootstrapped over facts. Seeds are replicates, not units — report the between-seed spread; it is the first such estimate in this repo.

## Scope

A mechanism diagnostic, not a leaderboard result. It does **not** license any change to study-1's published ranking, does not touch the sealed holdout, and is not a search for an optimal config. Its only job is to determine whether study-2 looks for one config or a small set of config classes.

---

# Outcome (2026-07-22)

**H1 falsified.** Stage 1 ran 9 cells on bonsai-27b-q1 (3 arms x 3 seeds, 209 items, zero failures).

Fresh-split search propensity:

| arm | s42 | s43 | s44 | mean |
|---|---|---|---|---|
| A `enriched` (control) | 95.3% | 96.7% | 95.3% | **95.8%** |
| B1 `no-cutoff` | 94.7% | 95.3% | 96.0% | **95.3%** |
| B2 `parallel` | 94.0% | 96.7% | 96.0% | **95.3%** |

P1 (B2 >= 99%) fails: 95.3%, indistinguishable from control. P5 (stable-split rate rises toward ~48%) fails: 8.6 / 7.5 / 8.1% vs a 12.9% baseline. P3 guardrail holds but is moot. The pre-registered falsification criterion — no material movement under either B1 or B2 — is met.

**Why.** Of 13 fresh items skipped at least once across 8 cells, only 2 were skipped in all 8. The skip is stochastic — bonsai sits near a ~95% search probability and the misses are borderline draws at temperature 0.7, not systematic refusals that wording can reach. The 2 consistent refusals ("When did the LHC shut down for its four-year upgrade?", "What organization developed the AlphaFold protein structure database?") read as timeless encyclopedia facts, so declining to search them is defensible; this is a dataset observation, consistent with 24 of 80 fresh facts being answerable with no tools at all.

**Stage 2 not run**, per the pre-registered gate.

**Shipping note.** B1 is still worth adopting on reliability grounds independent of this result: the cutoff clause asks a model to reason about its own training cutoff, which small models do poorly and often get wrong. It costs nothing measurable (95.3% vs 95.8%, inside seed noise).

**Incidental result, larger than the intended one.** These were the first replicate runs in the repo. See `FINDINGS-2026-07-22-measurement-precision.md`.
