# Latest-work resolution assessment

Date: 2026-07-21  
Assessed Ferret Bench revision: `dc77f33` (`origin/main`, fetched 2026-07-21)  
Prior audit: `REVIEW-2026-07-15-rigorous-methodology-audit.md`  
PocketPal target: `a-ghorbani/pocketpal-ai`

## Executive verdict

The latest Study 1 work is materially cleaner than v1-v3, but it has **not resolved enough of the audit to make the research decision-grade**.

Against the prior audit's 31 findings:

| status | count | findings |
|---|---:|---|
| Closed or removed from current scope | 5 | C1, C5, H2, H12, H15 |
| Partially addressed | 12 | C2, C3, C4, H3, H4, H13, H14, H18, M2, M3, M6, M7 |
| Substantially unresolved | 14 | C6, H1, H5-H11, H16-H17, M1, M4-M5 |

"Removed from scope" is not the same as experimentally answered. The date-effect, tier-gradient, fabrication-rate, and cloud-parity claims were withdrawn rather than confirmed with a corrected experiment.

Recommended disposition: **treat Study 1 as an improved exploratory model/package leaderboard. Do not use it as confirmation of an exact model order or proof that the current PocketPal search configuration is optimal.**

## What genuinely improved

1. The invalid T1-T4 difficulty construct was removed. Study 1 no longer publishes a tier gradient.
2. Dataset records now have `fact_id`; dev and holdout are partitioned by fact rather than prompt wording.
3. Leaderboard accuracy is aggregated at fact level, so prompt variants no longer multiply the reported sample size.
4. A 58-fact sealed holdout exists and has not been used for the current leaderboard.
5. Tool-schema/package failures are separated from the ranked models rather than interpreted as zero model capability.
6. Cloud anchors were removed from the on-device leaderboard.
7. The fabrication headline was withdrawn because the current unanswerable dev split has only 3 facts.
8. Public limitations now acknowledge dev-only results, composition skew, workstation execution, and unmeasured phone performance.

These are meaningful corrections. They do not, however, close the central configuration, reproducibility, ground-truth, stochasticity, and on-device validation gaps.

## Finding-by-finding status

### Critical findings

| ID | status | latest-work assessment |
|---|---|---|
| C1 | Closed by scope correction | T1-T4 and the monotone-difficulty story were removed. No replacement difficulty scale has been validated. |
| C2 | Partial | Study 1 stopped making T2/T3/T4 path claims, but did not implement frozen evidence graphs or runtime path compliance. RQ5 remains unanswered. |
| C3 | Partial | `fact_id`, fact-level splitting, and fact-level aggregation were added. Clustering remains automatic/heuristic without the promised human confirmation, and the CI calculation is not valid for fractional per-fact scores. |
| C4 | Partial | A new dev set and unused holdout were created after the old configuration was selected. However, the curation spec remains `DRAFT, not yet frozen`, there is no immutable preregistration/inclusion manifest, and no sealed-holdout confirmation has occurred. |
| C5 | Closed only as a withdrawn claim | The public `+17 points from date` claim was removed. The isolated date experiment was not run, so the causal question remains unanswered. |
| C6 | Unresolved | Official model runs still use temperature 0.7/top-p 0.95 with one sample per model-item and seed 42. No repeatability or multi-seed uncertainty analysis was performed. |

### High-severity findings

| ID | status | latest-work assessment |
|---|---|---|
| H1 | Unresolved | No paired model-comparison or paired configuration analysis is present. Overlapping marginal CIs are used to describe a cluster, which is not a paired test or equivalence test. |
| H2 | Closed for the current headline n | The current score uses 80 facts rather than pooling facts across models or treating all variants as independent. |
| H3 | Partial | Most old significance claims were removed, but there is no frozen primary/secondary analysis family and the public model stories were selected after inspecting the leaderboard. |
| H4 | Partial | The copy acknowledges noise, but labels models as tied/indistinguishable based on overlapping 90% intervals without an equivalence margin or powered equivalence analysis. |
| H5 | Unresolved | Study 1 evaluates only the already-selected bundle. It does not run provider x format x tool-description factorial cells or compare provider-only with the complete bundle. |
| H6 | Unresolved | There is no corrected result-count x fixed-budget experiment or realized-exposure dose-response analysis. |
| H7 | Unresolved | Brave remains the only backend in the Study 1 leaderboard. Provider retrieval quality is not separated from reader/agent behavior. |
| H8 | Unresolved | Official runs use `replay-or-live`. Models receive different mixtures of cached and newly live results, so time, run order, queries, and evidence remain entangled. There is no complete immutable replay package. |
| H9 | Unresolved | No per-model no-tool floor was run on the fresh facts. The published `memory` column is accuracy on a different stable-knowledge split; it cannot establish retrieval lift for fresh facts. |
| H10 | Unresolved | All 871 admission receipts have `human_signed: false`. Golds are LLM-panel-verified, not human-verified against archived primary evidence, and the scoring judge has no reported human calibration study. |
| H11 | Unresolved | The primary score still grades answer correctness without claim-level groundedness, citation entailment/precision, source quality, or unsupported-extra-claim penalties. |
| H12 | Closed only as a withdrawn claim | The fabrication rate was removed because the dev split has only 3 unanswerable facts. The safety/abstention question itself remains unanswered. |
| H13 | Partial | Study 1 declares a controlled crisp-fact estimand and composition skew. It still lacks a user-derived target population, languages/local intents, and the promised macro and weighted outputs. |
| H14 | Partial | Package/schema failures are now listed separately. The ranked board still mixes quantizations, package templates, file-size budgets, and two harness revisions, without complete weight/template/runtime hashes. |
| H15 | Closed for the current board | Cloud anchors were removed, eliminating the uncontrolled local-versus-cloud parity comparison. |
| H16 | Unresolved | Runs are workstation/DGX only. There are no iOS/Android latency, TTFT, energy, RAM, thermal, long-context, network, or crash measurements. |
| H17 | Unresolved | No conformance suite proves that the harness matches the current PocketPal/llama.rn prompt, schema, budgeting, wrapper, error, and final-answer behavior. |
| H18 | Partial | Gate failures are separated and the observed incident is real, but `schema_not_rendered` is still determined from the 300-token threshold rather than direct inspection of rendered tool definitions. |

### Artefact and governance findings

| ID | status | latest-work assessment |
|---|---|---|
| M1 | Unresolved | The replacement curation spec is explicitly draft/exploratory, while completed runs and handoff material call the configuration frozen. There is still no locked preregistration plus amendment system. |
| M2 | Partial | Study 1 is more self-contained, but its artefacts contradict one another: seven versus nine gate-passers, `5 of 9` failures versus 14 packages actually tested, stale `not pushed` wording, and repeated `28 needs_human` wording for a 281-item queue. |
| M3 | Partial | `leaderboard.json` is generated from local runs and the human table agrees with it. The public Git repository does not contain the official Study 1 raw runs, so a fresh clone cannot regenerate the payload; interpretive prose remains manually maintained. |
| M4 | Unresolved | There is no immutable run registry or inclusion manifest. The exporter finds run directories by glob/tag, while all Study 1 run directories are Git-ignored. |
| M5 | Unresolved | Search, curator, and judge services remain mutable aliases with incomplete routed-backend/revision/raw-response metadata. |
| M6 | Partial | Search/schema telemetry and package-failure presentation improved. Direct rendered-schema verification, delivered-answer metrics, fresh no-tool controls, groundedness, and no-search task reporting remain absent. |
| M7 | Partial; delivery state changed | The feature is now merged to PocketPal `main`, but not present in a release tag. Research artefacts still use `shipped` imprecisely, and PocketPal's app-wide thinking default remains on while Study 1 evaluates thinking off. |

## Evidence for the remaining blockers

### 1. The protocol was not frozen

`study-1/CURATION-SPEC.md` begins with:

> `DRAFT, not yet frozen`

and identifies its state as exploration. Nevertheless, run names, the leaderboard, and page content call the configuration frozen. A frozen config hash is useful but is not a frozen study protocol, endpoint family, exclusion rule, roster, or analysis plan.

### 2. The human-signoff gate was not executed

Receipt audit:

- receipts: 871
- admitted: 628
- dropped: 243
- `human_signed: true`: 0
- `human_signed: false`: 871

This conflicts with the curation spec's requirements for human confirmation of clusters, holdout golds, and unanswerable negative evidence. The later wording correction from `human-curated` to `panel-verified` is honest, but it does not resolve the underlying ground-truth requirement.

### 3. The fresh set has no no-tool control

The public metric definition says fresh facts cannot be answered from memory. No Study 1 run disables tools on those same facts for each ranked model. Stable-split accuracy is a general-knowledge check, not a matched contamination floor.

Required correction: run every ranked model on the same fresh items with tools disabled and, ideally, with shuffled/irrelevant evidence. Report per-fact retrieval lift and quarantine facts that are reliably solved without relevant evidence.

### 4. Official evidence is not held constant

All 14 Study 1 manifests specify `http_mode: replay-or-live`. Search-event audit on the nine passers shows different live/cache mixtures. Examples:

| model | search events | cached | newly live |
|---|---:|---:|---:|
| qwen3-06b | 375 | 24 | 351 |
| qwen3-1.7b | 369 | 78 | 291 |
| qwen35-4b | 454 | 156 | 298 |
| gemma-4-e2b | 400 | 183 | 217 |
| lfm25-1.2b | 383 | 190 | 193 |
| bonsai-27b-q1 | 380 | 224 | 156 |

This progression is consistent with cache population over run order. Because models also generate different queries, a fair model comparison needs either a frozen evidence corpus or randomized repeated live blocks. Study 1 does neither.

### 5. Statistical uncertainty is incorrectly calculated

The exporter:

1. averages binary correctness across variants within each fact;
2. averages the resulting fractional fact scores;
3. calculates `k = round(rate * n_facts)`;
4. applies a binomial Wilson interval.

The fact outcomes are not binary after step 1, so the Wilson model does not match the estimator. The correct minimum is a nonparametric bootstrap over facts, retaining all variants inside the sampled fact. Model contrasts should use paired fact-level bootstrap/permutation intervals because all models answer the same facts.

Also, overlapping marginal confidence intervals do not establish equivalence or a five-model tie.

### 6. Sample-size and estimand claims exceed the achieved dataset

The curation spec targets approximately 400 independent facts. The admitted dataset contains 193 facts total:

- dev: 135 facts, including 80 fresh facts;
- holdout: 58 facts, including 32 fresh facts.

The handoff itself acknowledges that 80 fresh facts cannot finely separate neighbouring models. The 32-fresh-fact holdout is smaller still and cannot provide the precision described for the originally targeted approximately 100 fresh holdout facts.

The declared category weighting is also not implemented in the exported score: only the observed overall crisp-fact mixture is shown, not both category-macro and declared-weight estimates.

### 7. The current study does not answer the configuration RQs

Study 1 evaluates a single preselected configuration:

- Brave;
- five results;
- Markdown menu;
- enriched descriptions;
- date/search/citation/anti-guessing prompt bundle;
- read available;
- five turns;
- thinking off.

There are no Study 1 contrasts isolating these choices. Consequently it can estimate model/package performance under this bundle, subject to the other limitations, but cannot establish that the bundle or its components are optimal.

### 8. Raw Study 1 evaluation runs are absent from the public repository

The 14 official directories under `runs/*study1*` are ignored by `.gitignore`; no Study 1 run outputs or judgments are tracked. The HTTP cache/evidence is also ignored. The repository contains the derived JSON and Markdown leaderboard but not the raw evaluation inputs needed by `study-1/export_site.py`.

This breaks clean-clone regeneration. Sensitive or bulky evidence can live in a versioned release/archive rather than ordinary Git, but it must have immutable hashes and a documented retrieval path.

## New artefact inconsistencies introduced by Study 1

1. `study-1/WEBDEV_HANDOFF.md` says seven gate-passers; the leaderboard contains nine.
2. `page_content.json` says five of nine packages failed tool delivery. The experiment ran 14 packages: nine passers plus five failures.
3. The handoff says the repository has not yet been pushed, although Study 1 is on `origin/main`.
4. `resolve.py`, the journal, and `RESOLUTION_SUMMARY.md` retain `28 needs_human` text from the pilot even though the scale run had 281.
5. The spec promises human holdout signoff and human cluster confirmation, but the recorded workflow explicitly performed no human review.
6. The spec promises macro plus weighted scores, but the export provides neither category-macro nor declared-weight results.
7. The public gate-failure wording treats absence of the schema as established, while the harness still infers it from the under-300-token heuristic.

These do not all alter raw model answers, but collectively show that document/payload consistency gates are still missing.

## PocketPal delivery-chain update

The delivery status in the July 15 audit has changed.

Verified 2026-07-21:

| delivery link | status |
|---|---|
| Research target feature branch | `origin/feature/TASK-20260625-1135` at `eab95f6b` |
| PocketPal `main` integration | Yes; squash commit `43477ad3` on 2026-07-17, `Add internet search to chat` |
| User-facing search settings | Present on `main` |
| Brave default | Yes on `main` |
| Default result count | 5 on `main` |
| Markdown search menu | Present on `main` |
| Enriched search description | Present on `main` |
| Released tag containing integration | No tag contains `43477ad3` as of 2026-07-21 |
| App-wide thinking default | Still `true` |

Correct wording is therefore:

> Internet search is merged into PocketPal main, user-reachable, and configured with Brave/five results plus the enriched Markdown search presentation. It is not yet present in a release tag. The Study 1 thinking-off condition is not the app-wide default.

The merge does not repair the benchmark methodology. It changes delivery status and increases the importance of calling the configuration provisional rather than experimentally optimal.

## Minimum remediation before confirmation/public decision use

1. **Freeze a real preregistration** containing estimand, primary endpoint, roster, exclusions, model/runtime hashes, analysis code, and smallest effect of interest.
2. **Human-verify confirmation golds and evidence**, with blind double-labeling and adjudication for a judge-calibration sample.
3. **Publish an immutable evidence package and raw run archive**; confirmation must be replay-only with zero misses.
4. **Run fresh-set no-tool and evidence-shuffle controls for every ranked model.**
5. **Use deterministic decoding or at least five independent samples per item**, then include run variance in uncertainty.
6. **Replace Wilson intervals with fact-bootstrap intervals** and use paired fact-level comparisons/equivalence tests.
7. **Run separate causal studies** for provider, bundle components, count/budget, prompt components, read policy, and thinking.
8. **Use the sealed holdout once**, only after every decision and exclusion is locked; create a new holdout if it has been inspected beyond integrity administration.
9. **Add PocketPal conformance fixtures** for prompt/schema rendering, budgets, wrappers, tool errors, and delivered final answers.
10. **Run actual iOS and Android benchmarks** and publish quality/latency/energy/RAM/thermal Pareto results.
11. **Generate all public claims from checked data** and fail CI on count, roster, config, dataset, or wording inconsistencies.

## Handoff conclusion

Study 1 is a useful recovery step and a more honest exploratory benchmark than v1-v3. It supports limited statements such as:

- the tested package/tool-template failures are operationally important;
- several working packages obtain broadly similar crisp-fact accuracy under the tested bundle;
- smaller models may be competitive enough to justify device testing;
- the current dataset is insufficient for fine ordering or fabrication claims.

It does **not** yet establish:

- the exact model order;
- that fresh accuracy is retrieval lift rather than memory/guessing;
- that the current search bundle is optimal;
- the causal value of Brave, Markdown, descriptions, date prompting, result count, read policy, or thinking-off;
- production suitability on phones;
- reproducibility from a clean public checkout.

Until the remediation gates pass, the appropriate label is:

> **Improved exploratory Study 1; not a confirmatory benchmark and not sufficient evidence for a final PocketPal model/configuration decision.**
