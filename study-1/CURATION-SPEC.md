# study-1 — dataset curation spec (DRAFT, not yet frozen)

Status: **exploration**. This file becomes part of the preregistration and freezes *before* the first confirmation run. Until then it is editable. After freeze, a change opens study-2 — it does not amend this.

Supersedes the v1–v3 tier-labelled dataset. Those questions are reused as a **candidate pool** (`datasets/candidates/`); only the questions, golds, `acceptable_answers`, `source_urls`, and split survive. The `tier` label is discarded (preserved as `origin_tier` provenance only — it is not a claim).

## The core principle

The dataset is the **output of a validator**, not a hand-authored list. An item enters only if a probe *proves* the property its use depends on. A label is a testable prediction about model behaviour; if we never ran the harness against the label, we never verified it — that is how "read-required, 90%, zero reads" happened. Difficulty is an **outcome measured post-hoc**, never an author tier.

Curation freedom is a feature: we may drop any ambiguous item. Dropping costs yield, never validity. Keep only items whose property is **unambiguously exhibited**.

## Temporal validity — every fresh item is bracketed by a window

A fresh item is only a valid retrieval test inside a time window. Two hard validator gates:

```
anchor − FRESHNESS_WINDOW  ≤  event_date  <  anchor          # freshness floor
gold stays correct until    →  valid_until  (> anchor)        # expiry ceiling
```

- **Freshness floor** (`FRESHNESS_WINDOW = 60 days`, default): the event must have happened within ~2 months of the anchor. This is the **primary contamination guard**, and it is strong, not a weak proxy: training data is frozen months before a model ships (data → filter → train → eval → release), so an event this recent is post-cutoff for essentially every model — on-device models most of all. The old validator only checked `event_date < anchor` (in the past), never recency; v3 satisfied ~60 days only by hand.
- **Expiry ceiling** (`valid_until`): time-relative / recurring-event questions ("who won the nba finals?") have a gold valid only until the next occurrence. Past `valid_until` a *correct* model answering the new result is scored wrong against a stale gold — the same inversion the `unanswerable` split already guards with `expires_on`, now required for recurring-event fresh items too. The validator refuses to run (or auto-quarantines) any item past its `valid_until`.

Recurring-event items are a distinct sub-type (`temporal: recurring`): most valuable (they test whether the model knows *today's date* — the whole date-dependence finding) and fastest to rot (tightest expiry discipline).

## Three contamination paths — matched guards

| path | guarded by |
|---|---|
| event is in training data | **freshness floor (~60d)** — strong on its own (release→cutoff lag) |
| answer guessable from priors, no retrieval | **per-model no-tool floor at eval** — the only thing that catches this |
| model trained on *our benchmark* as it publishes/ages | **sealed holdout** — the other two do nothing here |

The no-tool floor is **guessability insurance**, not the primary freshness gate: recency does the heavy lifting for "is it post-cutoff"; the floor catches lucky-prior answers (favourite wins) that recency cannot; the sealed holdout covers benchmark self-leakage.

## Two oracles — never confuse them

| Axis | Question | Who answers it |
|---|---|---|
| **Truth / answerability** | what is the correct answer? is there one? | **frontier panel, with search, unanimous.** Small models excluded — a small model beating the whole frontier panel on a searchable question is a *flag on the item*, not model skill (broken-clock). |
| **Contamination / retrieval-need** | can *our shipped model* answer from memory? | the **actual scored model**, measured **at eval time** as retrieval-lift (with-tool − no-tool). NOT a curation filter — frontier over-knows; contamination is relative to the model being ranked. |

Consequences:
- **Gold admission:** the frontier panel (≥2 models, e.g. `openrouter:anthropic/claude-sonnet-5`, `openrouter:openai/gpt-5.6-luna`, + a third) run with search must **unanimously converge** on the gold. Disagreement → drop or human. Unanimity guards against one model's confident hallucination.
- **Curator ⟂ scored:** models that curate are disjoint from models on the leaderboard, else the board is selected to flatter them. Same rule as gold-verifier ⟂ judge.
- **Gold-verifier ⟂ judge:** the scoring judge (`gemini-3.5-flash`) must not also verify golds — shared blindspots would be invisible.

## Per-property probes

| Property | Probe | Admit rule |
|---|---|---|
| Gold is true | frontier panel + search | unanimous convergence on gold; else drop/human |
| **Read-required** (`answer_only_in_body`) | `snippet_leak`: run a query battery, check if gold appears in any snippet | admit only if gold in **no** snippet but **is** in a fetched body |
| **Multi-hop** (`dependent_search`) | `single_search` floor (per curator) | genuine only if one-search fails AND not memorable |
| **Unanswerable** | frontier+search can't find an answer **+** archived negative-evidence URL **+** valid `expires_on` | all three; human sign-off |
| Not a duplicate | `fact_cluster`: shared-URL + gold + embedding similarity → `fact_id` | variants share `fact_id`; human confirms; holdout split by fact |

Runtime backstop: even an admitted `answer_only_in_body` item is re-checked at scoring — a model that answered it **without a read** flags the item for retro-quarantine. Static battery + runtime path-audit together; neither alone suffices (query space is infinite).

## Free integrity gate (every confirmation run)

Auto-flag every item where a **ranked** model is correct but the **frontier reference** was wrong → almost always a bad gold or contamination. Cheapest high-yield detector; runs every time.

## Receipt schema (`verification/<id>.json`)

```json
{
  "id": "...", "verdict": "admit | drop | needs_human",
  "attributes": {"answer_only_in_body": false, "dependent_search": false, "memorable": null},
  "fact_id": null,
  "probes": {
    "snippet_leak": {"queries": [...], "gold_in_snippet": true, "matched_query": "...", "evidence": "..."},
    "gold_verify": {"panel": {...}, "unanimous": null},
    "single_search": {...}
  },
  "curator_panel": ["openrouter:anthropic/claude-sonnet-5", "..."],
  "human_signed": false
}
```

## Declared limitations (state, don't hide)

1. Consensus filtering keeps only items *clean for current models* → this is a **controlled probe**, not a representative sample of user queries. Report which one you claim.
2. Cleanliness decays as models improve; the filter is **re-run on any roster change** (re-anchoring). The dataset is a function of the pinned curator panel.
3. Query battery is verified over a defined query set, not all conceivable queries — hence the runtime backstop.

## Declared estimand — target size and distribution

We have no PocketPal query logs (privacy), so we cannot claim population-representativeness. Instead we **declare** strata + weights up front and enforce them as generator quotas; we report **both** macro (equal-weight per category) and weighted scores.

**Target size (distinct facts, the unit that counts — variants of one fact add no statistical n):**

| split | dev | holdout.sealed | rationale |
|---|---|---|---|
| fresh (primary) | ~300 | ~200 | holdout powered for ~7-pt paired confirmation; dev finer |
| unanswerable | ~60 | ~40 | fabrication rate to ±~0.10 |
| stable | ~40 | ~30 | |
| no_search | ~30 | ~20 | |
| **total** | **~430** | **~290** | **≈700 facts** |

Power basis: proportion CI half-width ≈ 0.98/√(facts); paired (McNemar) detection of a 10-pt gap needs ~200 facts, a 5-pt gap ~800. Current ~95 facts → need ~7× more.

**Category weights (generator quotas; a declared choice, not a measured population):**
current events/news ~20%, sports ~12%, tech/AI ~12%, business/finance ~12%, science/health ~12%, entertainment ~10%, politics/world ~10%, geography/local ~7%, other ~5%. Enforced as strata so we stop inheriting v3's sports skew by accident.

## Splits (built after admission)

`dev/` and `holdout.sealed/`, split by `fact_id` (never by prompt). Holdout is never inspected during design. Human signs off holdout golds against archived evidence before it is sealed.
