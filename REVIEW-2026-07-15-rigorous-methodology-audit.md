# Rigorous methodology audit and recovery plan

Date: 2026-07-15  
Scope: `ferret-bench`, including protocol, datasets v1-v3, harness, run artefacts, analysis, public payload, and the actual PocketPal/llama.rn delivery chain.  
Disposition: independent re-audit. The earlier `REVIEW-2026-07-15-methodology-audit.md` is useful but incomplete.

Second-pass revision: rechecked 2026-07-15 against confirm4 traces and the intended PocketPal feature branch. This revision corrects the earlier `main`-branch assumption, adds pooled path-compliance counts, reconstructs the date contrast, quantifies dataset clustering with an explicitly limited proxy, and narrows the schema-canary recommendation.

## Executive verdict

This work is an **exploratory engineering campaign**, not a confirmatory benchmark. It found several valuable implementation defects, but the published research claims are not decision-grade.

The central problem is not untidy prose. The study repeatedly assigns a label to a construct without measuring the construct:

- T2 is called “read-required,” but the top model answers 28/31 T2 items correctly with zero reads.
- T4 is called harder than T1-T3, but Qwen3.5-4B scores 100% on T3 and T4 while scoring about 91% on T1 and 90% on T2 in v3.
- “Just telling it the date” is presented as an isolated treatment, but the compared prompts differ in date **and all search/citation/anti-guessing guidance**.
- “On-device” recommendations are inferred without running a phone or measuring latency, energy, memory pressure, or thermals.
- The intended PocketPal integration branch already contains the search implementation and the three recommended config changes, but the research artefacts call this “shipped” even though the branch is deliberately waiting for this study to finish before merge/release. The app-wide checked default for thinking is still `true`.

The benchmark therefore cannot currently support its strongest conclusions about retrieval difficulty, exact model ranking, the optimal configuration, the causal value of the date, fabrication rates, or production-on-device suitability.

Recommended publication status: **withdraw the leaderboard and “optimized configuration” claims from decision use, preserve the repository as an exploratory evidence archive, and run a clean vNext study from a preregistered protocol and untouched holdout.** This does not imply automatically reverting the feature branch: sound engineering and safety changes may remain as provisional implementation choices, but the research does not establish that the current bundle is optimal. Do not attempt another patch cycle on v3.

## Severity rubric

- **Critical** — invalidates a headline conclusion or makes a production/delivery claim false.
- **High** — can materially change effect size, ordering, significance, or interpretation.
- **Moderate** — damages reproducibility, auditability, or operational trust; may become high when combined with another flaw.

## What each research question can currently answer

| Research question | Current status | Why |
|---|---|---|
| RQ1 result count | **Unanswered** | Count 8 also raises the menu ceiling from 1000 to 1600, so result count is not isolated; actual included hits vary. |
| RQ2 formatting | **Unanswered causally** | Formatting changes token volume and appears mainly inside an adaptively selected bundle; no token-matched factorial confirmation. |
| RQ3 prompting | **Contradictory / unanswered** | v2 says bare ties shipped; v3 shows large model-specific changes. The “date” arm does not isolate date. |
| RQ4 provider | **Promising exploratory signal** | Brave appears better in one regime, but content, length, capture time, ranking, and evidence sets all change with provider. |
| RQ5 search-to-read | **Unanswered** | The “read-required” tier is not read-required in observed traces; almost all correct T2 answers occur without a read. |
| RQ6 model ranking | **Only the mechanical package-compatibility split is defensible** | One stochastic draw, nonuniform quants, no full floors, repeated facts, invalid tier construct, mutable remote anchors. Exact rankings and quality bands are not confirmed. |
| RQ7 baselines | **Partial** | Floors were run for only two models on v2 and none on v3; no-tools contamination is model-specific. |
| RQ8 thinking | **Token-cost direction likely; quality/product claim unresolved** | Local paired arm is useful, but wrong paired analysis and one draw remain; cloud anchors use another reasoning regime and no phone cost was measured. |
| Fabrication | **Pilot only** | Thirteen heterogeneous items measure refusal propensity as much as fabrication; no human evidence audit or stable estimate. |

## Flaw register

### Critical flaws

#### C1. The retrieval tiers do not measure a monotone difficulty construct

The published story treats T1→T4 as increasing difficulty. The data contradict it. On v3 Qwen3.5-4B scores T1 30/33, T2 28/31, T3 9/9, T4 12/12. Qwen3.5-2B likewise scores T2 18/31 but T4 10/12. The nominally harder tier is often easier.

This is not random noise alone. T4 frequently reveals a famous entity on hop one and lets parametric memory provide hop two. Tier composition (topic, entity fame, numerical specificity, source accessibility, query lexical overlap) is doing the work attributed to difficulty.

**Effect:** invalidates the headline “difficulty gradient,” tier-based model comparisons, and statements that a model specifically degrades on multi-hop retrieval.

**Fix:** stop calling these levels difficulty tiers. Define orthogonal, mechanically verified task attributes (`requires_page_body`, `min_sources`, `dependent_query`, `calculation`, `ambiguity`, `temporal_resolution`), then estimate empirical difficulty separately from a held-out reference panel. Difficulty is an outcome, not an author label.

#### C2. Required retrieval paths are never enforced or validated

The tier definitions are causal pathway claims, yet scoring checks only the final answer. A trace audit of the v3 Qwen3.5-4B confirmation run shows:

| tier | correct | correct with zero reads | correct with ≤1 search |
|---|---:|---:|---:|
| T1 | 30/33 | 30 | 29 |
| T2 (“must open page”) | 28/31 | **28** | 23 |
| T3 (“two sources”) | 9/9 | 9 | 0 |
| T4 (“dependent second search”) | 12/12 | 12 | **3** |

For Qwen3.5-4B, only one T2 item was read at all, and it was not needed for any of the 28 correct T2 answers. The failure is systematic, not specific to that model: across the seven working local models, **144/146 correct T2 answers (98.6%) used zero reads**. On T4, **35/48 correct local-model answers (72.9%) used at most one search**, so they could not have executed a second search dependent on the first. Curation checked some snippets at one point in time, not all queries a model can generate. A different query can expose the answer in a snippet.

**Effect:** T2 does not evaluate `read_url`; T3/T4 scores do not prove multi-source or dependent-hop reasoning; RQ5 is unanswerable.

**Fix:** store a frozen evidence graph per item and define admissible proof paths. Mechanically verify source IDs and dependency edges in the trace. For a read-required arm, withhold body-only facts from search snippets by construction. Score both answer correctness and path compliance.

#### C3. v3 contains repeated facts/rephrasings but treats them as independent questions

v3 carries all 53 v2 fresh items and adds undated/colloquial rephrasings of many of the same facts: Champions League, NBA Finals, French Open, Colombia election, Cursor acquisition, Fed decision, and others. A diagnostic proxy that connects prompts sharing a source URL or identical nontrivial gold reduces 85 prompts to **42 source/event-connected components**; 61 prompts sit in multi-prompt components. This proxy can over-connect distinct facts reported on one page, so 42 is not asserted as the exact effective n. It demonstrates substantial clustering that the current analysis ignores; the correct effective n requires explicit human-assigned `fact_id`/`event_id` fields.

Wilson intervals and significance calculations treat all prompts as independent Bernoulli trials. Repeated facts overweight a handful of sports/tech events and make intervals too narrow. They also leak the same source/search landscape into multiple “items.”

**Effect:** overstates effective sample size, distorts the leaderboard, invalidates simple binomial CIs, and contaminates the date/phrasing analysis.

**Fix:** introduce `fact_id` and `variant_id`. Split train/dev/test by `fact_id`, never prompt. Use clustered bootstrap or a mixed-effects model with fact as a random effect. Report both fact-level and phrasing-robustness scores.

#### C4. There is no untouched confirmation set; the campaign adaptively overfits the benchmark

There is no dataset that remains untouched by design decisions and is then used once for confirmation. v1 is used for screening and bundle selection; v2 is used to redesign tiers, revalidate the configuration, compare thinking, and publish rankings; v3 adds prompt variants and is used both to develop the date/fabrication story and publish the current board. Across v1→v2→v3, 17 protocol amendments, judge changes, criterion changes, repeated re-judging, and 192 run directories expose outcomes before subsequent decisions.

Honest amendments do not restore confirmatory validity. The final choice is optimized to observed benchmark noise—a leaderboard form of test-set overfitting.

**Effect:** winner's curse inflates the chosen bundle and model conclusions; reported p-values do not describe the adaptive procedure that produced the winner.

**Fix:** label all existing data exploratory. Build development and sealed holdout sets from disjoint facts and sources. Freeze protocol, judge, roster, exclusions, primary contrast, and analysis code before one confirmation run. A failed confirmation triggers a new study, not another amendment to the same one.

#### C5. The “date gives +17 points” treatment is not an isolated date treatment

`rv-prompt-bare` is “You are a helpful assistant.” The frozen prompt adds today's date **plus** search-first advice, tool budget, citation instruction, evidence-only instruction, and anti-guessing instruction (`harness/configs.py`). The contrast cannot attribute any difference to date.

On the 36 undated v3 prompts, the exact paired counts are:

| model | frozen prompt | bare prompt | difference |
|---|---:|---:|---:|
| Qwen3.5-4B | 33/36 | 28/36 | +13.9 points |
| Ministral-3-3B | 33/36 | 15/36 | +50.0 points |
| Qwen3-0.6B | 23/36 | 28/36 | **−13.9 points** |
| pooled prompts | 89/108 | 71/108 | +16.7 points |

The pooled headline hides extreme model heterogeneity and pseudoreplicates the same 36 prompts across three hand-picked models. Further, the earlier v2 conclusion that bare ties shipped does not hold uniformly on v3. Any reported significance must use the paired discordances and account for prompt/fact clustering and model interaction; the published unpaired p-value does not.

**Effect:** the public “Just telling it the date” card and p=0.008 causal claim are unsupported.

**Fix:** use a factorial prompt experiment with independently toggled date, search guidance, citation guidance, and abstention guidance. Use matched prompt variants of the same facts and analyze model×treatment interactions with paired/clustered statistics.

#### C6. Stochastic generation is sampled once, but uncertainty and significance ignore generation variance

The subject models run at temperature 0.7/top-p 0.95 with one generation per question. The study does not demonstrate local repeatability under the pinned seed, and remote endpoints strip the seed entirely. Wilson intervals model only question sampling. They omit within-question response/query variation, which can change the evidence retrieved as well as the answer.

**Effect:** row order, tier rates, config deltas, and p-values can move on a rerun; narrow cells of 9-13 items are especially unstable.

**Fix:** either use temperature 0 for a deterministic capability benchmark or run at least 5 independent samples per model×item×condition for a product-default benchmark. Model seed/run variance explicitly and freeze evidence separately from model sampling.

### High-severity flaws

#### H1. Statistical tests are unpaired even though observations are paired

Config and model contrasts use Fisher exact tests on total correct counts. The same questions are answered in both arms, so outcomes are paired. Pooling model rows also duplicates each question.

**Effect:** p-values and confidence statements are miscalibrated.

**Fix:** McNemar or paired permutation tests for a single matched contrast; hierarchical logistic/multinomial models for model×config studies; cluster/bootstrap by latent fact and seed.

#### H2. Pseudoreplication across models creates false sample size

The “n=159” configuration comparisons are 53 questions × 3 models, not 159 independent questions. A question that is intrinsically easy or whose search results contain the gold affects all three rows.

**Effect:** provider/bundle significance is overstated and generalization is implicitly to models never randomly sampled.

**Fix:** treat model as a fixed factor (for named-model conclusions) or predefine a defensible model population and random-effects structure. Cluster by question/fact; do not multiply n by model count in prose.

#### H3. Multiple comparisons and researcher degrees of freedom are not represented in the inference

Dozens of factor levels, bundles, datasets, rosters, tier contrasts, prompt variants, and headline candidates were examined. Select corrections were later added, but the final family of all attempted analyses is not controlled.

**Effect:** apparently significant survivors can be selection artifacts.

**Fix:** preregister one primary endpoint/contrast and a small secondary family with Holm control. Treat all other analyses as exploratory with effect sizes and intervals, not discovery p-values.

#### H4. Null results are converted into “does not matter” claims without equivalence power

Counts, snippets, reads, and turns are declared irrelevant from non-significant tests. Failure to reject a difference is not evidence of equivalence.

**Effect:** implementers may stop investigating meaningful effects the study was underpowered to detect.

**Fix:** define a smallest effect of practical interest before running; power the study; use TOST/equivalence intervals. Otherwise say “unresolved.”

#### H5. Bundle causality and “super-additivity” are not identified

Two of three bundle components are individually noise, yet the entire bundle is recommended. “Super-additive” is inferred by adding point estimates, without a factorial interaction test. The winning combination was adaptively selected.

**Effect:** the recommendation to ship all three components is unsupported; provider alone may carry the gain.

**Fix:** run a preregistered 2×2×2 factorial for provider×format×tool-description on a holdout, estimate main effects/interactions, and compare the full bundle directly with provider-only.

#### H6. RQ1 confounds result count with token ceiling and realized exposure

The count-8 configs set `menu_token_ceiling: 1600`, while count 3/5 use 1000. This changes two factors. The outcome also depends on hit text lengths, so requested count is not actual included count.

**Effect:** no causal answer to “how many results?” and no clean coverage-vs-context curve.

**Fix:** cross result count with a fixed token budget, plus a separate fixed-bytes/characters arm. Record actual included hits/tokens and analyze dose-response using realized exposure.

#### H7. Provider comparisons change evidence, length, ranking, time, and failure behavior simultaneously

Brave and Tavily return different documents, ordering, text fields, snippet lengths, metadata, and capture times. That is valid for an end-to-end provider comparison, but not for claims about model comprehension or format. Capture-on-miss makes evidence vary again by generated query and run time.

**Effect:** provider gains cannot be attributed, and config/model comparisons inherit evidence luck.

**Fix:** run two studies: (a) retrieval-provider evaluation with fixed queries and relevance judgments; (b) reader/agent evaluation on a common frozen corpus. Keep a separate live end-to-end monitor for ecological performance.

#### H8. Record-replay does not hold the web constant across arms and cannot reproduce a clean rerun

Only identical queries replay. Model/config changes produce different queries, which capture live results across days. The same cache is also reused across dataset versions. The manifest records cache keys but not a complete per-run evidence bundle or a canonical web snapshot.

Run and question order are fixed rather than randomized. Under capture-on-miss, earlier cells systematically populate the cache while later cells receive a mixture of replayed and newly live evidence. Time, model/config order, and cache state are therefore entangled.

**Effect:** differences may be search-result drift or query luck; an outside rerun cannot reproduce the board from first principles.

**Fix:** materialize an immutable evidence package per dataset version (query, timestamp, provider response, normalized hits, page contents, hashes). Confirmation must be replay-only with zero misses. Live-web scores must be repeated in randomized time blocks and reported separately.

#### H9. No-tool contamination controls are incomplete and absent for the current v3 board

v2 floors cover only Qwen3.5-4B and Ministral. v3 has no floor runs. Other gate-failed models answer some T2/T3 facts from memory/guessing, proving contamination is model-specific.

**Effect:** “retrieval-required” and “the board measures retrieval, not memory” do not hold roster-wide.

**Fix:** run matched no-tool and evidence-shuffled controls for every ranked model and every fact. Report retrieval lift per model/item; quarantine items solved reliably without evidence when measuring retrieval skill.

#### H10. The judge and gold stack lacks independent human ground truth

Golds were agent-curated. “Manual” labels were another LLM. The 60/60 precision check is substring presence, not semantic correctness. The judge sees gold but not evidence and remote judge model revisions are not pinned.

**Effect:** systematic gold/judge errors can move all results; judge agreement with another LLM does not establish validity.

**Fix:** human-verify every confirmation gold against archived primary evidence. Blind double-label a statistically meaningful sample with adjudication and report agreement. Pin judge outputs and use a fixed judge revision or human primary endpoint.

#### H11. Correctness ignores groundedness, source quality, citation validity, and unsupported extra claims

Groundedness was dropped. The judge rewards the key fact even if the answer invents surrounding details or cites sources that do not support it. Search-assistant quality is thus reduced to short-answer matching.

**Effect:** a lucky memory answer and a well-grounded synthesis score the same; verbose hallucinations can pass.

**Fix:** score answer correctness, claim-level entailment from retrieved evidence, citation precision/recall, source quality/diversity, and unsupported-claim rate separately. Require evidence IDs in outputs for automated traceability.

#### H12. The “unanswerable” split measures abstention style more than fabrication

The 13 items mix future-premise, undisclosed, private, and unknowable questions. The judge calls any “could not find” response correct, even if the model searched poorly. Proving that information does not exist is intrinsically difficult. Empty/parse-failed cases remain in the denominator and are neither refusal nor fabrication.

**Effect:** 8-69% rates are unstable and not comparable as a general hallucination trait; “does not track accuracy” is an untested correlation claim.

**Fix:** separate false-premise, temporally unresolved, closed-world absent, and open-world not-found tasks. Use controlled corpora for true negatives, require adequate search coverage, enlarge each stratum, and human-adjudicate asserted claims.

#### H13. Dataset sampling has no target population and is strongly topic-skewed

v3 fresh contains 25/85 sports items, 14 tech, 13 politics, and no empirical weighting from PocketPal user queries. It is English-only and concentrated in an eight-week period. Source concentration includes 35 Wikipedia URLs.

**Effect:** overall accuracy is an arbitrary mixture; rankings may reflect sports/news search affinity rather than user value. Wilson intervals describe a hypothetical binomial sample but cannot justify population-generalization intervals when items were deliberately curated without a sampling frame.

**Fix:** define the estimand. Build a privacy-safe taxonomy from real or realistically sampled user intents, set strata/weights in advance, include languages/local queries and ambiguity, and publish macro plus population-weighted scores.

#### H14. Model comparisons do not hold deployment conditions constant

Most local models are Q4_K_M, but Qwen3-1.7B is Q6_K. Chat templates differ, five packages receive no schemas, context behavior differs, and remote anchors run different serving stacks with seeds stripped and reasoning uncontrolled.

**Effect:** the leaderboard mixes model capability, quantization, packaging quality, runtime integration, and serving policy.

**Fix:** publish separate boards: checkpoint capability under a validated common tool template; package-as-downloaded compatibility; and product deployment performance. Match quant/size budget where making model claims. Pin exact weight hashes, tokenizer/template hash, llama.cpp commit/build, and serving flags.

#### H15. Cloud anchors and local models use different reasoning regimes

`enable_thinking=false` is sent only to local llama.cpp. Remote anchors manage their own reasoning. The board compares deliberately thinking-off locals with opaque cloud reasoning.

**Effect:** “close to frontier” is not a controlled capability comparison.

**Fix:** separate a product board (same cost/policy constraints where controllable) from a best-capability reference board. Never use an uncontrolled anchor for a parity claim.

#### H16. “On-device production” claims lack on-device measurements

The DGX study uses token/turn counts as proxies. It has no iOS/Android latency, time-to-first-token, energy, peak memory, thermal throttling, crash rate, network/API latency, or long-context prefill measurement. Generated-token tax alone does not establish battery or user-perceived latency.

**Effect:** the study cannot select a production model/config for phones, which is one of the R&D mission's core outcomes.

**Fix:** run representative iPhone and Android chip-family benchmarks using the actual PocketPal/llama.rn path. Predeclare quality-latency-energy constraints and use Pareto analysis rather than a quality-only leaderboard.

#### H17. The harness is a hand-maintained replica, not a conformance-tested product path

The contract was copied from a feature branch and subsequently diverged as app commits changed. There is no golden contract suite that executes identical fixtures through the harness and PocketPal implementation.

**Effect:** harness findings can reflect replica behavior, not app behavior; the delivery chain already demonstrates drift.

**Fix:** extract shared fixtures or a conformance test: tool schemas, prompt rendering, budgeting, wrappers, forced-final behavior, errors, and thinking fields must hash/compare against the target app revision before every campaign.

#### H18. The 300-token schema canary is a useful incident heuristic, not a general capability gate

The current canary declares schemas missing when turn-one prompt tokens are below 300. The observed bimodality is strong evidence for the five tested packages, especially alongside template inspection. But prompt length also depends on tokenizer, schema wording, system prompt, and question length. A long question can push a schema-less prompt over 300 (false negative); a compact schema/tokenizer can fall below 300 (false positive).

**Effect:** the published recommendation that one threshold “catches all five and any future repack” overgeneralizes from the incident. Used as a permanent product gate, it can silently misclassify new packages.

**Fix:** inspect the actual rendered prompt or runtime capability result and verify that declared tool names/signatures are present. Keep token length as an anomaly signal, not the authoritative gate.

### Moderate but important artefact/governance flaws

#### M1. The protocol is not a usable source of truth

It remains “v1” despite 17 amendments, has an empty factors table, lists a superseded local judge and ceiling in the main body, retains groundedness as a metric after dropping it, and numbers amendments out of order.

**Fix:** preserve this as an immutable historical protocol. For vNext, create a preregistration with a schema-validated amendment file; no retroactive edits after confirmation starts.

#### M2. Current artefacts contradict each other

README says v2 and commands rerun `confirm2`; the leaderboard is v3/`confirm4`; report opens by saying the current result is v2 and never provides a full v3 analysis; `STATE.md` still says v2 curation is next; `PROVENANCE.md` describes v1 evidence despite v4 revalidation.

**Fix:** one machine-readable study manifest must name the current protocol, dataset, run set, analysis revision, report, and publication payload. Generated docs must fail CI on mismatch.

#### M3. Report numbers are not actually generated from analysis

Tables and prose are manually appended. Past dead anchors, stale charts, cherry-picks, and corrections show that “regenerable” is aspirational. The exporter checks only a few hand-coded claims.

**Fix:** generate every table, effect, interval, and claim datum from a versioned analysis dataset. Narrative references stable claim IDs. CI rebuilds from raw runs and compares a clean working tree.

#### M4. Run indexing and quarantine are inadequate

Hundreds of run directories include exploratory, superseded, contaminated, rerun, and current data. Selection is primarily substring tags (`confirm2`, `confirm3`, `confirm4`), and `scores.jsonl` is cumulative.

**Fix:** create an immutable run registry with status (`exploratory`, `eligible`, `quarantined`, `superseded`), reason, parent experiment, exact analysis inclusion, and checksums. Analyses consume an explicit frozen inclusion manifest, never a tag substring.

#### M5. Remote services are mutable and insufficiently pinned

OpenRouter aliases, provider routing, judge implementations, and search APIs can change. Manifests record names but not provider revision, response IDs, routed backend, or raw judge response metadata.

**Fix:** store complete raw response metadata, endpoint/provider revision where available, and a judge calibration set. Treat remote reruns as a new environment block.

#### M6. Mechanical metrics have construct and denominator problems

Tool-call validity is `None` for zero calls, so a package that never receives tools is not “invalid”; engagement uses executed searches rather than attempted/valid calls; no-search correctness is not graded; completion accepts recovered reasoning content that may not be user-visible in the product.

**Fix:** define a trace-state taxonomy: schema delivered, call attempted, parsed, schema-valid, executed, result usable, answer user-visible. Score no-search task quality as well as unnecessary calls. Keep produced-answer and delivered-answer metrics separate.

#### M7. Delivery status is documented inaccurately, although the intended integration branch is correct

The research was built for `origin/feature/TASK-20260625-1135`, not PocketPal `main`. That branch does contain the complete search feature and the research-driven changes:

- `668e81d7` — enriched tool descriptions;
- `e257258c` — markdown search-result menu;
- `a9ca6553` — Brave as the default provider;
- `eab95f6b` — budget against the rendered menu.

It also contains the talent registry, UI switch, search/read engines, grounding prompt, and tests. The branch is intentionally waiting for the research to be finalized, so absence from `main` is **not** a delivery-chain failure. My initial audit interpretation on that point was wrong.

The remaining problem is terminology and state precision: the report repeatedly says “shipped” or “adopted upstream” when the verified state is **implemented on the target feature branch, not yet merged/released**. Separately, `enable_thinking` remains `true` in `defaultCompletionParams`; thinking-off is supported and user-controllable, but is not the app-wide default.

**Effect:** this does not invalidate the benchmark methodology, but it can mislead readers about release and default activation state.

**Fix:** report the chain explicitly: implemented on target branch = yes; supported by llama.rn = yes; UI-reachable on target branch = yes; merged to main = no; released = no; thinking-off active by default = no. Update the final state when the branch merges.

## Findings worth preserving, with narrower wording

1. **Tool-schema delivery failure is real for the tested GGUF packages/runtime combination.** Preserve the telemetry and canary. Do not phrase it as a model-family incapability until template overrides are tested.
2. **The `reasoning_content`/empty-content defect is a real integration finding.** Preserve its regression fixture and verify the fix through llama.rn and PocketPal.
3. **Thinking increases generated tokens substantially in the tested local Qwen arms.** The magnitude is useful. The correctness effect and phone-level cost remain unresolved.
4. **Brave is a strong candidate for a clean provider confirmation.** Current evidence is exploratory, not enough for a causal universal recommendation.
5. **The combined configuration is promising.** Its exact active ingredients and out-of-sample lift are not established.
6. **Jina reader 403s are useful operational telemetry.** Re-estimate on a representative URL sample before quoting a population rate.

## PocketPal feature-branch disposition while the study is rebuilt

The target branch does not need to throw away all engineering work while waiting for clean confirmation. Separate implementation correctness from optimization claims.

**Reasonable to preserve on independent engineering/safety grounds:**

- provider abstraction, BYOK/consent flow, URL validation, bounded responses, and untrusted-content wrapping;
- the model-driven search/read loop and forced final answer after budget exhaustion;
- tool-schema delivery diagnostics and the `reasoning_content` regression fix, once verified through the actual PocketPal/llama.rn path;
- telemetry needed to measure realized results, calls, errors, evidence, tokens, and user-visible completion.

**Keep configurable and label provisional pending confirmation:**

- Brave as default provider;
- markdown result formatting;
- enriched tool descriptions;
- result count/menu budget, read policy, turn cap, and thinking default;
- any model recommendation or package allowlist.

If product timing requires merging before the clean study finishes, ship behind an explicit experimental flag or reversible configuration, avoid publishing the current leaderboard as justification, and collect privacy-safe operational telemetry. “Provisional” here means the choice may be sensible; it means the benchmark has not established optimality.

## Recovery plan

### Phase 0 — stop further contamination

1. Mark v1-v3 and all current leaderboard/config results **exploratory / not for production decision**.
2. Remove or caveat the public cards for tier gradient, +17 date, configuration doubling, frontier proximity, and fabrication range.
3. Freeze current repository history and create an explicit inventory of eligible, superseded, and known-bad runs.
4. Preserve the existing audit and this audit; do not rewrite history.
5. Do not automatically revert the PocketPal feature branch. Separate independently justified engineering/safety fixes from claims of research optimality, and keep configurable choices behind explicit defaults until confirmation.

Exit criterion: no downstream consumer can mistake the current board for confirmed evidence.

### Phase 1 — define the decision and estimands

Create separate studies instead of one benchmark trying to answer everything:

1. **Retrieval-provider study:** fixed queries, provider relevance/coverage, latency, failures, and cost.
2. **Agent-policy study:** identical frozen evidence corpus; compare prompts, formats, count/budget, read policy, and turns.
3. **Model/package capability study:** same template/runtime/evidence; separate raw checkpoint capability from GGUF package compatibility.
4. **Live end-to-end product study:** actual PocketPal path on devices, repeated over time.
5. **Safety/abstention study:** controlled false premises and closed-world negatives.

For each, state population, unit of analysis, primary endpoint, smallest practical effect, and production decision it informs.

Exit criterion: every RQ maps to one study and one estimand; no metric is asked to represent two constructs.

### Phase 2 — rebuild the dataset

1. Add `fact_id`, `prompt_variant_id`, required evidence IDs, source snapshots, and expiry.
2. Create dev and sealed holdout splits by fact/source/event, not wording.
3. Use orthogonal task attributes instead of T1-T4; empirically calibrate difficulty only after the holdout is sealed.
4. Determine independent facts per primary stratum by simulation/power analysis using the declared smallest practical effect. The present 9-31-item tier cells are demonstrably insufficient; do not replace them with another arbitrary round number.
5. Add matched dated/undated and formal/colloquial variants of the **same facts** for robustness analyses; never count variants as independent facts.
6. Human-verify golds and evidence; double-annotate ambiguous items.
7. Weight categories from a declared user-intent distribution; otherwise report only stratified macro scores.

Exit criterion: path validators pass, no latent fact crosses dev/holdout, and two humans approve confirmation golds.

### Phase 3 — redesign the harness and evidence layer

1. Confirmation runs are replay-only against a complete immutable evidence bundle; zero cache misses allowed.
2. Add product conformance fixtures against a pinned PocketPal commit and llama.rn/native revision.
3. Pin GGUF SHA-256, tokenizer/chat-template hash, llama.cpp commit/build, all generation flags, and remote response metadata.
4. Record evidence IDs delivered at every turn and compute path compliance, grounding, citation, and unsupported-claim metrics.
5. Add explicit canaries for schema delivery, attempted calls, parsing, result failures, final-answer visibility, and context truncation.
6. Add a run registry and immutable inclusion manifest.

Exit criterion: a clean replay reproduces inputs byte-for-byte and all product conformance tests pass.

### Phase 4 — run clean experiments (time depends on power)

Recommended designs:

- Provider: randomized paired questions, fixed query sets for retrieval quality; randomized temporal blocks for live end-to-end.
- Bundle: 2×2×2 factorial for provider×format×tool-description, including provider-only and full-bundle cells.
- Count/budget: factorial result count×token budget with realized-hit exposure recorded.
- Prompt: date×search-guidance×citation×abstention factorial on matched prompt variants.
- Thinking: paired off/on samples for each supported model, ≥5 seeds/item if retaining temperature 0.7.
- Ranking: one sealed configuration and holdout; all official models at matched deployment budgets, with separate package-compatibility failures.

Randomize run order where live systems are involved. Do not inspect holdout outcomes until all cells and exclusions are complete.

Exit criterion: preregistered sample size reached, no unplanned exclusions, and all runs pass integrity checks.

### Phase 5 — analysis and human validation

1. Use paired tests or hierarchical models; cluster by fact and model/seed as appropriate.
2. Report effect sizes and 95% intervals; correct the declared secondary family for multiplicity.
3. Use equivalence tests for “does not matter.”
4. Blind double-label the required judge-validation sample; adjudicate disagreements.
5. Report sensitivity to judge, seed, category weights, contamination controls, and evidence failures.
6. Publish per-item traces for every headline claim.

Exit criterion: an independent analyst can regenerate all tables from the frozen inclusion manifest.

### Phase 6 — on-device and delivery confirmation

1. Benchmark representative iOS and Android chip families through PocketPal+llama.rn: TTFT, total latency, energy, peak RAM, thermal behavior, and failure rate.
2. Produce a quality-cost Pareto frontier, not a single accuracy order.
3. Verify every production claim through: upstream → llama.cpp vendored layer → llama.rn TS API → PocketPal UI/control → default → released build.
4. State explicitly whether each recommendation is merged, user-reachable, and active by default.

Exit criterion: the recommendation names a tested device envelope and a verified released/default state.

## Proposed clean artefact layout

```text
study-vnext/
  preregistration.yaml
  amendments/                 # locked once confirmation starts
  datasets/
    dev/
    holdout.sealed/
    evidence-snapshots/
  run-registry.jsonl
  inclusion-manifests/
    exploratory.json
    confirmation.json
  raw-runs/
  human-labels/
  analysis/
    analysis.py
    generated-results.json
  report.generated.md
  delivery-chain.generated.md
  integrity/
    conformance-tests/
    reproduction-report.json
```

`JOURNAL.md` should remain a chronological lab notebook, but decisions that define inference belong in the preregistration and amendment files. The journal must not be the only place where the reader can discover a changed endpoint, exclusion, criterion, or failure.

## Minimum go/no-go gates before publishing again

- Zero unresolved Critical findings.
- Sealed fact-level holdout never used for design iteration.
- Required retrieval paths mechanically validated.
- Full-roster no-tool/evidence-shuffle controls.
- ≥5 samples/item at stochastic settings, or deterministic decoding.
- Correct paired/clustered statistics and multiplicity plan.
- Human-verified golds and judge calibration.
- Byte-replayable evidence and pinned model/runtime artefacts.
- Actual on-device measurements for production claims.
- Verified delivery chain and default activation state.
- One generated report whose dataset/run/config IDs agree everywhere.

Until those gates pass, the correct high-level conclusion is:

> Ferret-bench uncovered useful engineering defects and promising hypotheses, but it does not yet establish a reliable retrieval-difficulty scale, a production model ranking, or an optimal PocketPal web-search configuration.
