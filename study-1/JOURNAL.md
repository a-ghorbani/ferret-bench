# study-1 lab notebook

## 2026-07-15 — clean-room kickoff, data curation first

Decision (with owner): do NOT wipe or rewrite. Quarantine v1–v3 as exploratory; start study-1
clean-room beside it. Reuse v3 questions/golds/sources as a CANDIDATE POOL — discard only the
unverified tier labels (kept as `origin_tier` provenance). Start with data curation because the
dataset is the root: "read-required 90% with zero reads" was an unverified author label.

Design agreed (see CURATION-SPEC.md):
- Two oracles, never confused: frontier-unanimous panel (with search) = TRUTH/answerability;
  per-scored-model retrieval-lift AT EVAL = contamination. Frontier over-knows, so it must NOT
  gate "retrieval-required".
- Curator panel ⟂ leaderboard models; gold-verifier ⟂ scoring judge (gemini).
- Drop-freely: keep only items whose property is unambiguously exhibited. Dropping costs yield,
  not validity.
- Difficulty is an OUTCOME measured post-seal, never an authored tier.
- Non-amendable firewall: this spec freezes before the first confirmation run; a change after
  freeze opens study-2, never amends study-1.

### snippet_leak probe (mechanical, reuses providers.search) — first result on 85 fresh candidates
Gold-in-snippet by OLD tier label (naive question-as-query battery = LOWER BOUND):
  T1 32/33 (97%) | T2 "read-required" 20/31 (65%) | T3 33% | T4 "multi-hop" 10/12 (83%)
=> tier taxonomy is upside-down. The "hardest" tier leaks the gold into a single snippet MORE
than the "read-required" tier. C1/C2 confirmed with numbers on the real data. Only T3's 6
non-leaking items look like genuine body-only reads.

### gold_verify probe (frontier panel: claude-sonnet-5 + gpt-5.6-sol, single-shot w/ search)
Pilot 8 items: 6 gold_confirmed, 2 flagged (both correct):
- fr3-und-02/03 (undated natural): panel w/ fresh search -> Knicks/Hurricanes = our gold. These
  are the exact items Qwen3.5-4B failed by returning last-year champions. Gold right, model wrong.
- fr3-col-02 (colloquial): panel split -> ambiguous question, correct human flag.
- fr2-tech-17 (T4): both said "don't know" from ONE search block.

FINDING (probe design): single-shot gold-verify confirms single-search golds but UNDER-POWERS
multi-hop. T3/T4 candidates need an AGENTIC gold-verify (panel with real search tools, multi-turn).
Next: add agentic mode, then full 143 admission pass, then fact_id clustering + dev/holdout split.

## 2026-07-15 (cont) — temporal guards added

Owner raised: is there a guard that fresh events aren't too old (1-2 months)? There was NOT —
assemble.py only checked event_date < anchor, never recency. v3 satisfied ~60d by hand only.
Also (prior turn): undated recurring-event items had expires_on=(none) -> silent stale-gold rot.

Agreed reasoning: recency window is a STRONG contamination guard, not a weak proxy — training
data freezes months before release, so a <=60d event is post-cutoff for essentially all models.
No-tool floor is reframed as GUESSABILITY insurance (lucky-prior answers recency can't catch),
not the primary freshness gate. Sealed holdout covers benchmark self-leakage. Three paths, three
matched guards — written into CURATION-SPEC §Temporal validity + §Three contamination paths.

temporal_guard.py (mechanical, dates only) on 85 fresh candidates, anchor 2026-07-14, window 60d:
  stale (>60d): 0   |   recurring needing valid_until: 9 (nba/stanley/UCL/french open/... )  |  clean: 76
The 9 recurring items are the silent-rot risk v3 shipped unguarded; each proposed valid_until
~+1yr, flagged HUMAN-confirm. Pipeline proposes expiry, never auto-sets a gold's window.

## 2026-07-15 — full admission pass (validate.py orchestrator)

Ran `study-1/validate.py` over all 143 candidates (anchor 2026-07-14, provider brave,
mode replay-or-live, panel = claude-sonnet-5 + gpt-5.6-sol). One receipt per item in
`verification/receipts/<id>.json`. New probe added: `probes/gold_verify_agentic.py` — for
multi-hop candidates (origin_tier T3/T4, 21 fresh items) it runs the SHIPPED ReAct loop
(harness/agent_loop.run_agent) with real web_search+read_url instead of single-shot snippets,
then matches the final answer to gold. Verified live: e.g. fr2-news-12 ran 2 turns / 2 searches
per model and both converged on the gold. T1/T2 fresh + all stable used single-shot gold_verify.

Headline: **115 admit / 0 drop / 28 needs_human** (143 total).
  fresh   85 -> 70 admit, 15 needs_human, 0 drop
  stable  30 -> 30 admit
  unanswerable 13 -> 13 needs_human (all genuinely unanswerable: panel unanimously declined WITH
                    search; none answerable, so 0 drops. Await human negative-signoff.)
  no_search 15 -> 15 admit (mechanical false-positive probes)

Splits by fact_id (never by prompt): 81 distinct admitted fact_ids -> dev 81 items / 57 facts,
holdout.sealed 34 items / 24 facts (~30% of facts). Zero fact_id overlap (partitioned by fact).

needs_human queue (28): 13 unanswerable negatives, 9 recurring-event items needing valid_until,
5 gold_disputed (panel agrees on a different answer), 1 gold_uncertain (panel split).

Two things the human must decide (recorded, not auto-resolved — no methodology change mid-run):
1. Two disputed golds look genuinely WRONG, not matcher noise:
   - fr3-und-11 "what's the new macos called?" our gold 'macOS Golden Gate' vs panel-unanimous
     'macOS 26 Tahoe'.
   - fr2-tech-08 Nvidia next-quarter forecast: our gold '$91 billion' vs panel '$78.0 billion'.
2. Three of the six disputes are gold-MATCHER artifacts, effectively true matches the substring/
   ascii normalizer missed — human should confirm-admit, not fix:
   - fr2-news-02 'Evian-les-Bains' vs panel 'Évian-les-Bains' (diacritic dropped by [^a-z0-9] norm).
   - fr2-tech-14 both models DO say "Salesforce buying Fin first" (= our gold) but word-order
     defeats the substring match -> falsely gold_uncertain.
   - fr2-news-08 / fr3-col-02 the panel declined from snippets (NObodyKNOWS) rather than disputing;
     single-shot snippet limitation, human review.
   The normalizer is unicode-naive and substring-based; leaving it unchanged per "implement, don't
   redesign" — flagged for study-2.

Clustering caveat (surfaced in HUMAN_QUEUE §5, 15 multi-item clusters): comparison-style questions
("which vote happened first, Malta's or Colombia's?") share source_urls with BOTH events and, via
union-find, transitively bridge two distinct facts into one cluster (e.g. fact_001 merges Malta +
Colombia items). This OVER-merges — the safe direction for holdout (never leaks a variant across
dev/holdout) but it understates the independent-fact count. Human should split bridged clusters.
No ambiguous near-threshold (0.80-0.85) pairs were found.
