# Report — Agentic web search for small on-device LLMs

**Experiment**: `2026-07-10-web-search-agentic-config` (ferret-bench) · **Dataset**: v1 (sha256 `d3502755…`, 44 fresh / 30 stable / 15 no_search, anchor 2026-07-10) · **Judge**: google/gemini-3.5-flash, prompt `v2-simpleqa-3way-acceptable`, temp 0 (validation below) · **Loop**: faithful replica of PocketPal PR #808 (`harness/CONTRACT.md`) · All tables regenerable from `analysis/scores.jsonl`; every number below traces to `runs/<run-id>/`.

## Executive summary

1. **Small models can genuinely drive web search.** With the frozen config, Qwen3.5-2B, Qwen3.5-4B, and Ministral-3-3B each score **0.977 on retrieval-required questions — statistically indistinguishable from the 31B/27B ceiling references** (0.977 / 0.955) on this dataset. Even LFM2.5-1.2B reaches 0.909. Without search (floor), the same questions score ≤ 0.05.
2. **Configuration matters as much as model choice at the small end**: on qwen3-06b, the frozen config lifts fresh correctness from 0.568 (shipped) to 0.886 — mostly by raising search engagement from 0.77 to 0.98.
3. **The frozen config** = PocketPal shipped defaults + three changes: **enriched tool descriptions** (usage guidance + keyword-query hint), **Brave** as default provider, **markdown result formatting**. Everything else (5 results, 280-char snippets, read_url available @4800 chars, 5 turns, untrusted wrapper) stays as shipped — measured, not assumed (`frozen-config/PROVENANCE.md`).
4. **5 of 13 candidate models fail the capability gate** (never execute a tool call): gemma-3-1b/4b, phi-4-mini, smollm3-3b, hermes-3-3b. Three distinct failure modes (below) — one of them (Gemma-3's `tool_code` format) looks fixable at the app level.

## Answers to research questions

### RQ1 — result count → **5 (shipped default retained)**

3 results (screen: 0.75/0.85 on qwen1.7b/ministral) and 8 results (0.70/0.80, +tokens) showed no gain over 5 (0.75/0.80); 8 is additionally capped by the app's 1000-token menu ceiling, which silently drops trailing hits — raising the count without raising the ceiling is a no-op. Runs: `20260710-224903/225215/234816/234943-screen-*`.

### RQ2 — result formatting → **markdown list**

The single formatting win: markdown (bold title, date, snippet, `<url>`) beat the shipped labeled-blocks on the full dataset (a2 composite 0.920 over 4 models vs shipped 0.875) and decisively on gemma-4-e2b (0.932 vs 0.841). JSON and compact-numbered formats were dominated at screen (0.70–0.85) and eliminated. Runs: `2026071*-ablate-a2-*`, `20260711-1057/1107-tiebreak-a2-*`, screen fmt-* runs.

### RQ3 — prompting → **enriched tool descriptions (biggest single effect); system prompt: shipped grounding line retained**

Enriched descriptions (what to use the tool for + "write short keyword queries") was the largest single-factor effect at screen (0.95/1.00 vs shipped 0.75/0.80; `20260710-231840`, `20260711-000342`) and is in every winning combo. A strategy-explicit system prompt (guided) helped correctness but fired searches on 29% of no-search questions; the v2 rewrite (explicit "answer directly" escape hatch) fixed that (false-search 0.0) yet **stacking guided-v2 with markdown formatting hurt** (a6 composite 0.852 < either alone — anti-synergy, runs `2026071*-ablate-a6-*`). The prompt therefore stays shipped; guided-v2 is the documented prompt-only runner-up (`harness/configs.py`).

### RQ4 — provider → **Brave (recommended default)**

Brave beat Tavily at the same config in screen (0.90/0.90 vs 0.75/0.80; `20260710-232202`, `20260711-000529`) with ~25% fewer prompt tokens (raw snippets are shorter than Tavily's content chunks), and the Tavily variant of the a3 combo lost by 0.11 composite (a5 vs a3, ablate runs). Tavily remains fully supported (BYOK user choice).

### RQ5 — search→read loop → **read_url stays available; limits & turn cap unchanged; snippets carry the load**

Models read pages rarely under every config (avg reads ≤ 0.12/question) and snippet-only answering matched or beat read-enabled configs (a4 = 1.000 on ministral). Disabling read_url costs engagement on qwen3-1.7b (0.86 vs 0.93) and it's a shipped product feature, so it stays available. Content limits 2400/9600 and turn caps 3/8: within noise of shipped 4800/5 (screen readlim*/turns* runs). The turn budget is not the binding constraint — winners average 1.7–1.9 turns.

### RQ6 — model ranking (<8B, frozen config, dataset v1)

| rank | model | fresh ✓ [CI90] | stable ✓ | engage | false-search | notes |
|---|---|---|---|---|---|---|
| 1= | huihui-qwen35-2b | 0.977 [0.90,0.99] | 0.97 | 1.00 | 0.20 | ceiling-level at 2B |
| 1= | qwen35-4b | 0.977 [0.90,0.99] | 1.00 | 1.00 | 0.00 | **recommended ship** |
| 1= | ministral-3-3b | 0.977 [0.90,0.99] | 0.97 | 1.00 | 0.00 | **recommended ship** |
| 4 | gemma-4-e2b | 0.932 [0.84,0.97] | 1.00 | 1.00 | 0.07 | |
| 5 | lfm25-1.2b | 0.909 [0.81,0.96] | 0.97 | 0.95 | 0.20 | best ≤1.5B |
| 6 | qwen3-06b | 0.886 [0.78,0.94] | 0.90 | 0.98 | 0.33 | smallest viable |
| 7= | qwen3-1.7b | 0.841 [0.73,0.91] | 0.97 | 0.93 | 0.00 | |
| 7= | mlabonne-qwen3-4b | 0.841 [0.73,0.91] | 0.97 | 0.91 | 0.07 | |
| — | *ceiling: gemma-4-31B Q8* | 0.977 | 1.00 | 1.00 | 0.00 | context row |
| — | *ceiling: qwen3.6-27B Q8* | 0.955 | 0.97 | 0.98 | 0.00 | context row |

**Capability-gate failures** (0 tool calls executed; fresh ≈ 0): gemma-3-1b-q4, gemma-3-4b, phi-4-mini, smollm3-3b, hermes-3-3b. Three modes, from transcripts (`20260711-1951*/2002*/2007*-confirm-*`): (a) **format mismatch** — gemma-3 wants to search and emits Gemma-style ` ```tool_code ` blocks the OpenAI-format parser can't map: fixable app-side with a format shim or template; (b) **capability denial** — phi-4-mini answers "I can't perform web searches"; (c) **silent hallucination** — hermes-3-3b fabricates answers with plausible fake citations (the worst UX: confidently wrong).

Runs: `20260711-19*/20*/22*-confirm-frozen-*`. Rank 1= models are undecided among themselves at n=44 (identical scores); all dominate ranks 5+ (non-overlapping CIs vs rank 6 down).

### RQ7 — baselines

**Floor** (no tools): fresh 0.023 on all four models measured (`20260711-0858/0955-ablate-floor-*`, `20260710-2246/2347-screen-floor-*`) — retrieval is provably the mechanism; one guessable question flagged (fr-news-03, journal 2026-07-11). Stable floor 0.83–0.97 confirms the stable split is memory-answerable. **Ceiling**: large local models through the same harness score 0.955–0.977 fresh — i.e., **the dataset's practical ceiling is ~0.98, and three sub-4B models reach it**. Amendment #2 replaced the original frontier-cloud ceiling with local models (no cloud key; reproducible).

## Frozen configuration

See `frozen-config/` (machine-readable: `config.json`, `tool_web_search.json`, `tool_read_url.json`, `system_prompt.txt`) and `PROVENANCE.md` for the per-value run-id table, including anti-recommendations (JSON formatting; result_count 8 without raising the menu ceiling; stacking guided-v2 prompt with markdown formatting).

## Judge validation

- Manual: control agent blind-graded a stratified 40-item sample (`analysis/judge-validation-sample.json`, seed 7): **38/40 (95%) agreement**; both disagreements traced to a judge-prompt bug (acceptable answers omitted), fixed in v2 and all runs re-judged — config ordering unchanged (journal 2026-07-11).
- Judge-vs-judge: gemini-3.5-flash vs local qwen3.6-27b on 14 screen runs: 92.1% raw, ~3.5% substantive (18/31 disagreements were the local judge's own parse failures).
- Limitation: the manual labels are the control agent's, not independent human labels.

## Limitations & not tested

- **Providers**: Exa and Parallel not tested (no keys; Parallel gated in-app). Brave-vs-Tavily measured on small models only; the gap may differ for larger models.
- **Environment**: quality measured on workstation llama.cpp with phone-class Q4 GGUFs; on-device latency/thermals/memory not measured — turn and token counts are the cost proxies. On-device confirmation is the natural follow-up.
- **Dataset**: 44 fresh questions, single time window (2026-05..07), EN-only, single-fact short answers; multi-hop and non-English behavior untested. Fresh questions go stale — see refresh + re-anchoring protocol (`datasets/README.md`).
- **Sampling**: one generation per question (temp 0.7, seed 42); rank-1 ties unresolved at this n.
- **Judge**: remote (OpenRouter) — benchmark reruns need a key; local fallback documented.
- Live-web capture: model-generated queries differ across configs, so the replay cache pins repeats rather than guaranteeing identical evidence across arms; captures span 2026-07-10..12.

## Reproducing

`README.md` — quick start, re-run sweep, add a model, refresh dataset, regenerate tables (`harness/aggregate.py` + `harness/leaderboard.py`).
