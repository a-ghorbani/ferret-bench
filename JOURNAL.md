# Journal — 2026-07-10-web-search-agentic-config

Append-only. Decisions, findings, surprises, dead ends.

## 2026-07-10 — Session start / FRAME

- Scaffolded repo, git init (embedded repo inside rd-team; rd-team gitignores evaluation/experiments/).
- Verified environment: llama-swap at localhost:8080 serves 45 model ids incl. Qwen3-1.7B/4B, Gemma-3 1B/4B, Gemma-4-E2B, Ministral-3-3B, Phi-4-mini, SmolLM3-3B, LFM2.5-1.2B, and large models usable as judge/ceiling candidates (Qwen3.6-27B-Q8, Gemma-4-31B-Q8).
- BRAVE_API_KEY / TAVILY_API_KEY are NOT in the shell env; they live in `~/Dev/rd-team/.env`. Harness will load from a `.env` path (gitignored); manifests name providers only.
- Drafted `context/topics/web-search.md` in rd-team (didn't exist; FRAME output per skill).
- Spawned Explore subagent to extract the exact PR#808 talent contract (tool schemas, system prompt, result formatting, truncation, turn caps) from ~/Dev/pocketpal-ai — harness must be a faithful replica, and PocketPal's shipped values are the natural default config for screening.
- Wrote PROTOCOL.md v1 with RQ1–RQ7. Key design choices: record-replay HTTP cache for comparability + API budget; freshness-split dataset to prove mechanism engagement (contamination control); floor=no-tool, ceiling=frontier-through-same-harness.

## 2026-07-10 — Contract extracted (PR #808)

- Subagent extracted the full talent/loop contract from `origin/feature/TASK-20260625-1135` in ~/Dev/pocketpal-ai → pinned verbatim in `harness/CONTRACT.md`. Notable: PR #808 is on the feature branch, not local main.
- Shipped values now known and set as the default config: result_count 5 (1–8), snippet 280 chars, search-menu ceiling 1000 tok, read_url 4800 chars via r.jina.ai, max_turns 5 with forced no-tools final, dated grounding system line (budget=4 wording), nonce'd UNTRUSTED WEB CONTENT wrapper on every tool result, labeled plain-text result blocks, Tavily default provider.
- Surprise worth testing: `budgetHits`' 1000-token ceiling silently drops trailing hits — result_count>5 may be a no-op without raising the ceiling. Logged as confound in factors.md; harness will log hits-actually-included.
- Providers in app: tavily (default), brave, exa, parallel(gated). We have keys for brave+tavily → RQ4 scope stays brave-vs-tavily; exa/parallel noted as not-tested.

## 2026-07-10 — Harness built + smoke-tested (PROTOCOL phase)

- Wrote harness/: common.py (budget/text replicas), http_cache.py (record-replay, key-stripped), providers.py (tavily/brave/jina), talents.py (web_search/read_url replicas + format variants), configs.py (factor knobs, prompt/tool-desc variants), agent_loop.py (AgentRunner replica incl. forced-final nudge), llm.py (llama-swap client, warm-up retries, serial), run_eval.py, judge.py (Qwen3.6-27B judge, v1-simpleqa-3way), aggregate.py (Wilson 90% CIs → analysis/scores.jsonl).
- Smoke run 20260710-203213-smoke-shipped-qwen3-1.7b: 3/3 questions, fresh Q searched (Tavily live→cache), no_search Q didn't, message shapes match contract, no API-key fragments in cache/ or runs/ (grep scan).
- Protocol amendments #2–#4 logged (local ceiling, local judge, anchor_date-as-today).
- GitHub: private repo a-ghorbani/ferret-bench created, pushed.

## 2026-07-10 — Dataset v1 + SCREEN launched

- Dataset v1 assembled: 89 questions (44 fresh web-verified by 3 curator subagents with source URLs, 30 stable, 15 no_search); sha256 d3502755…; screening slice = 35 stratified (20 fresh: 7e/9m/4h across beats, 8 stable incl. 2 gotchas, 7 no_search).
- Dropped 1 duplicate between curator beats (Eurovision winner appeared in news + entertainment; kept fr-news-02).
- Judge pipeline validated on smoke run (Canberra → CORRECT with sane reason).
- Dev-model probe (shipped config): gemma-3-4b NEVER calls tools (0 searches on fresh Q, instant answer) — early capability-gate signal, noted for CONFIRM. qwen35-4b and ministral-3-3b both search properly. Dev models for SCREEN: qwen3-1.7b + ministral-3-3b (family diversity: Qwen + Mistral).
- SCREEN sweep launched in background: 19 configs (shipped, floor, 17 OFAT variants) × 2 models × 35 Qs, then judge + aggregate. Log: analysis/screen-sweep.log.

## 2026-07-11 — Judge switch + SCREEN analysis + ABLATE launch

- User directed switch to a fast remote judge (proposed x-ai/grok-4.5 on OpenRouter). grok-4.5 is region-blocked by xAI (403). Selected google/gemini-3.5-flash (1.2 s/call vs 16 s remote qwen3.6-27b); amendment #5. All 38 screen runs re-judged in 184 s with 8 parallel workers.
- Judge agreement gemini-3.5-flash vs local qwen3.6-27b on 14 preserved runs: 361/392 = 92.1%. 18/31 disagreements are local-judge PARSE_FAILs (27B emitted unparseable grading output; gemini did not) → substantive disagreement ≈ 3.5%. Gemini judge adopted; 27B judgments kept as judgments-qwen27b.jsonl.
- SCREEN results (35-Q slice, qwen3-1.7b + ministral-3-3b, all runs in analysis/scores.jsonl):
  - Floor (no tools): fresh 0.00 (qwen) / 0.05 (ministral) — retrieval is provably required; dataset contamination controlled. The 1 floor-correct fresh item is fr-news-03 (Starmer resignation — guessable via incumbency); flagged for v2 refresh, kept in v1 (hash pinned, effect symmetric across configs).
  - Stable floor: 0.88/1.00 — stable split is memory-answerable as designed.
  - WINNERS (consistent on both models): td-enriched (fresh 0.95/1.00 vs shipped 0.75/0.80 — largest effect); prov-brave (0.90/0.90, ~25% fewer prompt tokens than tavily); sp-guided (0.90/0.95 but false-search 0.29 on both → guided-v2 written with explicit no-search escape hatch); read-off ≥ shipped on both with lowest tokens (read_url not earning its keep); sp-dateonly ≥ shipped on both (shipped grounding line adds little for these models).
  - ELIMINATED (dominated: ≤ shipped on both or worse on one + more expensive): fmt-json (0.75/0.85 vs cost), fmt-compact (0.70/0.80), rc8 (0.70/0.80 + more tokens), snip-full (0.75/0.75, +50% tokens), turns8 (mixed, no gain). Kept for possible later use: rc3 (cheaper, ~neutral), snip140 (mixed), turns3 (~neutral, cheaper), readlim* (~neutral — reads are rare), fmt-markdown (0.75/0.95 — model-dependent, carried into ablate).
  - Tool-call validity 1.00 across every screen config on both dev models — these two families have no syntax problem; the gate will matter for others in CONFIRM.
- ABLATE launched on FULL dataset (89 Qs), 8 configs × 2 models: shipped + floor anchors; a1 td+brave; a2 +markdown; a3 +guided-v2; a4 +read-off; a5 td+guided-v2 (tavily control); a6 full combo. Log: analysis/ablate-sweep.log.

## 2026-07-11 — ABLATE results (full 89-Q dataset, both dev models; 0 failures)

- Composite fresh (mean of both models): a2 td+brave+markdown 0.921; a3 td+brave+guided2 0.909; a4 td+brave+readoff 0.909; shipped 0.875; a6 full-combo 0.852; a1 td+brave 0.830; a5 td+guided2(tavily) 0.795; floor 0.023.
- Per model: ministral a4=1.000 [0.94,1.00], shipped/a2/a3=0.977; qwen3-1.7b a2=0.864 best, a3=0.841, shipped=0.773.
- guided-v2 fixed the false-search problem: 0.0 on every ablate config (screen guided-v1 was 0.29); shipped shows 0.067.
- INTERACTION: markdown + guided-v2 together (a6) UNDERPERFORMS either alone on both models — do not stack; choose one.
- read_url: disabling it (a4) is best-or-tied on ministral but drops qwen engagement to 0.86; product-wise PocketPal ships read_url, and a2/a3 (reads available) match a4 — keep read_url available in the frozen config.
- a2 vs a3 statistically tied → tiebreak criterion: search-ENGAGEMENT on weak models (the observed failure mode of small/weak models is never searching — cf. gemma-3-4b probe). Tiebreak sweep launched: a2/a3/shipped × qwen3-06b + gemma-4-e2b, full dataset.
- Note: a1 (td+brave, snippets unchanged) < a2 on both models and < shipped on qwen — the screening td-enriched effect partially came through interaction with formatting/other levels; OFAT screen estimates were noisy at n=20. Full-dataset ablate is authoritative.

## 2026-07-11 — TIEBREAK + FREEZE + CONFIRM launch

- Tiebreak (a2 vs a3 vs shipped on weak models, full dataset): gemma-4-e2b a2=0.932 > a3=0.864 > shipped=0.841; qwen3-06b a3=0.886 ≈ a2=0.864 (within CI), both >> shipped 0.568 (engagement 0.77→0.95+). Composite over all 4 tested models: a2 0.909 vs a3 0.892 → **frozen config = a2** (enriched tool descriptions + brave + markdown formatting; all other params shipped defaults retained).
- Caveat logged: a2 false-search on qwen3-06b 0.33 vs a3 0.20 (tiny models sometimes search for creative asks under a2); accepted — correctness on real questions weighs more than an occasional wasted search, and at 1.7B+ a2 false-search is 0.
- frozen-config/ written: config.json (hash 2e5a7826…), tool_web_search.json, tool_read_url.json, system_prompt.txt (shipped grounding retained), PROVENANCE.md (per-value run-id table + anti-recommendations). guided-v2 documented as prompt-only runner-up.
- CONFIRM sweep launched THROUGH the packaged harness (sweep.py --configs frozen --models-file models-confirm.txt): 13 <8B models + 2 large local ceiling refs, full dataset v1.
- Floor for confirm models skipped (logged reason): floor≈0.02 established on 4 models spanning 0.6B–3.3B; per-model floors would double GPU time for no decision value.

## 2026-07-11 — Judge manual validation → v2 prompt + full re-judge

- Manual validation (protocol §Metrics): control agent blind-graded a stratified 40-item sample (20 CORRECT / 12 INCORRECT / 8 NOT_ATTEMPTED as judged; sample pinned in analysis/judge-validation-sample.json, seed 7). Agreement with gemini v1 judge: 38/40 = 95%.
- Both disagreements were the same root cause: JUDGE BUG — v1 prompt omitted the dataset's acceptable_answers (e.g. "Wolfram" marked INCORRECT vs gold "Tungsten"). Fixed: v2-simpleqa-3way-acceptable includes the acceptable list; judge_run now joins acceptable_answers from the manifest-pinned dataset.
- All 61 pre-confirm runs re-judged with v2 (482 s, parallel). ORDERING UNCHANGED: a2 wins gemma-4-e2b 0.932 / qwen3-1.7b 0.886; a3 leads qwen3-06b 0.909 vs a2 0.886; ministral top group unchanged. 4-model composite: a2 0.920 vs a3 0.898 → freeze (a2) CONFIRMED on v2 numbers.
- Borderline judging notes (logged for transparency): st-07-type answers with wrong side details but correct key fact; graded per rubric key-fact rule.
- TODO when confirm sweep ends: its in-process judging uses v1 (module loaded pre-fix) → re-judge confirm runs with v2 --overwrite, re-aggregate, then regenerate leaderboard.

## 2026-07-11 — Confirm wall-time diagnosis (user asked)

- 13 ranked small models: ~57 min total. Ceiling refs dominate: qwen3.6-27b-Q8 took 7,496 s alone (reasoning model, 604 completion tok/question = 5× ministral, at 27B Q8 decode speed); gemma-4-31b-Q8 pacing ~95 s/question. ~80% of sweep wall time = the 2 ceiling rows. No harness pathology (0 failures, avg 1.75 turns, no retries/timeouts in log).
- Action: split models-ceiling.txt out of models-confirm.txt — ceilings are once-per-dataset-version context rows, not part of the per-model-addition rerun path. README wording already matches (sweep re-run = models-confirm.txt).

## 2026-07-12 — CONFIRM results + report + review launched

- Confirm sweep: 15/15 runs, 0 failures. Re-judged with v2 (172 s). Leaderboard (analysis/leaderboard.md):
  - Rank 1= (0.977 fresh): huihui-qwen35-2b, qwen35-4b, ministral-3-3b — equal to gemma-4-31B ceiling (0.977), above qwen3.6-27B (0.955). Then gemma-4-e2b 0.932, lfm25-1.2b 0.909, qwen3-06b 0.886, qwen3-1.7b/mlabonne-qwen3-4b 0.841.
  - Capability-gate failures (0 tool calls, fresh≈0): gemma-3-1b/4b, phi-4-mini, smollm3-3b, hermes-3-3b. Modes: gemma-3 emits ```tool_code``` blocks (format mismatch — app-side shim could fix); phi-4-mini denies having tools; hermes-3-3b hallucinates with fake citations.
- report.md written: all RQ1–7 answered with run ids; limitations include ceiling-effect caveat, single-seed, EN-only.
- Secret scan: full history (2,918 blobs), grep-based key patterns (brave/tavily/openrouter/gh/etc.): 0 hits. gitleaks unavailable on box; pattern scan logged as the method.
- Adversarial review: fresh-context subagent launched, repo-only access, brief = invalidate conclusions; findings will be resolved in this journal before COMPLETE.

## 2026-07-12 — Floor verification + COMPLETE

- Floorfix runs (0 failures): huihui-qwen35-2b floor fresh 0/44, qwen35-4b floor fresh 0/44 (runs 20260712-083638/085121) — stronger than the pre-written 1/44 claim; report corrected to 0.000. Rank-1 results are retrieval, not memory. Review finding #5 fully closed.
- Final aggregate + leaderboards regenerated. Setting phase=COMPLETE; checklist evidence in this entry's sibling (final reply) and below.
- Completion Checklist:
  - [x] Every RQ answered in report.md (RQ1–7, with evidence tiers)
  - [x] Every numeric claim cites run ids present in runs/ (regenerated from v2 scores.jsonl post-review)
  - [x] frozen-config/ populated with per-value provenance (bundle-tier framing)
  - [x] Confirmation sweep executed through the packaged harness (sweep.py, runs 20260711-19*..22*-confirm-*)
  - [x] README: re-run sweep / add model / refresh dataset / regen report — all documented
  - [x] Adversarial review ran pre-COMPLETE; 11/11 findings accepted & addressed (journal 2026-07-12)
  - [x] Amendment log complete (#1–#8)
  - [x] analysis/ machine-readable (scores.jsonl); report regenerable
  - [x] Limitations & not-tested present (incl. saturation, bundle-vs-factor, judge independence)
  - [x] Repo committed; history shows phase transitions and amendments
  - [x] Pushed to private GitHub (a-ghorbani/ferret-bench); full-history secret scan clean (2,918 blobs, 0 hits; public flip remains user decision)

## 2026-07-12 (post-COMPLETE addendum) — RQ6 gate-failure root cause, from the PocketPal implementer's handoff + our own template probe

The PocketPal implementer (PR #808) traced the gemma-3 gate failure into llama.cpp and asked us to confirm two things from our traces. We did, and the answer **revises RQ6's failure-mode taxonomy**. Recorded here rather than silently editing the frozen report; report.md carries a matching addendum.

**Their mechanism (accepted).** PocketPal parses no tool calls itself — llama.cpp does, and it selects a parser via a differential autoparser gated on `jinja_caps.supports_tool_calls`, computed by probe-rendering the model's chat template to see whether it ever reads `tools[]` / `tool_calls`. A template that ignores `tools` ⇒ caps false ⇒ llama.cpp builds a **content-only parser** ⇒ `tool_calls` is structurally always empty. The old generic polyfill that used to let any model tool-call via injected schema + constrained grammar has been removed upstream, so there is no safety net.

**Their key insight (accepted, and it kills the shim idea):** if the template ignores `tools`, **the tool schemas are never rendered into the prompt at all**. The model only knows the tools exist because PocketPal's grounding system line *names* them. So it has been told the names and never shown a signature — which is exactly why gemma improvises Gemma-native ```tool_code```. An app-side tool_code text-parser would therefore NOT fix it: the model would still be guessing the call signature. Any fix must do both halves (schema into the prompt + syntax parsed out). Their fix — supply a tool-declaring gemma-3 Jinja template as `chat_template` on the completion params, which llama.rn already forwards to native — does both, because the autoparser is differential (any consistent syntax works) and caps-true then buys a real PEG parser + lazy constrained grammar.

**Our confirmation, from run traces (`runs/*confirm-frozen-*`, n=89 each):**

| model | tool_calls emitted | responses containing a ```tool_code``` fence |
|---|---|---|
| gemma-3-4b | **0** | **64 / 89** |
| gemma-3-1b-q4 | **0** | 5 / 89 |
| phi-4-mini | 0 | 0 |
| hermes-3-3b | 0 | 0 |
| smollm3-3b | 0 | 0 |

Confirms (a): gemma models want to search, emit a fence, and llama.cpp returns zero tool calls. Sharper still — gemma-3-1b guesses the **wrong function name** (`search_web("earthquakes 24 June 2026")` vs the real `web_search`), which is direct evidence the model never saw a schema; it is pattern-matching a plausible name, not calling a declared tool.

**Our confirmation of (b) — the decisive one — by reading the chat template out of each GGUF** (the same thing llama.cpp's caps probe does; `tokenizer.chat_template` via gguf-py):

| model | template length | `tools` refs | `tool_calls` refs | ⇒ caps | class |
|---|---|---|---|---|---|
| gemma-3-4b | 1532 | **0** | 0 | false | **structural** |
| gemma-3-1b | 1532 | **0** | 0 | false | **structural** |
| hermes-3-3b | **291** (bare ChatML) | **0** | 0 | false | **structural** |
| phi-4-mini | 423 | 3 | 0 | true | compliance |
| smollm3-3b | 5340 | 15 | 0 | true | compliance |

**This revises their "fixes 2 of 5" to 3 of 5, and revises our own RQ6 taxonomy.** The `hermes-3-3b` GGUF we (and PocketPal) load — NousResearch `Hermes-3-Llama-3.2-3B.Q4_K_M` — ships a **bare ChatML template with zero `tools` references**, even though upstream Hermes-3 is marketed as a tool-calling model. So hermes is **structurally blocked, not non-compliant**: it was never shown a schema and has no way to emit a parseable call. That reframes our RQ6 failure mode (c): hermes' "silent hallucination with plausible fake citations" is not a badly-behaved model choosing to lie — it is a structurally muzzled model failing *unsafely* (unlike gemma, which fails *visibly* by improvising a fence). The template-override fix should therefore cover hermes-3-3b too.

**Genuinely compliance-class (template declares tools, schema IS rendered, model still won't call):** phi-4-mini (denies the capability outright) and smollm3-3b. These need a different lever — the implementer notes `tool_choice` is never set on PocketPal's local path (only the remote OpenAI path), so nothing nudges a local model toward `required`.

**Caveat on this addendum:** the caps mapping is inferred from the GGUF-embedded template, which is what llama.cpp uses by default and what these runs used; a build that substitutes a bundled template for a known architecture could differ. The empirical trace column (0 tool_calls for all five) is consistent with the inference in every case.

**Their correction to our result_count/ceiling finding (accepted, and now moot):** the ceiling under-count was real but the mechanism differed from our "raising count past ~5 is a no-op" phrasing — the budget was charged against a differently-rendered string than the model received, making the drop marginal and input-dependent rather than a flat no-op. Verified against their branch: `budgetHits` now charges the ceiling against the same `formatHit` renderer used to build the menu (`origin/feature/TASK-20260625-1135`, eab95f6b "fix(search): charge the result token ceiling against the rendered menu", 2026-07-12). They also landed e257258c (markdown menu) and 668e81d7 (enriched tool descriptions) the same day — i.e. the frozen-config bundle is adopted upstream. Our RQ1 recommendation (don't raise result_count without raising the ceiling) stands; the stated reason is corrected here.

## 2026-07-12 — Dataset v2 assembled + v2 sweep launched

- 3 curator agents delivered 54 tiered fresh items (T2s with empirical snippet-absence checks; conflicting-source candidates rejected and logged in curator notes). 1 cross-beat duplicate removed (SpaceX IPO price) → v2 = 98 questions: fresh 53 (T1 20 / T2 12 / T3 9 / T4 12), stable 30, no_search 15 (carried from v1). sha256 e7544608…, anchor 2026-07-12.
- Known reuse: a handful of T1 facts also appeared in v1 (WWDC, SpaceX, Nvidia, PSG, Knicks…) — harmless (model weights unaffected by v1), noted for variety in v3.
- v2 sweep chain launched: floor2 (qwen35-4b + ministral no-tool contamination check) then confirm2 (12 official + 2 variants + 2 frontier anchors via OpenRouter × 98 Qs, frozen config). Tier validation is post-hoc from telemetry (searches/reads/turns per question): any T3/T4 item broadly solved with a single search gets flagged for demotion.
- Watcher fixed to an anchored pgrep pattern (python3 sweep[.]py) so it can't match itself (root cause of the 4 zombie shells the user spotted).
