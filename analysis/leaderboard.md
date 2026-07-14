# Leaderboard — agentic web search, small on-device LLMs

Primary metric: **fresh-split correctness** (questions that require retrieval), judged 3-way vs gold. `[..]` = Wilson 90% CI. Full metric definitions in PROTOCOL.md §Metrics; every row traces to `runs/<run_id>/`.

| model | config | dataset | fresh ✓ | stable ✓ | engage | false-search | validity | avg turns | avg prompt tok | run |
|---|---|---|---|---|---|---|---|---|---|---|
| openrouter:anthropic/claude-sonnet-5 | frozen | v3 | 0.98 [0.93,0.99] (n=85) | 1.00 [0.92,1.00] (n=30) | 1.00 | 0.00 | 1.00 | 1.83 | 3211 | 20260714-160407-confirm4-frozen-claude-sonnet-5 |
| openrouter:openai/gpt-5.6-sol | frozen | v3 | 0.98 [0.93,0.99] (n=85) | 1.00 [0.92,1.00] (n=30) | 1.00 | 0.00 | 1.00 | 2.03 | 2051 | 20260714-162732-confirm4-frozen-gpt-5.6-sol |
| qwen35-4b | frozen | v3 | 0.93 [0.87,0.96] (n=85) | 1.00 [0.92,1.00] (n=30) | 1.00 | 0.00 | 1.00 | 2.1 | 2740 | 20260714-152532-confirm4-frozen-qwen35-4b |
| ministral-3-3b | frozen | v3 | 0.82 [0.75,0.88] (n=85) | 0.93 [0.82,0.98] (n=30) | 1.00 | 0.07 | 1.00 | 2.04 | 2051 | 20260714-154122-confirm4-frozen-ministral-3-3b |
| qwen35-2b | frozen | v3 | 0.72 [0.63,0.79] (n=85) | 0.97 [0.86,0.99] (n=30) | 1.00 | 0.47 | 1.00 | 2.06 | 2318 | 20260714-152028-confirm4-frozen-qwen35-2b |
| lfm25-1.2b | frozen | v3 | 0.72 [0.63,0.79] (n=85) | 0.90 [0.77,0.96] (n=30) | 0.98 | 0.20 | 1.00 | 1.85 | 1379 | 20260714-155325-confirm4-frozen-lfm25-1.2b |
| gemma-4-e2b | frozen | v3 | 0.71 [0.62,0.78] (n=85) | 0.97 [0.86,0.99] (n=30) | 0.94 | 0.00 | 1.00 | 1.88 | 1530 | 20260714-153804-confirm4-frozen-gemma-4-e2b |
| qwen3-06b | frozen | v3 | 0.60 [0.51,0.68] (n=85) | 0.93 [0.82,0.98] (n=30) | 0.94 | 0.53 | 1.00 | 1.87 | 1581 | 20260714-151546-confirm4-frozen-qwen3-06b |
| qwen3-1.7b | frozen | v3 | 0.60 [0.51,0.68] (n=85) | 0.93 [0.82,0.98] (n=30) | 0.78 | 0.00 | 1.00 | 1.55 | 1203 | 20260714-151652-confirm4-frozen-qwen3-1.7b |
| gemma-3-1b-q4 | frozen | v3 | 0.06 [0.03,0.12] (n=85) | 0.83 [0.70,0.92] (n=30) | 0.00 | 0.00 | — | 1.0 | 121 | 20260714-153323-confirm4-frozen-gemma-3-1b-q4 |
| smollm3-3b | frozen | v3 | 0.05 [0.02,0.10] (n=85) | 0.97 [0.86,0.99] (n=30) | 0.00 | 0.00 | — | 1.0 | 152 | 20260714-154933-confirm4-frozen-smollm3-3b |
| hermes-3-3b | frozen | v3 | 0.04 [0.01,0.09] (n=85) | 0.93 [0.82,0.98] (n=30) | 0.00 | 0.00 | — | 1.0 | 115 | 20260714-155602-confirm4-frozen-hermes-3-3b |
| phi-4-mini | frozen | v3 | 0.02 [0.01,0.07] (n=85) | 0.90 [0.77,0.96] (n=30) | 0.00 | 0.00 | — | 1.0 | 105 | 20260714-154611-confirm4-frozen-phi-4-mini |
| gemma-3-4b | frozen | v3 | 0.01 [0.00,0.05] (n=85) | 0.20 [0.11,0.34] (n=30) | 0.00 | 0.00 | — | 1.0 | 121 | 20260714-153512-confirm4-frozen-gemma-3-4b |
