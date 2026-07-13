# Experiment Protocol — Agentic web-search configuration & model ranking for small on-device LLMs

- **Slug**: 2026-07-10-web-search-agentic-config
- **Domain**: web-search (`context/topics/web-search.md` in rd-team)
- **Status**: see STATE.md — this file holds the protocol, not the live state
- **Protocol version**: v1 (bump on every amendment; see §Amendment Log)

## Frame

PocketPal shipped model-driven internet search (PR #808): `web_search` + `read_url` talents (BYOK) driven by an OpenAI tool-calling ReAct loop (assistant `tool_calls` → execute → `role:tool` → repeat, capped turns). We want to ship the best possible search experience and share the findings. Two goals: (1) the best agentic web-search **configuration** for small on-device LLMs, and (2) a re-runnable **benchmark** that ranks small (<8B) on-device-class models at agentic web search.

### Research questions

1. **RQ1 (result count)** — How many `web_search` results should be returned to a small model? Where is the coverage-vs-context-burn sweet spot?
2. **RQ2 (result formatting)** — What tool-result formatting (JSON vs markdown vs compact text; which fields; snippet length) yields the best answers from small models?
3. **RQ3 (prompting)** — Do system-prompt and tool-description variants materially change behavior (search-when-needed, sensible queries, read-after-search) for small models, and which variant wins?
4. **RQ4 (provider)** — Brave vs Tavily: at the same config, which provider yields better end-answer quality for small models? Does Tavily's LLM-ready content close the gap that snippets leave?
5. **RQ5 (search→read loop)** — Does enabling/encouraging `read_url` improve answer quality over snippet-only answering for small models, and what turn cap / content-truncation limit is right?
6. **RQ6 (model ranking)** — Under the frozen config, how do small (<8B) on-device-class models rank at agentic web search? Which models fail the tool-calling capability gate outright (itself a reportable result)?
7. **RQ7 (baselines)** — How much does the search loop improve over the no-tool floor (parametric memory only), and how close does the best small model get to a frontier-cloud ceiling on the same task?

### Environment & constraints

- **Execution tier**: DGX workstation running llama.cpp via llama-swap (OpenAI-compatible, `http://localhost:8080`). GGUF quants matching what phones run (Q4_K_M class) — this is a *quality* proxy for on-device; latency numbers are workstation-only and reported as turn/token counts, not wall-clock.
- **Serial model access**: llama-swap loads models on demand on a single GPU. Never issue concurrent requests to two different model ids; warm each model with retries and generous timeouts before its batch.
- **Search APIs**: `BRAVE_API_KEY` / `TAVILY_API_KEY` from `~/Dev/rd-team/.env` (never committed; manifests reference providers by name). `r.jina.ai` keyless reader for page fetch.
- **Nondeterminism pinning**: a record-replay cache for all external HTTP (search + page fetch); repeated queries replay identically, but model-generated queries differ across configs/models, so novel queries capture live (capture-on-miss) — comparability is approximate, not exact (see report Limitations). Cache keys strip API keys at capture time.
- **Loop contract**: mirrors PocketPal's talent/loop semantics (extracted from `~/Dev/pocketpal-ai`, PR #808) so frozen values transfer directly.

### Claims to test

- Small models are context-poor: fewer, denser results beat many raw results → RQ1, RQ2.
- Tavily's agent-oriented output helps small models more than it helps large ones → RQ4.
- `read_url` helps only if content is aggressively truncated; otherwise small models drown → RQ5.
- Several popular small models cannot reliably emit tool calls at mobile quants → RQ6.
- The loop mechanism (not parametric memory) is what answers fresh questions → RQ7 / contamination control.

## Factors

See `factors.md` for the full table. Summary of controlled factors and their frozen values (filled as screening/ablation freezes them):

| Factor | Levels tested | Frozen value | Frozen at (run/journal ref) |
| ------ | ------------- | ------------ | --------------------------- |

## Dataset

- **Source**: curated three-split set, generated + hand-curated (curation protocol in `datasets/README.md`), SimpleQA-style short-answer format:
  - `fresh` (~40): answers post-date small-model training cutoffs (events/facts from 2026-05..07) — retrieval required by construction; each pinned with gold answer + source URLs.
  - `stable` (~30): timeless facts (SimpleQA-style) — measures whether the search loop *hurts* questions memory could answer, and feeds the floor comparison.
  - `no_search` (~15): questions where searching is wrong/unnecessary (chit-chat, arithmetic, creative) — measures false-positive tool firing.
- **Version/hash**: `datasets/v<N>/questions.jsonl` pinned by sha256 in every manifest; `anchor_date` recorded per version.
- **Fitness check**: categories mirror phone-user asks (news, sports, prices/releases, local-ish facts, how-to); short-answer gold keeps judging tractable.
- **Contamination assessment**: split tags are the control; the no-tool floor run quantifies memory answering per question — a `fresh` question the floor answers correctly gets demoted/flagged.
- **Nondeterminism pinning**: record-replay HTTP cache for all provider/reader calls (capture-on-miss, keys stripped); the grounding line's `today` uses the dataset `anchor_date`, not wall clock (deliberate harness deviation for replay consistency); generation seed pinned.

## Metrics

| Metric | Type | How measured | Primary? |
| ------ | ---- | ------------ | -------- |
| Answer correctness | semantic | LLM judge vs gold answer, graded correct/partial/incorrect | **yes** |
| Groundedness | semantic | judge: is answer supported by fetched evidence | secondary |
| Tool-call validity rate | mechanical | parse + schema check of every tool_call | gate |
| Search engagement rate | mechanical | did ≥1 web_search fire on fresh questions | control |
| Loop completion rate | mechanical | final answer within turn cap | secondary |
| Turns & tokens to answer | mechanical | loop telemetry | cost axis |

- **Judge config**: `ggml-org/Qwen3.6-27B-GGUF:Q8_0` (local, ~7× larger than the class under test), temperature 0, SimpleQA-style 3-way grading (CORRECT / INCORRECT / NOT_ATTEMPTED) against gold answer; prompt versioned in `harness/judge.py` and every manifest. Validated against a control-agent manual re-label of a stratified 40-sample before results are trusted; absence of independent human labels goes in Limitations.

## Baselines

- **Floor**: same models, no tools ("answer from what you know") — quantifies parametric-memory contamination per question.
- **Ceiling**: largest local models (Qwen3.6-27B Q8 / Gemma-4-31B Q8) through the *same* harness and frozen config — amended from "frontier cloud" (no cloud LLM key guaranteed; local is reproducible and free; still far above the <8B class under test). See Amendment #2.

## Experiment design

- **Screening (SCREEN)**: OFAT from a sensible default config, small dataset slice (~30–40 Qs), 2 dev models (one ~1.7B, one ~4B class). Eliminate dominated levels.
- **Ablation (ABLATE)**: surviving levels + interactions (e.g. count×formatting, provider×read_url) on the fuller slice.
- **Confirmation (CONFIRM)**: frozen config × full model sweep through the packaged harness. Model list: PocketPal-relevant small models available on llama-swap (Qwen3 1.7B/4B, Gemma-3 1B/4B, Gemma-4 E2B, Ministral 3B, Phi-4-mini, SmolLM3 3B, LFM2.5 1.2B, …) + capability gate + ceiling reference.
- **Sample sizes & seeds**: min n = full dataset slice per cell; generation temperature per PocketPal defaults; seed pinned where the server honors it; judge at temperature 0.

## Stopping rules

- **Elimination**: a config level is dropped when its correctness score is clearly dominated (non-overlapping 90% bootstrap CIs on the slice) or it fails a mechanical gate (validity, completion).
- **Undecided**: comparisons undecided at slice-n go to ABLATE with more n; if still undecided at budget cap, report undecided and freeze the cheaper option.
- **Budget caps**: search APIs are metered — replay cache mandatory after first capture; cap ~2,000 live Brave/Tavily calls total. LLM runs are local/free but serial — cap the confirmation sweep at ~12 models.
- **Pause (BLOCKED)**: missing user-only input → STATE.md phase=BLOCKED with the exact need.

## Deliverables

1. **`frozen-config/`** — optimized parameters (system prompt, tool descriptions, result count, formatting rules, provider recommendation, loop caps) as machine-readable files, each value annotated with justifying run ids — directly consumable by pocketpal-dev-team.
2. **Ongoing benchmark harness** — `harness/` + README: one command re-runs the sweep; adding a model = one manifest entry; results append to `analysis/` (cumulative leaderboard).
3. **Dataset curation protocol** — fresh questions go stale: refresh script + versioning + re-anchoring rule (scores across dataset versions are not comparable until reference models re-run).

## Completion Checklist

phase=COMPLETE may be set only when every item passes, printed with evidence:

- [ ] Every RQ in §Frame answered in report.md, or marked unanswerable with reason
- [ ] Every numeric claim in report.md cites a run id present in `runs/`
- [ ] `frozen-config/` populated; every frozen value cites the runs that justified it
- [ ] Confirmation sweep was executed through the packaged harness (not ad-hoc scripts)
- [ ] README lets a stranger re-run the sweep, add a model, refresh the dataset, and regenerate the report from `analysis/`
- [ ] Adversarial review (fresh-context reviewer, repo-only) ran before COMPLETE; every finding accepted-and-addressed or rebutted with a logged reason in JOURNAL.md
- [ ] Amendment log reflects every protocol change made during the run
- [ ] analysis/ contains machine-readable scores; report.md regenerable from it
- [ ] Limitations & not-tested section present
- [ ] Repo committed; git history shows phase transitions and amendments
- [ ] Pushed to the private GitHub remote; full-history secret scan clean (public flip remains a user decision)

## Amendment Log

Append-only. An unlogged protocol change invalidates the run.

| # | Date | Change | Rationale | Solo / user-approved |
| --- | ------ | ---------------- | --------- | ---------------------------- |
| 1 | 2026-07-10 | Initial protocol | — | solo (goal-run) |
| 2 | 2026-07-10 | Ceiling baseline = large local models (Qwen3.6-27B/Gemma-4-31B) via same harness, not frontier cloud | No cloud LLM key guaranteed in env; local ceiling is reproducible, free, and still ~7× the size class under test | solo |
| 3 | 2026-07-10 | Judge = local Qwen3.6-27B-Q8, temp 0, 3-way SimpleQA-style grading; validated vs control-agent manual labels (n=40) | Same rationale as #2; agreement stats reported; no independent human labels → Limitations | solo |
| 4 | 2026-07-10 | Harness grounding line uses dataset anchor_date as "today", not wall clock | Replayed search captures come from the capture window; a wall-clock date would contradict the evidence the model sees | solo |
| 5 | 2026-07-11 | Judge = remote via OpenRouter (temp 0, same v1-simpleqa-3way prompt), parallel calls. User proposed x-ai/grok-4.5 → region-blocked by xAI (HTTP 403); selected google/gemini-3.5-flash (1.2 s/call vs 16 s for remote qwen3.6-27b). Local Qwen3.6-27B kept as fallback; its 14 fully-judged screen runs preserved as judgments-qwen27b.jsonl for judge-vs-judge agreement | 27B judge serializes on the single GPU and was the wall-clock bottleneck; remote judge parallelizes freely. Agreement vs the local judge + manual-label validation both reported before results are trusted | user-approved (grok substitution: solo, region constraint) |
| 6 | 2026-07-11 | Judge prompt v1 → v2-simpleqa-3way-acceptable (acceptable_answers included in the grading prompt); ALL runs re-judged with v2 and analysis regenerated | Manual validation (38/40) found v1 marked acceptable alternates INCORRECT (e.g. Wolfram vs Tungsten). Config ordering unchanged post-re-judge. Logged here per adversarial review finding #8a (was journal-only) | solo |
| 7 | 2026-07-12 | Groundedness (secondary metric in §Metrics) formally dropped, not implemented | Judge grades against gold only and never sees fetched evidence; correct-but-ungrounded answers are invisible to scoring. Floor baselines bound the parametric-memory path; residual risk documented in report Limitations. Per adversarial review finding #8b | solo |
| 8 | 2026-07-12 | Freeze tiebreak criterion: pre-declared criterion was weak-model ENGAGEMENT; the freeze decision used weak-model composite correctness (a2 0.909 vs a3 0.898 over 4 models, v2: 0.920 vs 0.898) | Engagement saturated near 1.0 for both candidates on the tiebreak models, so it could not discriminate; correctness subsumes it. Same winner under either criterion. Logged per adversarial review finding #4 (post-hoc criterion change must be visible) | solo |
| 9 | 2026-07-12 | V2 cycle opened (post-COMPLETE follow-up for pocketpal.dev publication): dataset v2 with difficulty tiers T1 single-search / T2 read-required / T3 multi-source / T4 multi-hop, tier labels behaviorally validated (an item any reference model solves below its tier's demand is demoted); per-tier scoring added to analysis | v1 saturates at the top (report Limitations); tiers restore discrimination and honest public claims | user-approved |
| 10 | 2026-07-12 | Ceiling = frontier models via OpenRouter through the same harness (reverses #2 now that an OpenRouter key is confirmed available); local 27B/31B ceiling rows retired (kept in analysis/ as historical v1 rows) | User: local large models are "too random" as a reference; frontier anchors calibrate the leaderboard against the real quality bound. Note: judge model (gemini-3.5-flash) is excluded from anchor duty to avoid self-grading | user-approved |
| 12 | 2026-07-12 | **Quantization is a FACTOR, not a constant.** factors.md claimed "Q4_K_M — held constant"; it was false (qwen3-1.7b Q6_K, huihui-qwen35-2b Q8_0, mlabonne-qwen3-4b Q4_K_S). Manifests never pinned the weights despite the protocol requiring it. Now: `run_eval.resolve_weights()` records gguf path + quant + size in every manifest; `quant` is emitted per row and shown on the leaderboard | User caught it. An uncontrolled Q8_0-vs-Q4_K_M difference sat underneath a published "abliterated beats official" comparison. A score without its weights is not a result | user-raised, solo |
| 13 | 2026-07-12 | **Thinking (reasoning) is a FACTOR, and the primary board runs with it OFF for every model** (`enable_thinking=false` via chat_template_kwargs). A `frozen-thinking-on` arm quantifies the cost/benefit on thinking-capable models | User's call, and correct on two grounds. (a) SCIENCE: thinking was an accident of model choice — Qwen models reasoned, others could not, and an abliterated variant "won" partly because abliteration suppresses thinking. Not apples-to-apples. (b) PRODUCT: agentic search already floods the context with results; a thinking budget on top is latency, battery and context pressure exactly where a phone has none. Measured: identical trivial answer cost 140 tokens thinking-on vs 2 thinking-off | user-raised, solo |
| 14 | 2026-07-12 | Harness bug fixed: the loop read only `content` and discarded answers that thinking models delivered inside `reasoning_content`, scoring them NOT_ATTEMPTED. Fallback added + `answer_from_reasoning` / `empty_content_turns` canaries. All affected runs quarantined and re-run | Under-scored exactly the thinking models (qwen35-2b 17.3% blank finals, mlabonne 12.2%, qwen3-1.7b 7.1%) and inverted the abliterated-vs-official comparison. Also a live PocketPal bug — escalated | solo |
| 15 | 2026-07-13 | **Community variants are dropped from the published board.** They are ablations, not leaderboard entries: results go in report.md, not in a ranked row. `huihui-qwen35-2b` retained in `runs/` (ablation complete: abliteration effect = zero). `mlabonne-qwen3-4b` dropped outright | User asked what value the variant rows add. Answer: none, and one was harmful. mlabonne VIOLATED amendment #11's own rule — its official sibling (Qwen3-4B) is not on the board, so the row compared against nothing while implying a verdict on Qwen3-4B we never measured (same defamation pattern as the gate-failure rows). huihui's comparison was real but is now ANSWERED (38/53 = 38/53); an answered question needs a sentence, not a permanent row inviting people to ship an abliterated model | user-raised, solo |
| 16 | 2026-07-13 | **"Retained shipped default" is abolished as a valid outcome.** Every frozen value must be DERIVED under the current regime. Agreement with PocketPal's shipped value is a *result*, not a starting point, and must be stated as "we tested X and shipped-value won" with the runs that show it. A value we did not test is a value we do not own | User: "why does PocketPal ship something we have not tested? If they need their own research, why do we exist?" Correct, and worse than it looked: `PROVENANCE.md` used the phrase "retained shipped default" 8 times — each one reads like a decision but is the *absence* of one. A benchmark that inherits its defaults from the thing it is meant to advise is not a source of truth; it is a mirror | user-raised, solo |
| 17 | 2026-07-13 | **The entire frozen config is re-validated under the clean regime** (thinking off, dataset v2, discarded-answer bug fixed): OFAT over tool_desc, provider, result_format, result_count, snippet_chars, read_url_policy, max_turns, system_prompt × 3 models (top / fallback / weakest). Runs tagged `revalidate` + `prompt3` | The config was tuned when **half the dev-model evidence base was contaminated**: screening, ablation AND tiebreak each used 1 thinking-capable model of 2, whose answers were being silently deleted 7–17% of the time with thinking uncontrolled. Every config decision therefore rests on partly-broken data — not just the system prompt. Re-deriving all of it is the only defensible response | user-raised, solo |
| 11 | 2026-07-12 | Roster policy: official checkpoints only; community variants (huihui abliterated 2B, mlabonne 4B) demoted to explicitly-labeled comparison rows, only kept where an official sibling exists for contrast | User directive: stay with originals unless a variant is measured better — which is itself a reportable finding, not a silent substitution | user-approved |
