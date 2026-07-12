
---

# v2 — Tiered dataset + frontier anchors (2026-07-12)

**Dataset**: v2 (sha256 `e7544608…`, anchor 2026-07-12) — 53 fresh questions in four retrieval-difficulty tiers, 30 stable, 15 no_search. **Config**: unchanged frozen bundle (hash `2e5a7826…`). **Ceilings**: frontier models via OpenRouter through the *identical* harness, replacing v1's local 27B/31B (amendment #10). **Roster**: official checkpoints; community variants labelled (amendment #11). Runs: `20260712-*-confirm2-frozen-*`, floors `20260712-*-floor2-*`.

## Why v2 exists

v1 saturated: eight models sat within noise of each other and of a 31B reference, because every question was a single-fact lookup that one good search answers. v1's own report flagged this. v2 adds retrieval difficulty as a designed factor:

| tier | n | what it demands |
|---|---|---|
| T1 | 20 | answer is in the search-result snippets (everyday lookup) |
| T2 | 12 | answer is only in the page body — snippets are not enough (verified at curation time) |
| T3 | 9 | answer requires combining/reconciling two sources that never co-occur |
| T4 | 12 | second lookup depends on the first's result (multi-hop) |

## Result: the board separates, and the tier gradient is the finding

| model | class | fresh ✓ [CI90] | T1 | T2 | T3 | T4 |
|---|---|---|---|---|---|---|
| GPT-5.6-sol | anchor | 0.981 [0.92,1.00] | 20/20 | 11/12 | 9/9 | 12/12 |
| Claude Sonnet 5 | anchor | 0.943 [0.87,0.98] | 19/20 | 11/12 | 8/9 | 12/12 |
| **Qwen3.5-4B** | official | **0.924 [0.84,0.97]** | 19/20 | 11/12 | 8/9 | 11/12 |
| Qwen3.5-2B (huihui) | variant | 0.830 [0.73,0.90] | 18/20 | 10/12 | 7/9 | 9/12 |
| Ministral-3-3B | official | 0.811 [0.71,0.88] | 20/20 | 9/12 | 6/9 | 8/12 |
| Gemma-4-E2B | official | 0.774 [0.67,0.85] | 18/20 | 7/12 | 7/9 | 9/12 |
| LFM2.5-1.2B | official | 0.660 [0.55,0.76] | 18/20 | 5/12 | 5/9 | 7/12 |
| Qwen3.5-2B | official | 0.641 [0.53,0.74] | 14/20 | 5/12 | 8/9 | 7/12 |
| Qwen3-4B (mlabonne) | variant | 0.641 [0.53,0.74] | 18/20 | 8/12 | 3/9 | 5/12 |
| Qwen3-0.6B | official | 0.585 [0.47,0.69] | 17/20 | 5/12 | 5/9 | 4/12 |
| Qwen3-1.7B | official | 0.491 [0.38,0.60] | 16/20 | 3/12 | 2/9 | 5/12 |
| *gate failures* | — | 0.00–0.08 | — | — | — | — |

**1. The ranking is now resolved.** Top on-device model (Qwen3.5-4B, 0.924 [0.84,0.97]) vs bottom of the working band (Qwen3-1.7B, 0.491 [0.38,0.60]): non-overlapping 90% CIs, Fisher p < 0.00001. v1 could not separate any of these. Neighbouring rows remain within noise — read bands, not exact positions.

**2. The tier gradient separates small from frontier — everyday lookups do not.** Correctness on T1 vs T3+T4 combined:

| model | T1 | T3+T4 | drop |
|---|---|---|---|
| GPT-5.6-sol | 1.00 | 1.00 | 0.00 |
| Claude Sonnet 5 | 0.95 | 0.95 | 0.00 |
| Qwen3.5-4B | 0.95 | 0.90 | 0.05 |
| Ministral-3-3B | 1.00 | 0.67 | **0.33** |
| Qwen3-1.7B | 0.80 | 0.33 | **0.47** |

Frontier models do not degrade with retrieval difficulty on this set; small models do, and the degradation scales inversely with size. **Ministral-3-3B is perfect on everyday lookups and loses a third of the hard ones.** This is the honest shape of "small models can search": they are frontier-grade at the lookups people do most, and materially worse when a question needs several sources or a dependent second search.

**3. The best 4B is statistically indistinguishable from frontier — with a caveat.** Qwen3.5-4B (49/53) vs GPT-5.6-sol (52/53): Fisher p = 0.18, not significant at n=53. The point estimates differ (0.924 vs 0.981) and the tier table shows where: its only real losses are T4. Do not read this as parity — read it as "the gap has narrowed to the point this dataset cannot resolve it," which is a different and weaker claim.

**4. Mechanism confirmed again.** No-tool floors on v2: Qwen3.5-4B **0/53**, Ministral-3-3B 1/53. The board measures retrieval, not memory.

**5. Gate-failure taxonomy holds unchanged** (5 models, 0 tool calls each): structural (Gemma-3-1B/4B, Hermes-3-3B — templates never declare tools, so schemas are never rendered) and compliance (Phi-4-mini, SmolLM3-3B — schemas rendered, model refuses). See the v1 addendum for the root-cause analysis and the template-override fix.

**6. Official vs community variant.** The abliterated Qwen3.5-2B (0.830) outscores the official Qwen3.5-2B (0.641) — a large gap, driven by T1 (18/20 vs 14/20) and T2 (10/12 vs 5/12). This is a surprise and is reported as such rather than acted on: it is a single run on one dataset version, the variant carries a higher needless-search rate, and we have no mechanism for why abliteration would improve retrieval. Worth a dedicated replication before anyone ships a variant on this basis.

## v2 limitations (additional to v1's)

- The tier labels were validated at curation time (T2 items were checked to be absent from snippets), but tier *difficulty* is not orthogonal to topic: T3/T4 items skew toward politics/business because chained facts are easier to verify there.
- T3 has only 9 items; per-tier CIs are wide. The T1-vs-T3+T4 gradient is the robust claim, not any single tier's rate.
- Frontier anchors run through the same loop but on their own serving stacks; their latency/turn numbers are not comparable to local runs.
- One roster model (Gemma-4-E2B) carries an unused vision tower that is loaded to VRAM by the runtime; this affects memory accounting only, not numerics (see JOURNAL 2026-07-12).
