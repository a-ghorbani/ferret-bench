# Leaderboard — agentic web search, small on-device LLMs

Primary metric: **fresh-split correctness** (questions that require retrieval), judged 3-way vs gold. `[..]` = Wilson 90% CI. Full metric definitions in PROTOCOL.md §Metrics; every row traces to `runs/<run_id>/`.

| model | config | dataset | fresh ✓ | stable ✓ | engage | false-search | validity | avg turns | avg prompt tok | run |
|---|---|---|---|---|---|---|---|---|---|---|
| openrouter:anthropic/claude-sonnet-5 | frozen | v2 | 0.98 [0.92,1.00] (n=53) | 1.00 [0.92,1.00] (n=30) | 1.00 | 0.00 | 1.00 | 1.72 | 3272 | 20260712-194938-confirm3-frozen-claude-sonnet-5 |
| openrouter:openai/gpt-5.6-sol | frozen | v2 | 0.98 [0.92,1.00] (n=53) | 1.00 [0.92,1.00] (n=30) | 1.00 | 0.00 | 1.00 | 1.91 | 1981 | 20260712-200227-confirm3-frozen-gpt-5.6-sol |
| qwen35-4b | frozen | v2 | 0.89 [0.80,0.94] (n=53) | 1.00 [0.92,1.00] (n=30) | 1.00 | 0.00 | 1.00 | 1.94 | 2391 | 20260712-191603-confirm3-frozen-qwen35-4b |
| ministral-3-3b | frozen | v2 | 0.81 [0.71,0.88] (n=53) | 1.00 [0.92,1.00] (n=30) | 1.00 | 0.00 | 1.00 | 1.86 | 1787 | 20260712-192728-confirm3-frozen-ministral-3-3b |
| qwen35-2b | frozen | v2 | 0.72 [0.61,0.81] (n=53) | 0.97 [0.86,0.99] (n=30) | 1.00 | 0.33 | 1.00 | 1.99 | 2163 | 20260712-191254-confirm3-frozen-qwen35-2b |
| huihui-qwen35-2b | frozen | v2 | 0.72 [0.61,0.81] (n=53) | 0.97 [0.86,0.99] (n=30) | 1.00 | 0.07 | 1.00 | 1.77 | 1795 | 20260712-194118-confirm3-frozen-huihui-qwen35-2b |
| gemma-4-e2b | frozen | v2 | 0.68 [0.57,0.77] (n=53) | 1.00 [0.92,1.00] (n=30) | 1.00 | 0.00 | 1.00 | 1.86 | 1494 | 20260712-192514-confirm3-frozen-gemma-4-e2b |
| lfm25-1.2b | frozen | v2 | 0.66 [0.55,0.76] (n=53) | 0.97 [0.86,0.99] (n=30) | 0.96 | 0.20 | 1.00 | 1.85 | 1378 | 20260712-193514-confirm3-frozen-lfm25-1.2b |
| mlabonne-qwen3-4b | frozen | v2 | 0.60 [0.49,0.71] (n=53) | 0.90 [0.77,0.96] (n=30) | 0.91 | 0.00 | 1.00 | 1.51 | 1169 | 20260712-194432-confirm3-frozen-mlabonne-qwen3-4b |
| qwen3-1.7b | frozen | v2 | 0.58 [0.47,0.69] (n=53) | 0.93 [0.82,0.98] (n=30) | 0.92 | 0.07 | 1.00 | 1.55 | 1224 | 20260712-191007-confirm3-frozen-qwen3-1.7b |
| qwen3-06b | frozen | v2 | 0.53 [0.42,0.64] (n=53) | 0.83 [0.70,0.92] (n=30) | 0.94 | 0.27 | 1.00 | 1.72 | 1402 | 20260712-190834-confirm3-frozen-qwen3-06b |
| hermes-3-3b | frozen | v2 | 0.08 [0.03,0.16] (n=53) | 0.93 [0.82,0.98] (n=30) | 0.00 | 0.00 | — | 1.0 | 116 | 20260712-193635-confirm3-frozen-hermes-3-3b |
| smollm3-3b | frozen | v2 | 0.04 [0.01,0.11] (n=53) | 0.97 [0.86,0.99] (n=30) | 0.00 | 0.00 | — | 1.0 | 153 | 20260712-193244-confirm3-frozen-smollm3-3b |
| gemma-3-1b-q4 | frozen | v2 | 0.02 [0.00,0.08] (n=53) | 0.83 [0.70,0.92] (n=30) | 0.00 | 0.00 | — | 1.0 | 122 | 20260712-192208-confirm3-frozen-gemma-3-1b-q4 |
| gemma-3-4b | frozen | v2 | 0.02 [0.00,0.08] (n=53) | 0.17 [0.08,0.30] (n=30) | 0.00 | 0.00 | — | 1.0 | 122 | 20260712-192318-confirm3-frozen-gemma-3-4b |
| phi-4-mini | frozen | v2 | 0.00 [0.00,0.05] (n=53) | 0.73 [0.59,0.84] (n=30) | 0.00 | 0.00 | — | 1.0 | 106 | 20260712-193034-confirm3-frozen-phi-4-mini |
