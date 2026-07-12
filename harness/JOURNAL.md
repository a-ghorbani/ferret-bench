
## 2026-07-12 — Adversarial review findings: disposition

Review (fresh-context subagent, repo-only) verified the harness, manifests, leaderboard reproduction, judge-vs-judge figure, key-stripping, and gate-failure transcripts; confirmed the two load-bearing conclusions (mechanism engagement; config rescue of qwen3-06b, Fisher p=0.0015). 11 findings; disposition:

1. **Stale pre-re-judge numbers in report/PROVENANCE** — ACCEPTED. All numbers regenerated from v2 scores.jsonl (screen shipped qwen = 0.70 not 0.75, rc8 0.65, snip-full 0.70, a6 2-dev 0.864, etc.); composites now over identical model sets (4-model shipped composite = 0.790, not the 2-model 0.875); PROVENANCE rewritten with v2 numbers + judge version.
2. **Rank-separation claim false** — ACCEPTED. Domination claim deleted; report now states n=44 resolves only gate-pass vs gate-fail; within-band CIs overlap (top vs qwen3-06b p=0.20); table order = point estimate only.
3. **Per-factor attribution contradicted by a1 at full n** — ACCEPTED. Report + PROVENANCE reframed to evidence tiers: the a2 BUNDLE is validated (pooled 162/176 vs 139/176, p=0.0004); per-factor rows marked screening-tier; a1 contradiction stated explicitly.
4. **"Decisively" language inside noise; tiebreak criterion changed post-hoc** — ACCEPTED. Language softened, Fisher tests cited (gemma-e2b a2-vs-shipped p=0.16 — reviewer's 0.31 was two-sided, ours one-sided; either way not significant); criterion change logged as amendment #8 (engagement saturated → correctness; same winner).
5. **Floor coverage misstated (2 models not 4; 3 memory-answerable Qs not 1)** — ACCEPTED. Counts corrected (the "4 models" conflated screen+ablate duplicates of the same 2 models); floors RUN for both rank-1 models (floorfix sweep); fr-tech-05 and fr-news-12 flagged alongside fr-news-03 for v2 demotion.
6. **Judge validation not reconstructible; precision thin** — ACCEPTED. Manual labels committed (analysis/judge-validation-manual-labels.json; 39/40 vs v2); CORRECT-precision extended: 60 judged-CORRECT fresh items sampled (seed 11), 60/60 contain gold/acceptable verbatim (analysis/judge-correct-precision-sample.json). Human-independence remains a limitation (stated).
7. **Ceiling-effect framing** — ACCEPTED. Exec summary rewritten to "saturates this benchmark"; harder/multi-hop items named as v2 priority.
8. **Unlogged protocol changes** — ACCEPTED. Amendments #6 (judge v2) and #7 (groundedness dropped, with rationale + limitation).
9. **Cherry-picked reads/token claims** — ACCEPTED. Per-model numbers now stated (reads: qwen ≤0.01/q, ministral 0.17–0.46/q; Brave tokens: ministral −24%, qwen +10%).
10. **Replay-cache wording oversold** — ACCEPTED. README + PROTOCOL wording aligned with the limitation (approximate comparability, capture-on-miss).
11. **Model identity in headline** — ACCEPTED. Exec summary + leaderboard now name huihui (abliterated) and mlabonne (fine-tune) variants explicitly.

No findings rebutted; none required invalidating runs. The freeze decision itself survived: same winner under corrected numbers (4-model a2 composite 0.920 vs shipped 0.790, p=0.0004).
