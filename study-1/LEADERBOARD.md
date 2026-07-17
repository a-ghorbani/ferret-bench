# study-1 leaderboard — on-device agentic web search

Dev split. **fresh** = retrieval accuracy at fact level (variants aggregated per fact), 90% Wilson CI over 80 facts. **memory** = stable-split accuracy (no search needed). **searched** = share of fresh items where the model issued a query. Config: frozen. Judge: deepseek-v4-flash. Golds: gpt-5.6-luna + glm-5.2 (disjoint from judge). ★ = accuracy-vs-size Pareto frontier.

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
| gemma-3-4b | 0% | 0.06 | 0.00 | — |
| gemma-3-1b-q4 | 0% | 0.74 | 0.00 | — |
| phi-4-mini | 0% | 0.84 | 0.00 | — |
| smollm3-3b | 0% | 0.97 | 0.00 | — |
| hermes-3-3b | 0% | 0.94 | 0.00 | — |

Zero searches → zero retrieval, while *memory* stays high: the GGUF chat template never delivered the tool schema. A packaging failure, not a capability one.
