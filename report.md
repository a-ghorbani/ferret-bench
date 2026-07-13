# Report — Agentic web search for small on-device LLMs

> ## ⚠️ Read this first: two rounds, and the current result is v2
>
> This report is append-only and documents **two rounds** of the experiment.
>
> - **Part 1 (below)** is **v1** — 44 single-fact questions. It **saturated**: eight models tied near 0.98 and the board could not separate them. Its config findings (the frozen bundle) remain current and shipped; its *model ranking* is superseded.
> - **[Part 2 — v2](#v2--tiered-dataset--frontier-anchors-2026-07-12)** (bottom of this file) is the **current model leaderboard**: 53 questions across four retrieval-difficulty tiers, plus frontier anchors. It de-saturates the board and produces the headline finding — small models are frontier-grade on everyday lookups and degrade on hard retrieval.
>
> **If you only read one part, read v2.** The v1 executive summary immediately below is retained for provenance; where it and v2 disagree about model standings, **v2 supersedes it**.

---

## Part 1 — v1 (superseded for model ranking; config findings still current)

**Experiment**: `2026-07-10-web-search-agentic-config` (ferret-bench) · **Dataset**: v1 (sha256 `d3502755…`, 44 fresh / 30 stable / 15 no_search, anchor 2026-07-10) · **Judge**: google/gemini-3.5-flash, prompt `v2-simpleqa-3way-acceptable`, temp 0 (validation below) · **Loop**: faithful replica of PocketPal PR #808 (`harness/CONTRACT.md`) · All tables regenerable from `analysis/scores.jsonl` (v2-judge numbers throughout); every number traces to `runs/<run-id>/`. Statistical tests are one-sided Fisher exact on correct-counts unless noted; with 17 screening arms tested, screening p-values are uncorrected and treated as hypothesis-generating only.

## Executive summary

1. **Small models can genuinely drive web search — this benchmark saturates.** With the frozen config, huihui-qwen35-2b (a community abliterated Qwen3.5-2B variant), qwen35-4b, and ministral-3-3b each score **0.977 fresh** — the same score as the gemma-4-31B ceiling reference (0.977; qwen3.6-27B: 0.955). At this n the correct reading is that these models **saturate dataset v1**, whose practical ceiling is ~0.98 (single-fact, single-search questions); parity on harder multi-hop tasks is untested. Without search, the same fresh questions score 0.023 (floor).
2. **Configuration matters as much as model choice at the small end.** The frozen bundle beats the shipped config pooled over 4 dev models: 162/176 vs 139/176 fresh (0.920 vs 0.790, p=0.0004); on qwen3-06b alone, 39/44 vs 25/44 (p=0.0008), driven by search engagement rising 0.77→0.98.
3. **The frozen config** = PocketPal shipped defaults + a three-change bundle: **enriched tool descriptions + Brave + markdown result formatting** (a2). The bundle is what's validated; per-factor attribution is screening-level evidence only (RQ2–RQ4). Everything else (5 results, 280-char snippets, read_url available @4800 chars, 5 turns, untrusted wrapper) stays as shipped — measured, not assumed (`frozen-config/PROVENANCE.md`).
4. **5 of 13 candidate models fail the capability gate** (never execute a tool call): gemma-3-1b/4b, phi-4-mini, smollm3-3b, hermes-3-3b. *(**Revised** by the Addendum below and by v2: there are **two** classes, not three — structural (template never declares tools, so schemas are never rendered: gemma-3-1b/4b **and hermes-3-3b**) vs compliance (schemas rendered, model refuses: phi-4-mini, smollm3-3b). An app-side text-parser shim is **not** sufficient; the fix is a tool-declaring chat template. See the Addendum.)*

## Answers to research questions

**A note on evidence tiers.** Screening (n=20/config, 17 one-factor arms, 2 dev models) generates hypotheses; the full-dataset ablation (n=44 fresh) validates config *bundles*; no full-n single-factor arms were run except a1, so individual factor effects inside the winning bundle are not separately identified. This design limitation is flagged per-RQ below (adversarial review findings #3–#4, accepted).

### RQ1 — result count → **5 (shipped default retained)**

Screening found no level that beat 5: rc3 0.75/0.85 (qwen3-1.7b/ministral), rc8 0.65/0.80 with more tokens, vs shipped 0.70/0.80. rc8 is additionally capped by the app's 1000-token menu ceiling, which silently drops trailing hits — raising the count without raising the ceiling is a no-op. Runs: `20260710-224903/225215/234816/234943-screen-*`. (Screening-tier evidence; no full-n follow-up because no level showed promise.)

### RQ2 — result formatting → **markdown list (as part of the frozen bundle)**

JSON (0.75/0.85) and compact-numbered (0.70/0.80) formats gave no gain over shipped labeled-blocks (0.70/0.80) at screen and were eliminated. Markdown is in the frozen bundle because the bundle containing it (a2) was the best full-dataset performer: 2-dev composite 0.932 vs a1 (same bundle minus markdown) 0.841 and shipped 0.875→(v2: 0.875 = (0.7727+0.9773)/2). Isolated markdown-vs-shipped at full n was not run; the markdown *increment* within the bundle (a2 vs a1: qwen 39/44 vs 33/44, ministral 43/44 vs 41/44) is suggestive, not significant individually. Runs: `2026071*-ablate-a1/a2-*`, screen fmt-* runs.

### RQ3 — prompting → **enriched tool descriptions in the bundle; system prompt: shipped grounding line retained**

Enriched descriptions were the largest screening effect (0.95/1.00 vs shipped 0.70/0.80; `20260710-231840`, `20260711-000342`) and are in every winning combo — but the full-n a1 run (enriched+brave *without* markdown) scored at-or-below shipped (0.750 vs 0.773 qwen; 0.932 vs 0.977 ministral), so the enriched-description effect is **not separable from the bundle** at full n (review finding #3, accepted). System prompt: a strategy-explicit variant (guided) helped at screen but fired searches on 29% of no-search questions; the v2 rewrite fixed false-search (0.0 across ablate) yet **stacking guided-v2 with markdown hurt** (a6 2-dev composite 0.864 vs a2's 0.932 — anti-synergy; `2026071*-ablate-a6-*`). The system prompt therefore stays shipped; guided-v2 is the documented prompt-only runner-up (`harness/configs.py`).

### RQ4 — provider → **Brave (recommended default; screening-tier evidence)**

Brave-vs-Tavily at screen: pooled over both dev models 36/40 vs 30/40 (p=0.07, uncorrected; `20260710-232202`, `20260711-000529`), and the Tavily variant of the guided bundle lost at full n (a5 2-dev 0.784 vs a3 0.909). Token cost is model-dependent: Brave cut ministral prompt tokens ~24% (1736→1321) but qwen3-1.7b used ~10% more (1174→1290). Verdict: Brave is the recommended default on the evidence available; the effect is not isolated at full n (no brave-only arm), and Tavily remains fully supported (BYOK user choice).

### RQ5 — search→read loop → **read_url stays available; limits & turn cap unchanged; snippets carry the load**

Reads are rare but model-dependent: qwen models ≤0.01 reads/question; ministral 0.17–0.46 depending on config (max: read-encouraged 0.46, snip140 0.43). Snippet-only answering matched or beat read-enabled configs (a4 = 1.000 on ministral, 44/44) but cost engagement on qwen3-1.7b (0.86 vs 0.93); read_url is a shipped product feature and stays available. Content limits 2400/9600 and turn caps 3/8: within noise of shipped 4800/5 at screen. The turn budget is not binding — winners average 1.7–1.9 turns. Runs: ablate a4, screen readlim*/turns*/read-*.

### RQ6 — model ranking (<8B, frozen config, dataset v1)

| rank band | model | fresh ✓ [CI90] | stable ✓ | engage | false-search | notes |
|---|---|---|---|---|---|---|
| A | huihui-qwen35-2b | 0.977 [0.90,0.99] | 0.97 | 1.00 | 0.20 | abliterated community variant |
| A | qwen35-4b | 0.977 [0.90,0.99] | 1.00 | 1.00 | 0.00 | **recommended ship** |
| A | ministral-3-3b | 0.977 [0.90,0.99] | 0.97 | 1.00 | 0.00 | **recommended ship** |
| A | gemma-4-e2b | 0.932 [0.84,0.97] | 1.00 | 1.00 | 0.07 | |
| A | lfm25-1.2b | 0.909 [0.81,0.96] | 0.97 | 0.95 | 0.20 | best ≤1.5B |
| A | qwen3-06b | 0.886 [0.78,0.94] | 0.90 | 0.98 | 0.33 | smallest viable |
| A | qwen3-1.7b | 0.841 [0.73,0.91] | 0.97 | 0.93 | 0.00 | |
| A | mlabonne-qwen3-4b | 0.841 [0.73,0.91] | 0.97 | 0.91 | 0.07 | community fine-tune |
| — | *ceiling: gemma-4-31B Q8* | 0.977 | 1.00 | 1.00 | 0.00 | context row |
| — | *ceiling: qwen3.6-27B Q8* | 0.955 | 0.97 | 0.98 | 0.00 | context row |
| B (gate fail) | gemma-3-1b-q4, gemma-3-4b, phi-4-mini, smollm3-3b, hermes-3-3b | 0.00–0.02 | 0.20–0.97 | 0.00 | 0.00 | never execute a tool call |

**What n=44 resolves**: band A vs band B (gate pass/fail) is decisive. **Within band A, the ranking is NOT statistically separated** — 90% CIs overlap from rank 1 through rank 8 (top vs qwen3-06b: p=0.20; vs qwen3-1.7b: p=0.058) (review finding #2, accepted). The table order is the point estimate; treat within-band positions as provisional until more data (seeds or harder items) accumulates on the leaderboard.

**Capability-gate failure modes**, from transcripts (`20260711-1951*/1952*/2002*/2004*/2007*-confirm-*`): (a) **format mismatch** — gemma-3 wants to search and emits Gemma-style ` ```tool_code ` blocks the OpenAI-format parser can't map: fixable app-side with a format shim or chat-template change; (b) **capability denial** — phi-4-mini answers "I can't perform web searches"; (c) **silent hallucination** — hermes-3-3b fabricates answers with plausible fake citations (the worst UX: confidently wrong). gemma-3-4b's stable score (0.20) is also depressed because it keeps trying to emit `tool_code` even for memory questions.

### RQ7 — baselines

**Floor** (no tools): fresh 0.023 (1/44) on qwen3-1.7b and ministral-3-3b at full n (`20260711-0858/0955-ablate-floor-*`; screen floors agree: `20260710-2246/2347-*`), and **0.000 (0/44)** on both rank-1 models huihui-qwen35-2b and qwen35-4b (`20260712-083638/085121-floorfix-floor-notool-*`, added after adversarial review) — retrieval is provably the mechanism on the models that matter. Floor + gate-failure evidence identifies **three** fresh questions answerable without live retrieval (fr-news-03, fr-tech-05, fr-news-12 — flagged for demotion at v2 refresh per `datasets/README.md`); their effect is symmetric across configs. Stable floor 0.83–0.97 confirms the stable split is memory-answerable. **Ceiling**: large local models through the same harness score 0.955–0.977 fresh — the dataset's practical ceiling — reached by three sub-4B models (see saturation caveat, exec summary #1). Amendment #2 replaced the original frontier-cloud ceiling with local models (no cloud key; reproducible).

## Frozen configuration

See `frozen-config/` (machine-readable: `config.json`, `tool_web_search.json`, `tool_read_url.json`, `system_prompt.txt`) and `PROVENANCE.md` for the per-value table (updated post-review to bundle-level framing), including anti-recommendations (JSON formatting; result_count 8 without raising the menu ceiling; stacking guided-v2 prompt with markdown formatting).

## Judge validation

- **Manual labels** (committed: `analysis/judge-validation-manual-labels.json`): control-agent blind labels on a stratified 40-item sample; agreement 38/40 with judge v1 — both disagreements were a judge-prompt bug (acceptable answers omitted), fixed in v2 — and **39/40 vs the final v2 judge** (the residual item is a borderline key-fact-with-wrong-side-details case, logged).
- **CORRECT-precision on fresh** (committed: `analysis/judge-correct-precision-sample.json`, seed 11): 60 randomly sampled judged-CORRECT fresh items from confirm runs — **60/60 contain the gold or an acceptable answer verbatim** (normalized substring; one-sided 90% lower bound ≈0.96). Grade inflation at the top of the leaderboard is bounded by this.
- **Judge-vs-judge**: gemini-3.5-flash vs local qwen3.6-27b on 14 screen runs: 92.1% raw (361/392); 18/31 disagreements were the local judge's own parse failures.
- Limitation: manual labels are the control agent's (an LLM), not independent human labels.

## Limitations & not tested

- **Saturation**: the fresh split (14 easy / 21 medium / 9 hard, single-fact, one 7-week EN-only window) cannot discriminate above ~0.93 — top-of-table ties, and "equals the ceiling," are statements about the dataset as much as the models. Harder/multi-hop items are the v2 priority.
- **Bundle vs factors**: only the a2 bundle is validated at full n; per-factor attributions (RQ2–RQ4) are screening-tier (n=20, 17 uncorrected comparisons) and the a1 run shows they do not compose naively.
- **Statistical resolution**: single generation per question (temp 0.7, seed 42); within-band ranking unresolved at n=44.
- **Providers**: Exa and Parallel not tested (no keys; Parallel gated in-app).
- **Environment**: quality measured on workstation llama.cpp with phone-class Q4 GGUFs; on-device latency/thermals/memory not measured — turns and tokens are the cost proxies.
- **Judge**: remote (OpenRouter) — reruns need a key; local fallback documented. Groundedness was dropped (amendment #7): the judge never sees fetched evidence, so a correct-but-ungrounded answer is invisible to scoring; the floor baselines bound this risk but do not eliminate it.
- **Replay cache**: pins repeated queries; model-generated queries differ across configs/models, so captures span 2026-07-10..12 and later runs could see fresher web state for novel queries. Comparability is approximate, not exact.
- Model identity: two ranked models are community variants (huihui abliterated 2B, mlabonne 4B fine-tune); official checkpoints may differ.

## Addendum (2026-07-12, post-COMPLETE) — RQ6 gate-failure taxonomy revised

Root-cause work with the PocketPal implementer (PR #808) **revises RQ6's failure-mode split**. Full derivation and evidence tables in `JOURNAL.md` (entry: "RQ6 gate-failure root cause").

**Mechanism.** PocketPal parses no tool calls itself; llama.cpp does, selecting a parser via a differential autoparser gated on `jinja_caps.supports_tool_calls` — computed by probe-rendering the model's chat template to see whether it ever reads `tools[]`/`tool_calls`. A template that ignores `tools` ⇒ caps false ⇒ **content-only parser ⇒ `tool_calls` is structurally always empty**, whatever the model emits. Crucially, such a template also means **the tool schemas are never rendered into the prompt**: the model knows the tools only by name (from the grounding system line) and has never been shown a signature. That is why gemma improvises Gemma-native ```tool_code``` — and why an app-side text-parser shim would *not* be sufficient (the model would still be guessing the signature). A sufficient fix must put the schema into the prompt *and* parse the syntax out; the implementer is doing this by supplying a tool-declaring chat template on the completion params.

**Two classes, not one** (chat templates read from the GGUFs we ran, `tokenizer.chat_template`):

| model | `tools` refs in template | class | evidence from our runs (n=89) |
|---|---|---|---|
| gemma-3-4b | 0 | **structural** — parser cannot see a call | 0 tool_calls; **64/89** responses contain a ```tool_code``` fence |
| gemma-3-1b-q4 | 0 | **structural** | 0 tool_calls; 5/89 fences — and it guesses the *wrong* name (`search_web`, not `web_search`), direct evidence it never saw a schema |
| hermes-3-3b | 0 (bare ChatML, 291 chars) | **structural** | 0 tool_calls, 0 fences — fails *silently* |
| phi-4-mini | 3 | compliance — schema IS rendered, model refuses | 0 tool_calls; denies the capability in prose |
| smollm3-3b | 15 | compliance | 0 tool_calls |

**Corrections this forces to §RQ6 above:**
1. **hermes-3-3b is structurally blocked, not non-compliant.** The `Hermes-3-Llama-3.2-3B.Q4_K_M` GGUF ships a bare ChatML template with zero `tools` references despite upstream Hermes-3 being marketed as tool-calling. Its "silent hallucination with plausible fake citations" (failure mode (c) above) is therefore not a model choosing to lie — it is a **structurally muzzled model failing unsafely**, where gemma fails visibly. A template override should recover it.
2. **The template-override fix addresses 3 of the 5 gate failures** (gemma-3-1b, gemma-3-4b, hermes-3-3b), not just the Gemma family.
3. **Only phi-4-mini and smollm3-3b are true compliance failures** — the schema reaches them and they still won't call. Different lever needed; note `tool_choice` is never set on PocketPal's local path (only the remote path), so nothing nudges a local model toward `required`.

**Caveat:** caps are inferred from the GGUF-embedded template (what llama.cpp uses by default and what these runs used); a build substituting a bundled template for a known architecture could differ. The empirical column (0 tool_calls for all five) is consistent with the inference in every case.

**Also corrected — RQ1's ceiling mechanism.** Our "raising result_count past ~5 is a no-op" phrasing named the wrong mechanism: the budget was charged against a differently-rendered string than the model actually received, making the drop marginal and input-dependent rather than a flat no-op. The recommendation (do not raise result_count without raising the ceiling) stands. Now moot upstream: PocketPal landed `eab95f6b` (charge the ceiling against the rendered menu) on 2026-07-12, along with `e257258c` (markdown menu) and `668e81d7` (enriched tool descriptions) — i.e. the frozen-config bundle is adopted.

## Reproducing

`README.md` — quick start, re-run sweep, add a model, refresh dataset, regenerate tables (`harness/aggregate.py` + `harness/leaderboard.py`).

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


---

# Correction (2026-07-12, post-publication) — RQ6 gate-failure taxonomy: **one class, not two**

**What was published and is now withdrawn.** The v1 Addendum and the first v2 write-up split the five gate failures into *structural* (Gemma-3-1B/4B, Hermes-3-3B — template never declares tools) and *compliance* (Phi-4-mini, SmolLM3-3B — "schemas rendered, model refuses"). **The compliance class does not exist.** All five are structural.

**Why the error happened.** The compliance claim rested on counting `tools` substrings in `tokenizer.chat_template` as a proxy for tool-calling capability. That proxy is wrong: llama.cpp computes capability by *probe-rendering* the template with a synthetic tools array and checking whether it ever reads `tools[].function.name`. Phi-4-mini and SmolLM3 *mention* the variable but never render it under the actual invocation. A substring is not a render.

**The decisive evidence — from our own run data, which had it all along.** `usage.prompt_tokens` on turn 1 is the cleanest capability probe in this repo: it is exactly what the runtime tokenized.

| model | median turn-1 prompt tokens | tool calls |
|---|---|---|
| phi-4-mini | 105 | 0 |
| hermes-3-3b | 116 | 0 |
| gemma-3-1b | 122 | 0 |
| gemma-3-4b | 122 | 0 |
| smollm3-3b | 146 | 0 |
| gemma-4-e2b | 363 | 89 |
| ministral-3-3b | 371 | 94 |
| qwen3-1.7b | 452 | 72 |
| qwen35-4b | 576 | 116 |

Perfectly bimodal. Every gate-failing model renders ~105–146 tokens — system line plus question, with no room for the `web_search`/`read_url` schemas. The 250–450-token gap **is** the schema. Phi-4-mini and SmolLM3 never saw the tools either. Runs: `20260712-*-confirm2-frozen-*`.

**What this changes.**

1. **One failure class.** The tool-declaring-chat-template fix is worth **5 of 5**, not 3 of 5.
2. **Phi-4-mini was not refusing.** Its "I can't perform web searches in real-time" is a model *honestly reporting it has no tools* — because it had none. We read a structural bug as a behavioural one and published it as model misbehaviour. That was wrong and is retracted.
3. **`tool_choice: "required"` is moot** for these models — you cannot require a tool the model was never shown. (Recommendation withdrawn.)
4. **Severity differs only in failure *mode*, not cause** — by user harm: Hermes-3 (fabricates with fake citations — **unsafe**) > Gemma-3 (improvises a visible `tool_code` fence) > Phi-4-mini (honest disclosure — arguably the *correct* behaviour given its prompt).
5. **The leaderboard label was defamatory and is fixed.** "Models that can't search" flattened five very different models into a verdict about *them*, when it was an artifact of *our* prompt rendering. The tell was in our own data: Gemma-3-4B scores 0.20 on the stable split while SmolLM3 scores 0.97 — these are not the same kind of model, and neither was ever given a tool. The row group is now labelled **"the tool definitions never reach these models"**.
6. **The gate recommendation gets stronger:** gate on *rendered capability*, never on a model-family allowlist. A runtime canary — *tools were passed, but the rendered prompt is < ~300 tokens ⇒ the schemas did not land* — catches all five and any future GGUF repack that silently drops the tool template. The harness now asserts exactly this (`harness/agent_loop.py`); it would have caught this on day one.

**Provenance.** Root cause raised by the PocketPal PR #808 implementer; substring-proxy error introduced in an addendum committed to this repo by another agent while this session was idle; independently verified here against `runs/*confirm2*/outputs.jsonl` before acceptance. The earlier addendum's two-class taxonomy is superseded by this section wherever they disagree.

**Numeric note.** The implementer quoted ~1646/2055 turn-1 tokens for ministral/qwen35-4b where we measure 371/576. The discrepancy is almost certainly a later-turn measurement (after the results menu enters context) or a different config; the bimodal gap and the conclusion are identical either way. Our figures are turn-1, frozen config, dataset v2.

---

# v3 — The clean board: thinking OFF, quantization recorded, discarded answers recovered (2026-07-12)

Two uncontrolled factors and one harness bug were found *after* v2 was published. All three are fixed; **this board supersedes v2's model ranking entirely.** Runs: `20260712-*-confirm3-frozen-*` (primary), `20260712-*-thinkon-*` (ablation). Config hash `bbb5cdbf…` (thinking off). Dataset v2 unchanged.

## What was wrong with v2

1. **Quantization was never controlled and never recorded.** `factors.md` claimed "Q4_K_M — held constant". False: Qwen3-1.7B ran at **Q6_K**, the abliterated Qwen3.5-2B at **Q8_0**, mlabonne-Qwen3-4B at **Q4_K_S**. Manifests pinned only a model *alias*, so a score could not be traced to the weights that produced it — despite the protocol requiring exactly that. Now `resolve_weights()` records gguf path + quant + size in every manifest and **quant is a column on the leaderboard**.
2. **Thinking was an accident of model choice, not a controlled condition.** Qwen models reasoned; Gemma/Ministral/Phi could not. Comparing them was never apples-to-apples.
3. **The harness discarded answers.** The loop read only `content`. Thinking models sometimes end their turn *inside* the reasoning block: llama.cpp then routes the whole answer to `reasoning_content` and returns `content=''`. We scored those as NOT_ATTEMPTED. Blank-final rates: **qwen35-2b 17.3%, mlabonne-qwen3-4b 12.2%, qwen3-1.7b 7.1%, every non-thinking model 0%.** Proven, not inferred: on a blank case the model had correctly found "Ankara" — the answer was sitting in `reasoning_content` and we threw it away. Fixed (fallback + `answer_from_reasoning` / `empty_content_turns` canaries).

**These three interacted to produce a false finding** (see retraction below), which is why the whole board was re-run.

## RQ8 (new) — Should a phone-class model think while doing agentic search? **No.**

Same models, same questions, same config; only `enable_thinking` differs.

| model | fresh, thinking OFF | fresh, thinking ON | quality Δ | completion tokens OFF → ON | token tax |
|---|---|---|---|---|---|
| Qwen3.5-4B | 0.887 (47/53) | 0.924 (49/53) | +0.038 | 172 → 367 | **2.1×** |
| Qwen3.5-2B | 0.717 (38/53) | 0.792 (42/53) | +0.076 | 168 → 376 | **2.2×** |
| Qwen3-1.7B | 0.585 (31/53) | 0.491 (26/53) | −0.094 | 147 → 718 | **4.9×** |
| Qwen3-0.6B | 0.528 (28/53) | 0.585 (31/53) | +0.057 | 89 → 503 | **5.7×** |
| Qwen3-4B (mlabonne) | 0.604 (32/53) | 0.641 (34/53) | +0.038 | 181 → 763 | **4.2×** |
| **pooled** | **176/265 = 0.664** | **182/265 = 0.687** | **+0.023** | — | **2–6×** |

**No per-model difference is significant** (Fisher p = 0.44–0.84); pooled p = 0.64. Thinking buys **+0.023 correctness — indistinguishable from noise — for 2–6× the generated tokens.** On a phone, inside a loop whose context is already dominated by search results, that is a straight loss: more latency, more battery, more context pressure, no measurable answer gain. One model (Qwen3-1.7B) is actually *worse* with thinking on.

**Recommendation: ship agentic web search with reasoning mode OFF.** It is also the only way to compare thinking-capable and non-thinking models honestly, which is why the primary board uses it.

## RETRACTION — "the abliterated Qwen3.5-2B beats the official one"

v2 reported this as a surprise worth replicating (0.830 vs 0.641). **It is false, and it was an artifact of our own bugs.** Two causes, both ours:

- The official model *thinks*; the abliterated one does not (abliteration suppresses it). The discarded-answer bug therefore penalised **only the official model** — 17.3% of its answers were thrown away.
- They were also compared at **different quantizations** (Q8_0 vs Q4_K_M).

With thinking off and the bug fixed, at their shipped quants:

| | fresh |
|---|---|
| Qwen3.5-2B abliterated (Q8_0) | **38/53 = 0.717** |
| Qwen3.5-2B official (Q4_K_M) | **38/53 = 0.717** |

**Identical** (p = 0.59). The abliteration effect is zero. Nobody should ship an abliterated variant on the strength of our earlier number, and the roster policy (official checkpoints rank; variants are labelled comparison rows) is vindicated.

## The corrected board (thinking off, one config, quant shown)

| model | quant | fresh ✓ [CI90] | T1 | T3+T4 |
|---|---|---|---|---|
| *Claude Sonnet 5 (cloud ref)* | — | 0.981 | 20/20 | 21/21 |
| *GPT-5.6-sol (cloud ref)* | — | 0.981 | 20/20 | 21/21 |
| **Qwen3.5-4B** | Q4_K_M | **0.887 [0.80,0.94]** | 19/20 | 19/21 |
| Ministral-3-3B | Q4_K_M | 0.811 [0.71,0.88] | 20/20 | 14/21 |
| Qwen3.5-2B | Q4_K_M | 0.717 [0.61,0.81] | 18/20 | 13/21 |
| Gemma-4-E2B | Q4_K_M | 0.679 [0.57,0.77] | 18/20 | 10/21 |
| LFM2.5-1.2B | Q4_K_M | 0.660 [0.55,0.76] | 18/20 | 12/21 |
| Qwen3-1.7B | Q6_K | 0.585 [0.47,0.69] | 17/20 | 9/21 |
| Qwen3-0.6B | Q4_K_M | 0.528 [0.42,0.64] | 16/20 | 5/21 |
| *5 models never offered the tools* | Q4_K_M | 0.00–0.08 | — | — |

**Qwen3.5-4B is the recommended ship**, and the recommendation is now stronger than in v2: it is top of the on-device board (band separates from the bottom: p<0.001), it is the only small model whose accuracy does **not** collapse on hard retrieval (T1 0.95 → T3+T4 0.90), and it achieves that at Q4_K_M — the quant a phone actually runs — with thinking off. Ministral-3-3B remains the fallback for tiers where the 4B will not fit: perfect on everyday lookups (T1 20/20), materially weaker on multi-source/multi-hop (14/21).

The easy-vs-hard gradient survives all corrections and is the durable finding: pooled on-device **0.89 → 0.55**, while both cloud references stay flat at ~0.98.

## What this episode says about the benchmark

Three published claims were wrong, and every one was our infrastructure, not the models: five models "refused to search" (never given tools), an abliterated model "won" (its sibling's answers were being deleted), and a leaderboard "held quantization constant" (it did not). Each was caught by someone asking a plain question about the data. The harness now carries canaries for the first two (`schema_not_rendered`, `empty_content_turns`) and records the weights for the third — but the general lesson is the one worth publishing: **when a benchmark says a model is bad, suspect the benchmark first.**


---

## Addendum (2026-07-13) — community variants removed from the board

The two community-variant rows are gone from the published leaderboard, chart and site payload. They were ablations pretending to be entries.

- **`mlabonne-qwen3-4b`: dropped outright.** It violated our own rule (amendment #11: keep a variant *only* where its official sibling is on the board). **Official Qwen3-4B was never on the board** — so the row was compared against nothing, while sitting third from bottom under the name "Qwen3-4B" and implying a verdict on a model we never measured. That is the same failure as labelling five models "can't search" when we never gave them tools: a reader draws a conclusion about a *model* from an artifact of *our roster*.
- **`huihui-qwen35-2b` (abliterated): retained in `runs/`, removed as a row.** Its comparison was legitimate and it is now **answered**: at matched conditions, 38/53 vs the official checkpoint's 38/53 — abliteration is worth exactly nothing. An answered question belongs in a sentence, not in a permanent row that invites someone to ship an abliterated model on the strength of a number that no longer says what it appeared to say.

The published board now contains only **official checkpoints** (the things PocketPal could actually ship) plus two clearly-marked cloud references. Variant results remain in `report.md` and in the site's `variants_note`. Nothing is hidden; it is simply not *ranked*.
