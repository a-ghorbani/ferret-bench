# Report — Agentic web search for small on-device LLMs

**Experiment**: `2026-07-10-web-search-agentic-config` (ferret-bench) · **Dataset**: v1 (sha256 `d3502755…`, 44 fresh / 30 stable / 15 no_search, anchor 2026-07-10) · **Judge**: google/gemini-3.5-flash, prompt `v2-simpleqa-3way-acceptable`, temp 0 (validation below) · **Loop**: faithful replica of PocketPal PR #808 (`harness/CONTRACT.md`) · All tables regenerable from `analysis/scores.jsonl` (v2-judge numbers throughout); every number traces to `runs/<run-id>/`. Statistical tests are one-sided Fisher exact on correct-counts unless noted; with 17 screening arms tested, screening p-values are uncorrected and treated as hypothesis-generating only.

## Executive summary

1. **Small models can genuinely drive web search — this benchmark saturates.** With the frozen config, huihui-qwen35-2b (a community abliterated Qwen3.5-2B variant), qwen35-4b, and ministral-3-3b each score **0.977 fresh** — the same score as the gemma-4-31B ceiling reference (0.977; qwen3.6-27B: 0.955). At this n the correct reading is that these models **saturate dataset v1**, whose practical ceiling is ~0.98 (single-fact, single-search questions); parity on harder multi-hop tasks is untested. Without search, the same fresh questions score 0.023 (floor).
2. **Configuration matters as much as model choice at the small end.** The frozen bundle beats the shipped config pooled over 4 dev models: 162/176 vs 139/176 fresh (0.920 vs 0.790, p=0.0004); on qwen3-06b alone, 39/44 vs 25/44 (p=0.0008), driven by search engagement rising 0.77→0.98.
3. **The frozen config** = PocketPal shipped defaults + a three-change bundle: **enriched tool descriptions + Brave + markdown result formatting** (a2). The bundle is what's validated; per-factor attribution is screening-level evidence only (RQ2–RQ4). Everything else (5 results, 280-char snippets, read_url available @4800 chars, 5 turns, untrusted wrapper) stays as shipped — measured, not assumed (`frozen-config/PROVENANCE.md`).
4. **5 of 13 candidate models fail the capability gate** (never execute a tool call): gemma-3-1b/4b, phi-4-mini, smollm3-3b, hermes-3-3b. Three distinct failure modes (RQ6) — one (Gemma-3's `tool_code` format) looks fixable at the app level.

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

## Reproducing

`README.md` — quick start, re-run sweep, add a model, refresh dataset, regenerate tables (`harness/aggregate.py` + `harness/leaderboard.py`).
