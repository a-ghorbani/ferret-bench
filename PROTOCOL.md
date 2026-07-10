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
- **Nondeterminism pinning**: a record-replay cache for all external HTTP (search + page fetch) so that config comparisons see identical web state; cache keys strip API keys at capture time.
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

- **Source**: TBD in PROTOCOL phase — candidates: SimpleQA subset (contamination risk: high for pre-cutoff facts), FreshQA-style fresh questions (require retrieval by construction), plus a generated set of time-anchored questions. Decision + generator script land in `datasets/`.
- **Version/hash**: TBD
- **Fitness check**: questions must resemble what phone users actually ask (news, facts, how-to, local-ish lookups) and must *require* retrieval for a meaningful fraction (freshness split) so the mechanism is provably engaged.
- **Contamination assessment**: every question tagged `pre-cutoff` (answerable from memory) or `post-cutoff/fresh` (requires search); the floor baseline (RQ7) quantifies memory answering directly.
- **Nondeterminism pinning**: record-replay HTTP cache, dataset pinned by content hash.

## Metrics

| Metric | Type | How measured | Primary? |
| ------ | ---- | ------------ | -------- |
| Answer correctness | semantic | LLM judge vs gold answer, graded correct/partial/incorrect | **yes** |
| Groundedness | semantic | judge: is answer supported by fetched evidence | secondary |
| Tool-call validity rate | mechanical | parse + schema check of every tool_call | gate |
| Search engagement rate | mechanical | did ≥1 web_search fire on fresh questions | control |
| Loop completion rate | mechanical | final answer within turn cap | secondary |
| Turns & tokens to answer | mechanical | loop telemetry | cost axis |

- **Judge config**: TBD in PROTOCOL phase (candidate: a strong local model or cloud API; frozen prompt version in every manifest; spot-validated against a human-labeled sample before results are trusted).

## Baselines

- **Floor**: same models, no tools ("answer from what you know") — quantifies parametric-memory contamination per question.
- **Ceiling**: a frontier cloud model run through the *same* harness and config — the achievable quality bound for the task itself.

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
