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

## 2026-07-15 — auto-resolution of the 28 needs_human items (resolve.py)

Ran `resolve.py`: cleared the human queue with an agentic panel + small-LLM judges, no human review. Owner rule applied — anything that did not cleanly settle was DROPPED.
- **9 resolved-admit, 0 dropped** across disputed / recurring / unanswerable.
- Golds overwritten (panel oracle): none.
- Rebuilt splits from ALL admitted items: dev=95 items/67 facts, holdout.sealed=46 items/28 facts (split by fact_id, ~30% facts to holdout).
- Method: disputed -> agentic panel re-run + small-LLM equality (Évian==Evian) -> converge = overwrite gold+admit else drop; recurring -> agentic next-occurrence lookup -> set valid_until (fallback +358d) + admit; unanswerable -> agentic try-hard panel -> all decline = admit NOT_FOUND, any specific answer = drop.

## 2026-07-15 — auto-resolution of the 28 needs_human items (resolve.py)

Ran `resolve.py`: cleared the human queue with an agentic panel + small-LLM judges, no human review. Owner rule applied — anything that did not cleanly settle was DROPPED.
- **22 resolved-admit, 3 dropped** across disputed / recurring / unanswerable.
- Golds overwritten (panel oracle): fr2-tech-08 '$91 billion'->'$91.0 billion, plus or minus 2%'; fr2-tech-14 'Salesforce's Fin acquisition'->'Salesforce buying Fin'.
- Rebuilt splits from ALL admitted items: dev=93 items/66 facts, holdout.sealed=47 items/28 facts (split by fact_id, ~30% facts to holdout).
- Method: disputed -> agentic panel re-run + small-LLM equality (Évian==Evian) -> converge = overwrite gold+admit else drop; recurring -> agentic next-occurrence lookup -> set valid_until (fallback +358d) + admit; unanswerable -> agentic try-hard panel -> all decline = admit NOT_FOUND, any specific answer = drop.

## 2026-07-15 — auto-resolution of the 28 needs_human items (resolve.py)

Ran `resolve.py`: cleared the human queue with an agentic panel + small-LLM judges, no human review. Owner rule applied — anything that did not cleanly settle was DROPPED.
- **11 resolved-admit, 0 dropped** across disputed / recurring / unanswerable.
- Golds overwritten (panel oracle): none.
- Rebuilt splits from ALL admitted items: dev=93 items/67 facts, holdout.sealed=49 items/29 facts (split by fact_id, ~30% facts to holdout).
- Method: disputed -> agentic panel re-run + small-LLM equality (Évian==Evian) -> converge = overwrite gold+admit else drop; recurring -> agentic next-occurrence lookup -> set valid_until (fallback +358d) + admit; unanswerable -> agentic try-hard panel -> all decline = admit NOT_FOUND, any specific answer = drop.

## 2026-07-15 — auto-resolution of the 28 needs_human items (resolve.py)

Ran `resolve.py`: cleared the human queue with an agentic panel + small-LLM judges, no human review. Owner rule applied — anything that did not cleanly settle was DROPPED.
- **27 resolved-admit, 1 dropped** across disputed / recurring / unanswerable.
- Golds overwritten (panel oracle): fr2-news-02 'Evian-les-Bains, France'->'Évian-les-Bains, France'; fr2-tech-08 '$91 billion'->'$91.0 billion, plus or minus 2%'; fr2-tech-14 'Salesforce's Fin acquisition'->'Salesforce buying Fin'; fr3-col-02 'Google Gemini'->'Siri AI powered by Apple and Google Gemini'; fr3-und-11 'macOS Golden Gate'->'macOS 27 Golden Gate'.
- Rebuilt splits from ALL admitted items: dev=93 items/67 facts, holdout.sealed=49 items/29 facts (split by fact_id, ~30% facts to holdout).
- Method: disputed -> agentic panel re-run + small-LLM equality (Évian==Evian) -> converge = overwrite gold+admit else drop; recurring -> agentic next-occurrence lookup -> set valid_until (fallback +358d) + admit; unanswerable -> agentic try-hard panel -> all decline = admit NOT_FOUND, any specific answer = drop.

## 2026-07-15 — resolver completion, gold-trim audit, and study-2 notes

- **Resolver ran to completion in the FOREGROUND.** Final receipt state: **142 admit / 1 drop / 0 needs_human**. `RESOLUTION_SUMMARY.md` written. The 12 remaining `needs_human` were all the slow `unanswerable_confirmed_*` items (agentic search per item); all admitted as unanswerable (gold=NOT_FOUND) after the try-hard panel declined.
- **Gold-trim audit (quality fix).** The resolver had adopted the panel's full verbose sentence as the new gold, which is too wordy for judging. Audited all 5 overwrites; every one was the SAME fact as the original, merely wordier, so the crisp original gold was kept and the verbose form preserved on each receipt as `resolved_gold_verbatim`:
  - fr2-news-02: `Evian-les-Bains, France` (verbatim `Évian-les-Bains, France`) — diacritic only
  - fr2-tech-08: `$91 billion` (verbatim `$91.0 billion, plus or minus 2%`)
  - fr2-tech-14: `Salesforce's Fin acquisition` (verbatim `Salesforce buying Fin`)
  - fr3-col-02: `Google Gemini` (verbatim `Siri AI powered by Apple and Google Gemini`)
  - fr3-und-11: `macOS Golden Gate` (verbatim `macOS 27 Golden Gate`)
  None were a genuinely different fact; no new value was adopted. Splits rebuilt after the trim: **dev 96 items / 67 facts, holdout.sealed 46 items / 28 facts**, no fact_id in both (counts shifted from pre-audit 93/49 because clustering keys partly on gold text).
- **study-2 notes (do NOT implement now).** Running `resolve.py` in the BACKGROUND repeatedly got auto-backgrounded/killed partway through the slow agentic `unanswerable` checks. For study-2: (a) the resolver needs a **retry-on-empty** wrapper so a killed/empty pass resumes cleanly from remaining `needs_human`; (b) the unanswerable check should be **single-shot-with-search, not full agentic**, to be fast and robust (the full ReAct loop per item is what makes the pass slow enough to get killed). Also fold the gold-trim (crisp canonical, keep verbatim) into the resolver itself so overwrites are crisp by construction.

## 2026-07-15 — generate.py + first-batch PILOT (coordinator changed scope: pilot-first, isolated)

Built `generate.py` (scalable candidate generator) and `admit_pilot.py` (isolated admission driver that reuses the real probe fns + resolvers but writes only pilot-scoped artifacts — no clustering/split/merge, so the verified pool is untouched). Mid-task the coordinator switched from the full ~150-fresh batch to a small PILOT (~24 fresh / 6 unans / 4 stable / 4 no_search) to review quality before scaling, kept isolated in `datasets/candidates/pilot.jsonl` + `verification/receipts_pilot/`.

**generate.py design.** Fresh items come from REAL events: brave search (replay-or-live) with window-dated per-category queries -> pool of real hits (title/snippet/url/date) -> frontier panel model extracts crisp Q&A supported by >=2 distinct-domain pool URLs with event_date in [2026-05-15, 2026-07-14); each fact gets 1-2 dated/undated/colloquial variants sharing a fact_id; recurring-annual questions get an undated variant to exercise temporal_guard's valid_until. Unanswerable = false-premise/unfindable about real entities with negative-evidence URLs + expires_on. Stable/no_search from model knowledge. Checkpointed per (split,category) chunk; every item appended immediately.

**What actually happened — two blockers.**
1. **OpenRouter credits exhausted** (total_usage 560.15 ≥ total_credits 560, ~$0 left). Calls now 402 with a shrinking affordable-token budget (1747 -> 1325 -> 1048 as the run drained the last sliver). gpt-5.6-luna failed on tech/business/geography; sonnet failed on other/unanswerable/stable. This is a hard external blocker for the pinned panel (sonnet-5 + gpt-5.6-luna; gemini forbidden as verifier).
2. **JSON truncation bug** (found + fixed): higher-n categories (news=5, sports/tech/science=3) asked for 6 facts+variants which overran max_tokens=2000, so the whole array failed to parse and the chunk kept 0. Politics (n=2 -> 3 facts) fit and produced 2 clean facts. Fixed `_parse_json_array` with a brace-depth object salvager that recovers every complete object from a truncated array; also stopped marking a chunk "done" when the gen call itself errors (so a re-run resumes the gaps). Reset `pilot.state.json` to keep only `fresh:politics` so a credit-restored resume refills the empty categories.

**Pilot generated (partial, credit-limited): 2 fresh facts / 6 items**, both politics (G7-2026-Evian): high quality — crisp golds, real independent sources (consilium.europa.eu / PBS / Reuters / NYT), in-window dates, sensible dated/undated/colloquial variants.

**Isolated admission (real receipts in `verification/receipts_pilot/`): 3 admit, 3 needs_human.**
- `g1f-politics-02` (Japan PM = Sanae Takaichi) + 2 variants -> **admit** (gold_confirmed_and_fresh).
- `g1f-politics-01` (G7 city = Evian-les-Bains) + 2 variants -> **needs_human / gold_disputed**: BOTH panel models answered "Évian-les-Bains" (accent é), but the reused `gold_verify._norm` strips the accented é ("évian"->"vian") so `_matches` spuriously returns False. This is a real accent-insensitivity in the probe matcher; `resolve.py`'s small-LLM equality judge (Évian==Evian) is exactly designed to recover it on the agentic re-run — but that path is agentic (credit-heavy) so it was not run under the exhausted balance. Snippet_leak flagged gold-in-snippet (not read-required) and temporal_guard passed (28d old, fresh).

STOPPED per coordinator for pilot review. NOT re-split, NOT merged. Full batch remains blocked on (a) OpenRouter credit top-up and (b) confirming the salvage/quorum fixes on a fresh run.

## 2026-07-15 (overnight) — pilot reviewed; BLOCKED on OpenRouter credits

Owner asleep; authorized me to review the pilot, fix bugs, and scale if clean.

PILOT (isolated, committed 6dbdfe6): only 2 fresh facts generated (G7-2026-Evian, Japan PM Takaichi)
before the run stalled. Quality of what generated is GOOD — real independent sources, crisp golds,
sensible dated/undated/colloquial variants. Admission: 3 admit, 3 needs_human (the Évian accent bug).

BUGS:
1. FIXED by me — gold_verify._norm stripped accents ('Évian'->'vian') so any accented gold spuriously
   disputed. Now NFKD-folds ('Évian'->'evian'); verified José/Évian match, controls hold. Propagates to
   gold_verify_agentic + resolve (they import it). This is the "study-2" matcher weakness, fixed now.
2. Generator JSON-truncation bug — worker already fixed (_salvage_objects brace-depth parser + resumable
   state); reviewed, looks sound. Not re-run (blocked).

BLOCKER (hard, user-only): OpenRouter total_credits 560 / total_usage 560.17 -> remaining -0.17.
1-token calls slip through a grace but real panel/eval runs will 402. Cannot scale generation, cannot
run eval (both the frontier panel AND the gemini judge are OpenRouter). NOT starting a big run that
would fail midway. Did NOT do a premature partial eval — the dataset will change once we scale, so
eval belongs AFTER scaling.

STATE: blocked_on = "top up OpenRouter credits". On top-up: re-run full ~24 pilot -> review -> scale to
~700 -> eval on dev (holdout stays sealed). Everything staged; nothing pushed.

## 2026-07-16 — recommended cost-optimized model setup wired in + smoke-tested (credits restored ~$100)

Config (data-driven from OpenRouter Artificial Analysis agentic_index):
- Panel oracle: gpt-5.6-luna (agentic 45.6) + z-ai/glm-5.2 (43.1) — near-frontier agentic at ~1/3 price.
- Judge + drafting + equality: deepseek/deepseek-v4-flash (beats gpt-4o-mini on every axis + price).
- Dropped: gpt-4o-mini (agentic 1.0, obsolete), gemini-3.5-flash judge (mediocre agentic + overpriced).

KEY FINDING — glm-5.2 (and deepseek-v4) are REASONING models. Handling is role-dependent:
- reasoning:{enabled:False} is the clean off-switch (effort:'low' does NOT work — still truncates).
- JUDGE/DRAFT: reasoning OFF — simple tasks, cheap (glm answered in 6 tokens vs 1589). Applied.
- ORACLE PANEL: reasoning ON + max_tokens 2048. Reasoning-OFF made glm hallucinate a prior
  ("Real Madrid" for the CL winner instead of reading "PSG" from results). Accuracy > cost for the
  oracle. Cost: glm burns 400-1600 reasoning tok/call (real, but affordable in $100 budget).

SMOKE TEST (8 single-shot + 2 agentic multi-hop):
- Clean convergence on good items (Colombia, Fed, PSG, Knicks, Evian). Accent fix confirmed (Évian match).
- Agentic: glm-5.2 drives the ReAct loop fine (3-4 turns, multi-search); converged with luna on both
  multi-hop golds (Elon Musk, Isao Teshirogi).
- Disputes flagged (Nvidia: panel leans $78B vs our $91B gold; macOS: Tahoe vs our Golden Gate) —
  the oracle correctly questioning v3 golds that may be wrong. Unanimity nets glm's occasional
  empty-on-pathological-item into a harmless dispute.
Verdict: recommended setup VALIDATED and working. Ready to scale generation on credit restore.

## PENDING (blocked on HuggingFace outage 2026-07-16) — models to add when HF is back
HF API returning 504 on all calls (confirmed by owner). Deferred downloads:
1. LFM2-2.6B Q4_K_M  — repo likely LiquidAI/LFM2-2.6B-GGUF (unverified; 504'd). 
2. Bonsai 27B Q1_0.
For each, when HF recovers: (a) hf download the Q<x> gguf into ~/.lmstudio/models/,
(b) add alias to ~/llama-models.ini with model=<path> (filename must contain the quant so
resolve_weights can read it), (c) add the alias line to harness/models-confirm.txt.
Do NOT add the roster line before the file exists — eval would fail on a missing gguf.

## 2026-07-16 — drop-on-dispute (disable gold-overwrite recovery)
Pilot showed resolve's gold-overwrite "recovery" is net-harmful: recovered 6 fresh golds but at
least one wrong+inconsistent (entertainment-02 base admitted as "Morgan Wallen" while its own
variants dropped; panel actually split Post Malone/Morgan Wallen). resolve_disputed now DROPS
disputed/uncertain golds outright — no agentic re-run, no overwrite. Cheaper (skips the re-run) and
can't break fact_id consistency. resolve keeps only its safe jobs: unanswerable-confirm + equality
(Évian==Evian) + recurring valid_until lookup. Rationale: generation is cheap; generate another fact
rather than rescue a doubtful one.

Note (diagram correction): the eval judge (deepseek-v4-flash) is NOT part of curation. It runs in the
separate EVAL phase, grading the 12 on-device models' answers vs the curated gold. Curation golds are
set by the panel (luna+glm-5.2); deepseek appears in curation only as resolve's equality checker.
