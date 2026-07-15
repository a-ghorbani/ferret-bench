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
