# Leaderboard — agentic web search, small on-device LLMs

Primary metric: **fresh-split correctness** (questions that require retrieval), judged 3-way vs gold. `[..]` = Wilson 90% CI. Full metric definitions in PROTOCOL.md §Metrics; every row traces to `runs/<run_id>/`.

| model | config | dataset | fresh ✓ | stable ✓ | engage | false-search | validity | avg turns | avg prompt tok | run |
|---|---|---|---|---|---|---|---|---|---|---|
| huihui-qwen35-2b | frozen | v1 | 0.98 [0.90,0.99] (n=44) | 0.97 [0.86,0.99] (n=30) | 1.00 | 0.20 | 1.00 | 1.9 | 1879 | 20260711-192204-confirm-frozen-huihui-qwen35-2b |
| qwen35-4b | frozen | v1 | 0.98 [0.90,0.99] (n=44) | 1.00 [0.92,1.00] (n=30) | 1.00 | 0.00 | 1.00 | 1.87 | 1909 | 20260711-192832-confirm-frozen-qwen35-4b |
| ministral-3-3b | frozen | v1 | 0.98 [0.90,0.99] (n=44) | 0.97 [0.86,0.99] (n=30) | 1.00 | 0.00 | 1.00 | 1.8 | 1495 | 20260711-195951-confirm-frozen-ministral-3-3b |
| ggml-org/gemma-4-31B-it-GGUF:Q8_0 | frozen | v1 | 0.98 [0.90,0.99] (n=44) | 1.00 [0.92,1.00] (n=30) | 1.00 | 0.00 | 1.00 | 1.73 | 1271 | 20260711-221729-confirm-frozen-gemma-4-31b-it-gguf |
| ggml-org/Qwen3.6-27B-GGUF:Q8_0 | frozen | v1 | 0.95 [0.87,0.98] (n=44) | 0.97 [0.86,0.99] (n=30) | 0.98 | 0.00 | 1.00 | 1.75 | 1786 | 20260711-201023-confirm-frozen-qwen3.6-27b-gguf |
| gemma-4-e2b | frozen | v1 | 0.93 [0.84,0.97] (n=44) | 1.00 [0.92,1.00] (n=30) | 1.00 | 0.07 | 1.00 | 1.73 | 1271 | 20260711-195433-confirm-frozen-gemma-4-e2b |
| lfm25-1.2b | frozen | v1 | 0.91 [0.81,0.96] (n=44) | 0.97 [0.86,0.99] (n=30) | 0.95 | 0.20 | 1.00 | 1.83 | 1347 | 20260711-200617-confirm-frozen-lfm25-1.2b |
| qwen3-06b | frozen | v1 | 0.89 [0.78,0.94] (n=44) | 0.90 [0.77,0.96] (n=30) | 0.98 | 0.33 | 1.00 | 1.83 | 1509 | 20260711-191120-confirm-frozen-qwen3-06b |
| qwen3-1.7b | frozen | v1 | 0.84 [0.73,0.91] (n=44) | 0.97 [0.86,0.99] (n=30) | 0.93 | 0.00 | 1.00 | 1.72 | 1364 | 20260711-191405-confirm-frozen-qwen3-1.7b |
| mlabonne-qwen3-4b | frozen | v1 | 0.84 [0.73,0.91] (n=44) | 0.97 [0.86,0.99] (n=30) | 0.91 | 0.07 | 1.00 | 1.72 | 1368 | 20260711-193812-confirm-frozen-mlabonne-qwen3-4b |
| gemma-3-1b-q4 | frozen | v1 | 0.02 [0.01,0.10] (n=44) | 0.80 [0.66,0.89] (n=30) | 0.00 | 0.00 | — | 1.0 | 121 | 20260711-195151-confirm-frozen-gemma-3-1b-q4 |
| hermes-3-3b | frozen | v1 | 0.02 [0.01,0.10] (n=44) | 0.93 [0.82,0.98] (n=30) | 0.00 | 0.00 | — | 1.0 | 115 | 20260711-200756-confirm-frozen-hermes-3-3b |
| gemma-3-4b | frozen | v1 | 0.00 [0.00,0.06] (n=44) | 0.20 [0.11,0.34] (n=30) | 0.00 | 0.00 | — | 1.0 | 121 | 20260711-195254-confirm-frozen-gemma-3-4b |
| phi-4-mini | frozen | v1 | 0.00 [0.00,0.06] (n=44) | 0.73 [0.59,0.84] (n=30) | 0.00 | 0.00 | — | 1.0 | 105 | 20260711-200231-confirm-frozen-phi-4-mini |
| smollm3-3b | frozen | v1 | 0.00 [0.00,0.06] (n=44) | 0.97 [0.86,0.99] (n=30) | 0.00 | 0.00 | — | 1.0 | 146 | 20260711-200412-confirm-frozen-smollm3-3b |
