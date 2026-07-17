# Methodology audit — ferret-bench / web-search agentic config

Reviewer pass 2026-07-15. Repo-only, evidence-cited. Severity = how much it moves the published conclusions, not how hard it is to fix.

Bottom line: the engineering is careful and the self-corrections are honest, but the **study design cannot answer the questions it is being used to answer.** The central v2/v3 finding (a "retrieval-difficulty gradient") rests on a difficulty axis that is empirically not monotone, and the whole board is a single noisy draw graded by an un-anchored LLM judge. At least 5 of these flaws change conclusions, not just presentation.

---

## CRITICAL — changes the published conclusions

### C1. The tier "difficulty" axis is not monotone — the headline gradient is an artifact of tier composition
The central v2/v3 claim is "small models are frontier-grade on easy lookups and degrade on hard retrieval (T1→T4)." But per-tier correctness reconstructed from `runs/*confirm3*` shows **T4 (nominally hardest) beats T2 for most models**, and even beats T3:

| model | T1 | T2 | T3 | T4 |
|---|---|---|---|---|
| qwen35-2b | 18/20 | 7/12 | **4/9** | **9/12** |
| qwen35-4b | 19/20 | 9/12 | 8/9 | 11/12 |
| ministral-3-3b | 20/20 | 9/12 | 6/9 | 8/12 |
| lfm25-1.2b | 18/20 | 5/12 | 5/9 | 7/12 |
| **hermes-3-3b (0 tool calls — never searches)** | 1/20 | 0/12 | **3/9** | 0/12 |

T2 (fact only in page body — specific numbers like attendance "80,824", "$91B forecast") is consistently the *hardest* tier; T4 ("multi-hop") is often *easier* because the second hop lands on globally famous entities the model already knows (fr2-tech-15 → Elon Musk; fr2-news-17 → Erdogan; fr2-tech-16 → ESA; fr2-sport-17 → Germany). Once retrieval supplies hop 1, hop 2 is free parametric recall. That a **no-tool model (hermes) scores 3/9 on T3** proves those items are memory-answerable, not retrieval-hard. The tiers are labelled by *structural description*, never calibrated to *empirical difficulty*, so "T1→T4 gradient" measures topic/entity-fame composition, not retrieval difficulty. This is the user-flagged anomaly, and it is systemic.
**Fix:** Calibrate difficulty empirically, not by description. Order tiers by observed solve-rate of a fixed reference panel, and require each "hard" item to be (a) not floor-answerable by *any* roster model and (b) unsolved by a single search. Report per-item, not just per-tier. Report T4 second-hop-entity familiarity as a covariate. Until then, drop the "gradient" framing.

### C2. Temperature 0.7 + one generation per question = the whole leaderboard is a single noisy draw
`harness/configs.py:31`: `temperature 0.7, seed 42`, single sample per question (`report.md:88`). Generation is *stochastic*, yet every rate, every CI, every `p<0.001` is computed from one draw. The Wilson/Fisher CIs (`aggregate.py:23`) model only *between-question* binomial variance and completely ignore *within-question generation* variance — the dominant noise source at temp 0.7 on 9–20-item cells. Re-running the same model would move rows. "Seed pinned" is not reproducibility: llama.cpp continuous batching does not honor seed deterministically, and per-question query drift (see C-list below) breaks it further.
**Fix:** Either grade at temperature 0 (matched to the judge), or run k≥5 samples/question and report mean ± generation-variance-inclusive CIs (or a mixed-effects model with question and seed as random effects). Every significance claim needs re-derivation under this.

### C3. Cloud anchors reason; local models are forced not to — the ceiling comparison is rigged
`harness/llm.py:75-77`: `enable_thinking` is sent to llama.cpp only; "remote models manage their own reasoning." So the primary board runs GPT-5.6/Claude in native reasoning-ON mode against local models pinned reasoning-OFF. The report's own RQ8 table shows OFF costs Qwen3.5-4B **0.887 vs 0.924 ON**. So the flagship claims ("the gap has narrowed to the point the dataset can't resolve it," "frontier-grade") compare a deliberately-weakened local model to a full-strength cloud model. Amendment #13's stated justification — "the only way to compare thinking-capable and non-thinking models honestly" — is exactly what's violated at the most consequential comparison.
**Fix:** Publish two boards: (a) product board, everything thinking-off including anchors where controllable; (b) capability board, every model in its best mode. Never mix modes within one ranking. At minimum, footnote every anchor comparison with "local OFF vs cloud ON."

### C4. No human ground truth — LLM judge validated only by another LLM, gold answers LLM-authored
The judge is `gemini-3.5-flash`. Its "manual validation" labels are from `control-agent (Claude Fable 5)` (`analysis/judge-validation-manual-labels.json` → `"labeler": "control-agent (Claude Fable 5)"`). The "60/60 CORRECT-precision" check is normalized substring matching — circular. The gold answers themselves are LLM-curated for *future* (2026) events (`datasets/README.md` rule 7: "curation is agent-driven"), verified by an agent, never a human. A single wrong gold silently penalizes *correct* models and no human ever looked. The whole accuracy stack is LLM-grades-LLM.
**Fix:** Human-label a stratified ≥100-item sample (blind, two annotators, report κ) before any accuracy number is trusted; human-verify every fresh gold against primary sources; treat judge agreement vs *humans* (not vs another agent) as the acceptance gate.

### C5. Wrong significance test — unpaired Fisher on paired same-question data
Every model-vs-model and config-vs-config test is one-sided Fisher exact on correct-counts (`report.md:16`). But both arms answer the *same* questions — this is paired data. Fisher (unpaired) discards the pairing, mis-estimates variance, and is the wrong test; McNemar (on discordant pairs) is correct and usually more powerful. Every reported `p` is from the wrong model.
**Fix:** McNemar for paired comparisons; bootstrap over questions for CIs; Holm/BH across the family of tests actually run (not just the 4 currently corrected).

---

## MAJOR — materially weakens interpretation

### M1. Per-cell n is 9–20; the gradient rests on pooling low-n cells
T3=9, T2=12, T4=12 (`datasets/v2/meta.json`, tier counts). One flipped question = 8–11 points. The report concedes wide per-tier CIs but then leans on T3/T4 anyway (and pools T3+T4 to get a number). Combined with C1, per-tier claims are uninterpretable.
**Fix:** ≥30 items/tier after empirical calibration, or report only the pooled easy-vs-hard contrast with generation-variance-inclusive CIs and stop naming individual tiers.

### M2. Garden of forking paths — the design changed continuously under the results
v1→v2→v3; judge model swapped (#5); judge prompt swapped and everything re-judged (#6); ceiling swapped local→cloud (#10); tiebreak criterion changed *post-hoc* from engagement to correctness (#8); groundedness dropped (#7); the entire frozen config re-derived after declaring "half the evidence base contaminated" (#16-17). 17 amendments, ≥3 public retractions, 192 run dirs. Each change is individually defensible and honestly logged — but collectively this is researcher-degrees-of-freedom with the outcome visible at each fork. Screening p-values are uncorrected ("hypothesis-generating only") yet the surviving bundle they selected *is* the shipped recommendation.
**Fix:** Freeze dataset + judge + metrics + tests *before* looking at model results; pre-register the tier definitions and the primary comparison; run confirmation once on the frozen design. Everything to date is exploratory and should be labelled as such.

### M3. The shipped bundle contains two components that are individually noise
v4 OFAT (`report.md:324-338`): provider +0.157 (p=0.004, real); tool_desc +0.027 (p=0.475); result_format +0.019 (p=0.633). Two of the three "changes" are indistinguishable from noise, yet all three ship as "the bundle." The "super-additive / compounds not stacks" claim (0.384 bundle vs ~0.28 summed) is asserted from point estimates with **no interaction test** — at n=159 with these CIs, super-additivity is not established.
**Fix:** Test the interaction directly (2^k factorial or at least bundle-minus-provider vs shipped). If only provider is real, say the finding is "switch the provider," not "ship this 3-part bundle."

### M4. "Everything else doesn't matter" is an underpowered null sold as a positive result
`report.md:356`: result count, snippet length, read_url, turn cap all "genuinely do not matter" — from n=20 screens and n=159 OFAT with p=0.32–1.00. That is *absence of evidence*, not evidence of absence, and it's marketed to implementers as "where not to spend effort." A real no-effect claim needs a powered equivalence test with a pre-stated margin.
**Fix:** Reframe as "not resolved at this n" or run TOST equivalence tests with a declared negligibility margin before claiming no effect.

### M5. The replay cache does not hold evidence constant across models/configs
`PROTOCOL.md:27`, `factors.md:41`: model-generated queries differ, so cache is capture-on-miss spanning 2026-07-10..12; novel queries hit live/fresher web. So two models (or two configs) are graded on **different search results**, and a model that happens to phrase a luckier/fresher query scores higher for reasons unrelated to reasoning. This confounds every comparison and breaks the reproducibility the protocol claims.
**Fix:** Freeze a fixed corpus per question (retrieve-once, snapshot the top-k pages, serve that identical evidence to every model/config), or at minimum log per-run capture timestamps and quarantine any comparison where the evidence sets differ.

### M6. Contamination/floor is established on 2 hand-picked models, not the roster
Floor is measured only on qwen35-4b and ministral (`report.md:174`), both of which *refuse* without tools (0/0/0/0). But other models *guess* — hermes gets 3/9 on T3 with no tools. "The board measures retrieval, not memory" is therefore proven for the two models least prone to guessing, not for the ranking as a whole, and not per-tier. v1's 3 known memory-answerable fresh items were kept ("effect symmetric across configs") — but memory-answerability is **not** symmetric across models of different parametric strength; it inflates the better-memorized models in the *ranking*.
**Fix:** Run the no-tool floor for *every* ranked model, per tier; drop or quarantine any item any model floor-solves; report the ranking on the retrieval-necessary residual.

### M7. External validity — the dataset is the easy case
`report.md:353`: 91% of fresh questions embed their own date and are fully-specified single facts. Real phone queries are undated, ambiguous, underspecified ("who won the election?"). The benchmark structurally cannot measure the date's value (self-caught) — but the deeper problem is that fully-specified dated single-facts are the *easiest* slice of real usage, so the board overstates small-model capability on what users actually type.
**Fix:** Make undated/ambiguous/multi-intent phrasing a first-class split (v3 starts this with 20 undated — extend it), and report the dated-vs-undated gap as a headline, not a footnote.

---

## MODERATE — soundness, artefacts, reproducibility

### D1. Judge is blind to evidence (groundedness dropped, #7) → a fabricated-but-matching or lucky-from-memory answer scores CORRECT, bounded only by the 2-model floor (see M6). At minimum, spot-check groundedness on a sample.

### D2. Saturated anchors. GPT-5.6-sol and Claude-Sonnet-5 score byte-identically on every tier (both 0.981, 20/20, 21/21). The anchors don't separate either — using a ceiling the dataset can't resolve to claim "the gap narrowed" is uninformative. Add a mid-tier anchor (e.g. an 8–14B) that the dataset *can* separate.

### D3. Reproducibility theater. Protocol advertises pinned seed / deterministic replay, but temp 0.7 + continuous batching + capture-on-miss means a clean re-run will not reproduce the numbers. State this honestly at the top, not only in Limitations.

### D4. Tiny mechanical splits carry headline claims. no_search=15 (false-search rate), unanswerable=13 (v3 fabrication headline). A 13-item denominator cannot support "fabrication does not track accuracy" as a general claim.

### D5. Process/artefact hygiene undermines trust that artefacts match claims. JOURNAL documents an orphaned v2 report section (cwd bug, "third occurrence"), a **live public site shipping a cross-model cherry-pick "1.00→0.33"**, 14h lost to a re-introduced pgrep bug, and "reported progress I had not verified." 192 run dirs with no manifest-level index. None are science errors per se, but they are exactly the "patch-of-work / whack-a-mole" texture you flagged, and they raise the prior that a published number and its artefact have drifted. Add an integrity check that regenerates every report number from `analysis/scores.jsonl` in CI and fails on drift (the report claims regenerability — enforce it).

---

## What is genuinely solid (keep)
- The tool-schema capability-gate finding (5 models never receive schemas; the canary in `agent_loop.py:89`) — real, mechanistic, and upstream-actionable.
- The discarded-answer bug (`reasoning_content` fallback) — a real user-facing PocketPal bug found from the data.
- The reasoning-token-tax result (2–6× tokens for ≈+0.02) — directionally robust even under C2, because the token cost is large and deterministic.
- The honest retraction discipline. The problem isn't dishonesty; it's that the design keeps generating things to retract.

## Suggested triage order
1. Rebuild the difficulty axis empirically (C1, M1) — without this, v2/v3's headline is unsupported.
2. Add generation-variance sampling + temp-0 grading (C2), switch to McNemar (C5) — re-derive every significance claim.
3. Human-anchor the judge and golds (C4).
4. Fix the anchor thinking asymmetry (C3).
5. Freeze the design and re-run confirmation once (M2), then treat all prior numbers as exploratory.
