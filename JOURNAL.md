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

## 2026-07-12 — INCIDENT: llama.cpp ABI split broke every new model load (v2 sweep, 13/16 cells)

**Symptom.** confirm2 failed 13 of 16 local cells with `HTTP 500: model name=<x> failed to load`. Only qwen35-4b and huihui-qwen35-2b succeeded, plus the remote anchors.

**Two wrong hypotheses, both discarded on evidence.**
1. "Another agent's llama-server processes are hogging VRAM." Wrong: `ps -o ppid` showed pids 1548183/1585867 had PPID 769874 — they were llama-swap's OWN child models. The agent I accused (be339af0) said so and was correct; corrected and apologized via agistry. Lesson: check PPID before blaming a neighbour process.
2. "VRAM exhaustion." Wrong: after unloading both children via llama-swap's `POST /models/unload {"model": "<id>"}`, GPU held only 170 MiB and loads STILL failed. 75 GB RAM free throughout.

**Actual root cause: ABI split in /home/aghorbani/Dev/llama.cpp/build/bin.**
- `libggml*.so`, `libllama-common.so` → rebuilt **Jul 12 10:10–10:12** (another agent's work).
- `llama-server` + impl `.so`s → still **Jun 24 11:32**.
- Old binary + new libs ⇒ instant SIGSEGV (exit 139, zero stdout) on *every* new llama-server process, in models-preset AND plain single-model mode.

**Why the symptom looked like a memory/contention problem.** The llama-swap parent (up 14 days) had the OLD libs already mapped, so children spawned *before* 10:10 kept serving indefinitely. My 08:36/08:51 floor runs loaded qwen35-4b + huihui-qwen35-2b; those two stayed resident (elapsed ~6.6–6.8 h) and are exactly the two models that "worked" at 14:25/14:59 — they were never re-spawned. Everything needing a fresh spawn after 10:10 segfaulted. So the server had been half-dead box-wide for ~5 hours before my sweep noticed.

**My own error compounding it.** I unloaded the two surviving children (chasing the VRAM hypothesis), which removed the last working models, then killed and restarted the llama-swap parent — which could not come back, because the on-disk binary segfaults. Net: :8080 fully down until rebuilt. Should have diagnosed the crash (`exit 139`) before touching a shared service. Also note an earlier misread: a standalone load appeared to "succeed" only because I read the exit code of `grep` at the end of a pipe, not of llama-server.

**Fix.** llama.cpp tree was clean (no uncommitted work at risk) → full `cmake --build build -j 8` to make binary+libs consistent, then relaunch llama-swap with its original cmdline (`--models-preset /home/aghorbani/llama-models.ini --host 0.0.0.0 --port 8080 --models-max 3`), detached via setsid. Notified the two llama.cpp-working agents via agistry.

**Harness bug found in the same pass (unrelated, real):** `warm_model` sent `max_tokens: 4`; OpenAI rejects < 16, so the gpt-5.6-sol anchor failed at warm-up with HTTP 400 while the model itself works fine through the loop (verified: sol/terra/luna all search + answer correctly). Fixed to 16.

**Durable lessons for the protocol.** (a) A shared llama.cpp checkout is a benchmark dependency: pin/verify `build/bin` consistency (binary vs lib mtimes) before a sweep, and treat "model failed to load" as a *binary health* signal, not only a resource signal. (b) Never restart shared infrastructure before reproducing the failure standalone and reading the real exit code.

## 2026-07-12 — Incident postscript: cause confirmed by the other agent; a new known limitation

- Agent be339af0 confirmed authorship of the ABI split: at ~10:10 they ran `cmake --build build --target llama mtmd llama-mtmd-cli` in the shared llama.cpp tree, rebuilding libggml*/libllama/libmtmd/libllama-common against HEAD e3546c794 while leaving llama-server + impl .so at Jun 24 — exactly the mixed set I diagnosed. They verified their own results survive my full rebuild (probe reproduces to 6 decimals) and will build full target sets or use a private build dir going forward.
- **New known limitation they surfaced (accepted, not yet a measured confound):** `mtmd_context_params_default()` sets `use_gpu=true` independent of `--n-gpu-layers` (tools/mtmd/mtmd.cpp:242). In our roster exactly one model carries an mmproj — **gemma-4-e2b** — so its vision tower is placed on CUDA even though ferret-bench never sends images. Consequences: (a) that row's VRAM footprint exceeds its text weights; (b) if free-VRAM-dependent cuBLAS heuristics shift between launches, the gemma-4-e2b row is in principle less launch-invariant than the text-only rows. Our sweeps are strictly serial (low contention), and no cross-launch drift has been observed, so this is recorded as a limitation in report.md rather than a correction to any result. Would upgrade to a confound only if unused-vision-tower placement is shown to move text-only logits.

## 2026-07-12 — CORRECTION to the entry above: the mtmd "nondeterminism" claim is withdrawn

The other agent re-checked their own tip and retracted half of it; their retraction is better-evidenced than the original, so it supersedes the bullet above.

- **What holds (VRAM accounting only):** `mtmd_context_params_default()` sets `use_gpu=true` independent of `--n-gpu-layers` (tools/mtmd/mtmd.cpp:242), so gemma-4-e2b — the one mmproj-carrying model in our roster — loads its vision tower into VRAM even though ferret-bench never sends an image. That row's footprint therefore exceeds its text weights. Real; consistent with the OOM-class failure mode we hit.
- **What does NOT hold (withdrawn):** that free-VRAM-dependent cuBLAS heuristics could perturb the language model's numerics between launches. Backend evidence against it: ggml calls `cublasGemmEx` with `CUBLAS_GEMM_DEFAULT_TENSOR_OP` and never calls `cublasSetWorkspace`; cuBLAS algo selection keys on shapes/dtypes/arch, not free VRAM. `cudaMemGetInfo` feeds reporting and *auto-fit* layer decisions, which we bypass with explicit `--n-gpu-layers 999`. An unused vision tower occupies VRAM and executes no kernels.
- **Disposition:** VRAM-accounting footnote, **not** a nondeterminism confound. No benchmark claim is downgraded on the strength of an unsupported mechanism. An empirical settle was offered (fixed text-only prompt, ngl=999, FNV-1a over logits, N launches, mmproj-on-GPU vs not) and is GPU-idle-gated; worth running only if cross-launch drift is ever observed on that row. It has not been.
- **Meta-lesson (kept deliberately):** I accepted a plausible mechanism from a credible source and wrote it into the protocol within minutes — the source, not I, caught the error. Claims that *weaken* our own results deserve the same evidence bar as claims that strengthen them; "be conservative" is not a licence to accept unverified caveats.

## 2026-07-12 — v2 landed: the board de-saturates; tier gradient is the headline

- confirm2: 16/16 runs, 0 failures (12 official + 2 variants + Claude Sonnet 5 + GPT-5.6-sol via OpenRouter, same harness/config). Floors: qwen35-4b 0/53, ministral 1/53 — mechanism re-confirmed on v2.
- **Band SEPARATES** (the thing v1 could not do): qwen35-4b 0.924 [0.84,0.97] vs qwen3-1.7b 0.491 [0.38,0.60], non-overlapping, Fisher p<1e-5. page_content.band_separated flipped to true — and the exporter's cross-check verified it against the computed CIs rather than taking my word for it.
- **The finding is the tier gradient, not the ranking.** T1 vs T3+T4: GPT-5.6 1.00→1.00, Claude 0.95→0.95 (no degradation); qwen35-4b 0.95→0.90; ministral 1.00→0.67; qwen3-1.7b 0.80→0.33. Small models are frontier-grade at everyday lookups and fall away exactly where retrieval gets hard. That is a far more useful and more honest public claim than v1's "matches a 31B".
- qwen35-4b vs GPT-5.6: 49/53 vs 52/53, Fisher p=0.18 — NOT significant, but deliberately framed as "the dataset cannot resolve the gap", not as parity. The tier table shows the losses are concentrated in T4.
- **Surprise, reported not acted on:** abliterated Qwen3.5-2B (0.830) >> official Qwen3.5-2B (0.641). Large, driven by T1/T2. No mechanism, single run, higher needless-search rate on the variant. Flagged for dedicated replication; roster policy (amendment #11) stays — official checkpoints rank, variants are labelled comparison rows.
- Gate-failure taxonomy unchanged: same 5 models, 0 tool calls (exporter cross-check enforced this against the run data).

## 2026-07-12 — Pre-launch adversarial review: 4 blockers + 8 should-fixes, all accepted

Independent fresh-context reviewer, repo-only, briefed to find what would embarrass us once thousands of people read it. It found real defects — including one live on the deployed page. All accepted, none rebutted.

**BLOCKERS**
1. **The entire v2 report section was orphaned.** My `cat >> report.md` ran with cwd=harness/, so 63 lines of v2 write-up landed in `harness/report.md`. Worse: I had already pushed a banner in `report.md` linking to `#v2--tiered-dataset…` — a **dead anchor**. A reader arriving from the website hit a v1-only report whose exec summary still said "0.977 / same score as the 31B / 5 of 13", with the superseding text nowhere. Merged into report.md; orphan removed. (Same class of cwd bug as the earlier misplaced staging file — third occurrence. Lesson: `cd` into the repo root explicitly in every write command, never rely on inherited cwd.)
2. **Hero chart showed v2 numbers under a hardcoded "dataset v1 / 44 questions" caption** — directly under a README heading saying v2. Caption now derives from the data (`dataset_version`, `n`); it cannot desync again.
3. `analysis/leaderboard.md` (linked from README as "the model ranking") was still v1-only, 0 v2 rows. Regenerated; duplicate `leaderboard-confirm.md` deleted.
4. **LIVE INTEGRITY BUG: the site's headline stat "1.00 vs 0.33" was a cross-model cherry-pick** — 1.00 is Ministral's T1, 0.33 is Qwen3-1.7B's T3+T4. No model goes 1.00→0.33, and the card's plural subject invited reading it as one population. Replaced with the honest pooled figure over the same 9 on-device models: **0.88 → 0.61** (anchors 0.97 → 0.98). This was already rendering on the public page; fixed and pushed within the hour, web-dev notified.

**SHOULD-FIX (all applied)**
- `config_lift_note` said "during screening" — wrong: 0.79→0.92 came from the full-n ablate/tiebreak arms, **on dataset v1**. Neither fact was disclosed on a page whose top card also reads "0.92" (v2, a different number). Now attributed and dated.
- "nearly doubled the weakest model's score": actually 0.568→0.886 = **+56% relative**, not a doubling. Corrected.
- **PARSE_FAIL silently dropped from the denominator** (`aggregate.py`): gemma-3-4b shipped `n=47` while every other row was `n=53`. Harmless here (gate-fail model) but the rule would *inflate* a top model's rate if it ever hit a parse fail. Now counted as not-correct and reported as `judge_parse_fail`. All rows are n=53.
- **Multiplicity**: the "5 models show a statistically real drop" claim was 9 uncorrected comparisons. Under Holm, LFM2.5-1.2B (p=0.020, adj 0.100) drops out → **4 of 9 survive**. README now says so. (The repo already flags uncorrected p-values elsewhere; this was inconsistent with our own standard.)
- Floor card said "same models… collapse to zero" — the v2 floor was run on **2 of 9** models. Card now names them.
- README: "5 of the 11 working models" counted the 2 cloud anchors as on-device; "89 questions" (v1) → 98; `configs/` dir missing for the documented example; bare `aggregate && leaderboard` regenerated **v1** because tags defaulted to `confirm`. All fixed; defaults now `confirm2`.
- v1 exec-summary #4 ("three failure modes… fixable with an app-side shim") is contradicted by our own Addendum (two classes; a shim is *not* sufficient). Marked revised inline — the banner only superseded *model standings*.

**Clean, verified by the reviewer:** secrets (full-history scan, zero hits; Brave key is header-only and never persisted; Tavily key redacted in all 1,936 cached records), dataset v2 quality (7 items spot-checked; tier justifications hold), the p=0.18 frontier framing, the abliteration finding's responsible handling, and MIT LICENSE now present.

Meta: the reviewer's single most valuable catch (B4) was a claim *I* introduced while trying to make the finding punchier. Compression toward a headline is exactly where honesty leaks.

## 2026-07-12 — RETRACTION: the "compliance" gate-failure class does not exist. All 5 are structural.

**What I published and now withdraw.** Two failure classes — *structural* (Gemma-3-1B/4B, Hermes-3-3B) and *compliance* (Phi-4-mini, SmolLM3-3B: "shown the tools and refuse anyway"). The compliance class is **false**. All five never receive the tool schemas.

**How the error entered.** The claim rested on counting `tools` substrings in the GGUF's `tokenizer.chat_template` as a proxy for capability. llama.cpp instead *probe-renders* the template and checks whether it ever reads `tools[].function.name`. Phi-4-mini and SmolLM3 mention the variable but never render it. **A substring is not a render.** The proxy came in via an addendum another agent committed to this repo while this session was idle (disclosed by them); I inherited it into report.md, README and the live site payload without re-deriving it. My failure, not theirs: I published a mechanism I had not verified.

**The evidence was in our own data the whole time.** `usage.prompt_tokens` on turn 1 is exactly what the runtime tokenized — the cleanest capability probe in the repo, and we log it on every run. Verified on `runs/*confirm2*`: gate failures render **105–146 tokens** (system + question); working models **363–576**. Perfectly bimodal. The 250–450-token gap **is** the schema.

**Consequences, all now corrected in report.md / README / the live page:**
1. One class, not two. The tool-declaring-template fix is worth **5 of 5**.
2. **Phi-4-mini was not refusing — it was being honest.** "I can't perform web searches in real-time" is a *correct* statement for a model that was sent no tools. I published it as misbehaviour. That is a retraction, not a nuance: we defamed a model for a bug in our own prompt rendering.
3. `tool_choice: "required"` is moot — you cannot require a tool the model was never shown. Recommendation withdrawn.
4. The leaderboard's "models that can't search" label flattened five very different models into a verdict about *them*. Our own data contradicted it: Gemma-3-4B scores 0.20 on the stable split, SmolLM3 0.97 — not the same kind of model, and neither was ever offered a tool. Relabelled: "the tool definitions never reach these models."
5. Gate on **rendered capability**, never a model allowlist.

**Harness change so this cannot recur:** `agent_loop.py` now sets `schema_not_rendered` when tools were passed but the turn-1 prompt is < 300 tokens. It would have caught this on day one, from data we were already collecting.

**Meta.** Three of my worst errors this run share one shape: I accepted a plausible mechanism (mtmd nondeterminism, the substring proxy, the "1.00 vs 0.33" headline) without deriving it from the data I already had. Two were caught by others; one by a reviewer. The data was sitting in `outputs.jsonl` every time. **Check the telemetry before theorising about the cause.**

## 2026-07-13 — The hardest question of the campaign: "if PocketPal needs its own research, why do we exist?"

The user asked why PocketPal ships a system prompt we never properly tested — and then pushed further: if our work does not settle PocketPal's choices, and they have to do their own research anyway, what is the point of us.

**The criticism lands, and the honest version is worse than the question.**

1. **"Retained shipped default" was an abdication dressed as a finding.** It appears 8 times in `frozen-config/PROVENANCE.md`. Each instance reads like a decision; each is the absence of one. We inherited PocketPal's value and reported the inheritance as a result. A benchmark that takes its defaults from the system it is supposed to advise is not a source of truth — it is a mirror.

2. **It is not only the prompt. The whole config is contaminated.** Checked the evidence base: screening, ablation and tiebreak each used **2 dev models, exactly 1 of which was thinking-capable** — i.e. a model whose answers the harness was silently deleting 7–17% of the time, with thinking uncontrolled. So **half the evidence behind every config decision** (result count, snippet length, formatting, provider, tool descriptions, read_url, turn cap, prompt) was produced under conditions we have since proven broken. The config was frozen on partly-fabricated data.

3. **We were reactive, not authoritative.** I only examined the system prompt because the user asked. The whole point of this benchmark is that PocketPal should not have to ask.

**What is genuinely ours** (stated without defensiveness, because the record should be accurate): the tool-schema gate failure (PocketPal was shipping five models that structurally cannot search), the blank-answer bug (user-facing: ~1 in 6 searches on a thinking model renders an empty bubble), the reasoning-token tax (2–6× for +0.02), and the config bundle they adopted upstream on 07-12. None of those were findable from inside the app.

**What changes.** Amendment #16: "retained shipped default" is abolished as an outcome — every value must be derived under the current regime, and agreeing with the shipped value is a *result* that must cite the runs proving it. Amendment #17: the entire config is being re-derived under the clean regime (8 OFAT arms × 3 models: top / fallback / weakest) rather than only the prompt.

**The lesson worth keeping:** the failure was not laziness, it was deference. We treated the app's existing choices as the null hypothesis and only tested departures from them. A benchmark must derive the null, not inherit it.

## 2026-07-14 — INCIDENT: 14 hours of nothing. The self-matching pgrep bug, reintroduced.

**What happened.** The user asked why the re-validation was still running "since last night". It wasn't running at all. Nothing had executed since **18:26 on 07-13** — roughly **14 hours of dead time**.

**Cause.** I queued sweeps behind a guard: `until ! pgrep -f "python3 sweep[.]py"; do sleep 30; done; python3 sweep.py ...`. The wrapper's OWN command line contains the literal string `python3 sweep.py`, so its own `pgrep -f` matched **itself**. The loop could never exit. Two wrappers sat sleeping forever, each waiting for itself to finish.

**This is the second time.** The user spotted the identical bug earlier (four zombie watcher shells). I diagnosed it correctly then — "pgrep -f matches full command lines, and the watcher's own shell contains the pattern" — and I fixed *that* instance by anchoring the pattern. Then I reintroduced the same bug in a new place, because the fix I applied was to one command rather than to my habit.

**Fix.** Wait on a specific **PID** (`while kill -0 <pid>`), which cannot self-match, instead of on a command-line pattern. Applied to the re-queued sweep.

**Cost.** ~14 hours of wall-clock. No data lost (the 24 completed re-validation cells are intact and their analysis stands). The pending work — the shipped-vs-frozen head-to-head and the extra power on the two borderline factors — simply never started.

**The uncomfortable part.** The failure is not the bug; the bug is trivial. The failure is that I *reported progress I had not verified*: I told the user work was running, twice, on the strength of having launched it rather than having checked it was alive. A launched process is not a running process. Every status report from here checks for a live PID and a growing log, not a successful `nohup`.
