# study-1 leaderboard — on-device agentic web search

Dev split. **fresh** = retrieval accuracy at fact level (variants aggregated per fact), 90% Wilson CI over 80 facts. **memory** = stable-split accuracy (no search needed). **searched** = share of fresh items where the model issued a query. Config: frozen. Judge: deepseek-v4-flash. Golds drafted by deepseek-v4-flash (tech/business/geography by gpt-5.6-luna), then **verified** by a gpt-5.6-luna + glm-5.2 panel — the panel is disjoint from the judge, the drafter is not. ★ = accuracy-vs-size Pareto frontier.

> **Read this as bands, not ranks.** Every row is a single draw. Measured run-to-run SD is 0.020 (k=5, 5 models), so a difference between two single runs carries a 90% band of **±0.047** — wider than the #1-to-#4 spread. Under k=5 replication only **qwen35-2b** separates from the leader; ranks 1–4 are one statistical band. See `../FINDINGS-2026-07-22-measurement-precision.md`.

| # | model | fresh | 90% CI | searched | memory | size | quant | ★ |
|---|---|---|---|---|---|---|---|---|
| 1 | qwen35-4b | 0.87 | [0.80,0.92] | 100% | 0.97 | 2.71 GB | Q4_K_M | ★ |
| 2 | ministral-3-3b | 0.84 | [0.76,0.89] | 100% | 1.00 | 2.15 GB | Q4_K_M | ★ |
| 3 | gemma-4-e2b | 0.84 | [0.76,0.89] | 100% | 1.00 | 3.43 GB | Q4_K_M |  |
| 4 | bonsai-27b-q1 | 0.83 | [0.76,0.89] | 94% | 0.94 | 3.8 GB | Q1_0 |  |
| 5 | qwen35-2b | 0.80 | [0.72,0.86] | 100% | 0.90 | 1.27 GB | Q4_K_M | ★ |
| 6 | lfm2-2.6b | 0.76 | [0.66,0.82] | 97% | 0.97 | 1.56 GB | Q4_K_M |  |
| 7 | lfm25-1.2b | 0.74 | [0.66,0.82] | 96% | 1.00 | 0.73 GB | Q4_K_M | ★ |
| 8 | qwen3-06b | 0.74 | [0.65,0.81] | 94% | 0.65 | 0.48 GB | Q4_K_M | ★ |
| 9 | qwen3-1.7b | 0.72 | [0.64,0.80] | 92% | 0.90 | 1.67 GB | Q6_K |  |

## Gate failures — unranked

| model | searched | memory | fresh | quant |
|---|---|---|---|---|
| hermes-3-3b | 0% | 0.94 | 0.073 | — |
| smollm3-3b | 0% | 0.97 | 0.055 | — |
| gemma-3-1b-q4 | 0% | 0.74 | 0.023 | — |
| phi-4-mini | 0% | 0.84 | 0.017 | — |
| gemma-3-4b | 0% | 0.06 | 0.005 | — |

Zero searches → near-zero retrieval, while *memory* stays high: the GGUF chat template never delivered the tool schema. A packaging failure, not a capability one.

*Correction (2026-07-22): this column previously read `0.00` for all five. Those values were hand-entered — `export_site.py` emits no `fresh` field for gate-failures — and the run data shows non-zero scores. The fresh split is therefore not fully retrieval-required: **24 of 80 fresh facts** are answered correctly by at least one tool-less model. The conclusion survives (ranking moves ≤0.03 on the memory-free subset) but the board previously overstated it.*
