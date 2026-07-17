# study-1 leaderboard — web-search agentic config, on-device models

Dataset: study-1 dev (clean, rebuilt). Metric: fresh-split accuracy, **fact-level** (variants
aggregated per fact_id), 90% Wilson CI over **80 fresh facts**. Config: frozen. Judge: deepseek-v4-flash.
Panel that curated golds: gpt-5.6-luna + z-ai/glm-5.2 (disjoint from judge). Anchor 2026-07-14.

## Ranking (gate-passers — received the tool schema and did agentic search)

| # | model | fresh acc | 90% CI | searched |
|---|---|---|---|---|
| 1 | qwen35-4b | 0.87 | [0.80, 0.92] | 399/399 |
| 2 | ministral-3-3b | 0.84 | [0.76, 0.89] | 399/399 |
| 2 | gemma-4-e2b | 0.84 | [0.76, 0.89] | 399/399 |
| 4 | bonsai-27b-q1 | 0.83 | [0.76, 0.89] | 376/399 |
| 5 | qwen35-2b | 0.80 | [0.72, 0.86] | 399/399 |
| 6 | lfm2-2.6b | 0.76 | [0.66, 0.82] | 388/399 |
| 7 | lfm25-1.2b | 0.74 | [0.66, 0.82] | 383/399 |
| 7 | qwen3-06b | 0.74 | [0.65, 0.81] | 375/399 |
| 9 | qwen3-1.7b | 0.72 | [0.64, 0.80] | 369/399 |

**The top five (0.80–0.87) are one statistical cluster** — all CIs overlap the leader's, so this
ranks *tiers*, not fine positions. Separating them needs ~400 facts (dataset is growable).

## Gate failures — EXCLUDED (tool schema never rendered; not a capability result)

gemma-3-4b, gemma-3-1b-q4, phi-4-mini, smollm3-3b, hermes-3-3b — `schema_not_rendered`=399/399,
0 searches. The llama.cpp/GGUF tool-calling path never delivered the search tools to these packages,
so they could not search. Reportable as a packaging/template failure, NOT model weakness.

## Notes / limitations
- Ranking is on **dev**; the sealed holdout (58 facts) is reserved for a single confirmation run.
- **No fabrication claims possible** — dev has only 4 unanswerable facts (pool-limited generation).
- bonsai-27b-q1 is a 1-bit quant and still top-cluster — a genuinely surprising result worth a look.
- Composition skew is declared (sports/tech/business-heavy, June-heavy); scope = crisp-fact retrieval.
