# Web-dev handoff — replace the v3 web-search eval page with study-1

The current pocketpal.dev/evals/web-search page renders the **v3** benchmark, which a methodology audit found unsound (author-labelled difficulty tiers that didn't hold, pseudoreplication, a fabrication split too small to support claims). **study-1** is a from-scratch rebuild on a dataset that verifies its own labels. This handoff swaps the page over.

## Data source (the ONLY inputs you render)

- `study-1/analysis/site/leaderboard.json` — machine-readable results (rows, gate_failures, pareto block, dataset/judge/config metadata).
- `study-1/page_content.json` — all interpretive prose (headline cards, limitations, config notes, metric definitions). **Prose lives here, not in the renderer.**

Regenerate the JSON anytime with `python3 study-1/export_site.py`.

## What CHANGES from the v3 page

**REMOVE (these constructs are gone in study-1):**
- **Difficulty tiers (T1–T4)** and the tier-gradient chart. study-1 has no tiers — difficulty is not an author label.
- **Fabrication cards / hallucination-rate columns.** The unanswerable split is only 4 questions / 3 facts here — too small to state a rate. Do not show a fabrication number.
- **Frontier anchors** (Claude/GPT rows). study-1's leaderboard is on-device models only; the frontier models are the *gold-curation panel*, not competitors.

**ADD (new to study-1):**
1. **Gate-failure section** — `leaderboard.json.gate_failures[]`: 5 models that scored 0 because the GGUF chat template never delivered the tool schema (`searched 0%`, `memory` high, `fresh 0.00`). Render as a *separate, clearly-labelled* block below the ranked table — "unranked: never received the search tools." This is a packaging result, NOT a capability ranking. (This is the exact mistake the v3 page made and we're correcting — don't rank these as "bad models.")
2. **Per-model columns that make the story self-evident** (no explanatory notes needed — the columns are the story): `fresh` (retrieval accuracy) + 90% CI, `searched %` (`searched.searched_frac`), `memory` (`stable.rate`), `size` (`file_size_gb`), `quant`, and a **Pareto ★** (`pareto_frontier: true`).
3. **Accuracy-vs-size Pareto view** — `leaderboard.json.pareto` block (x=`file_size_gb`, y=`fresh.rate`, `frontier=[...]`). A scatter with the frontier highlighted is the on-device money chart. Optional but recommended: "best model per size budget" callouts (for a phone with X GB free, ship model Y).

**KEEP:** the ranked leaderboard table, config-values panel, limitations list, methodology footer.

## The story the page should tell (all backed by columns, not prose)

- **7 gate-passers ranked; 5 packages never got the tools.** The gate-failure block is a headline finding, not a footnote.
- **The top five (0.80–0.87) are one statistical cluster** — every 90% CI overlaps the leader's. Present as a *tier*, not a hard 1-2-3-4-5. Do not imply qwen35-4b is decisively #1.
- **A 1-bit 27B (bonsai) holds up** in the top cluster — surprising for the bit-width. Its `searched 94%` + mid `fresh` + biggest `size` + no ★ tell the nuance without a caption.
- **Small models punch up:** gemma-4-e2b (2B) ties ministral-3-3b; qwen3-06b (0.48 GB) matches lfm25-1.2b. The Pareto view is where this lands.

## Honest caveats (verbatim from page_content.limitations — show them, don't soften)

- **Dev split only, 80 fresh facts** — neighbouring models sit within noise; separating the top cluster needs ~400 facts (dataset is growable).
- **No fabrication claims** — unanswerable split too small.
- **Composition skew declared** — sports/tech/business-heavy, June-2026-heavy; scope is crisp-fact retrieval.
- **Holdout unused** — the config was frozen before any dev run, so dev is itself the out-of-sample test; the sealed holdout is reserved for a future confirmation.
- **Workstation quality, not on-device latency/battery** — those are unmeasured here.

## Practical notes

- The numbers in `LEADERBOARD.md` (human table) and `leaderboard.json` are generated from the same runs and agree; if they ever diverge, `export_site.py` is the source of truth.
- Nothing here changes the v3 files (`analysis/site/leaderboard.json`, `harness/page_content.json`) — study-1 is self-contained under `study-1/`.
- The repo is not yet pushed with study-1; coordinate the push with the owner before deploying (a gitleaks pass on new history is expected, though the record-replay cache is verified key-redacted).
