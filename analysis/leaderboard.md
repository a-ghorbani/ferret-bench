# Leaderboard — agentic web search, small on-device LLMs

Primary metric: **fresh-split correctness** (questions that require retrieval), judged 3-way vs gold. `[..]` = Wilson 90% CI. Full metric definitions in PROTOCOL.md §Metrics; every row traces to `runs/<run_id>/`.

| model | config | dataset | fresh ✓ | stable ✓ | engage | false-search | validity | avg turns | avg prompt tok | run |
|---|---|---|---|---|---|---|---|---|---|---|
| openrouter:openai/gpt-5.6-sol | frozen | v2 | 0.98 [0.92,1.00] (n=53) | 1.00 [0.92,1.00] (n=30) | 1.00 | 0.00 | 1.00 | 1.9 | 2031 | 20260712-164212-confirm2-frozen-gpt-5.6-sol |
| openrouter:anthropic/claude-sonnet-5 | frozen | v2 | 0.94 [0.87,0.98] (n=53) | 1.00 [0.92,1.00] (n=30) | 1.00 | 0.00 | 1.00 | 1.73 | 3156 | 20260712-151033-confirm2-frozen-claude-sonnet-5 |
| qwen35-4b | frozen | v2 | 0.92 [0.84,0.97] (n=53) | 1.00 [0.92,1.00] (n=30) | 1.00 | 0.00 | 1.00 | 2.06 | 2662 | 20260712-142549-confirm2-frozen-qwen35-4b |
| huihui-qwen35-2b | frozen | v2 | 0.83 [0.73,0.90] (n=53) | 1.00 [0.92,1.00] (n=30) | 1.00 | 0.07 | 1.00 | 2.03 | 2332 | 20260712-145935-confirm2-frozen-huihui-qwen35-2b |
| ministral-3-3b | frozen | v2 | 0.81 [0.71,0.88] (n=53) | 1.00 [0.92,1.00] (n=30) | 1.00 | 0.00 | 1.00 | 1.86 | 1787 | 20260712-161006-confirm2-frozen-ministral-3-3b |
| gemma-4-e2b | frozen | v2 | 0.77 [0.67,0.85] (n=53) | 1.00 [0.92,1.00] (n=30) | 0.98 | 0.07 | 1.00 | 1.91 | 1598 | 20260712-160137-confirm2-frozen-gemma-4-e2b |
| lfm25-1.2b | frozen | v2 | 0.66 [0.55,0.76] (n=53) | 0.97 [0.86,0.99] (n=30) | 0.96 | 0.20 | 1.00 | 1.85 | 1378 | 20260712-162002-confirm2-frozen-lfm25-1.2b |
| qwen35-2b | frozen | v2 | 0.64 [0.53,0.74] (n=53) | 0.87 [0.73,0.94] (n=30) | 1.00 | 0.20 | 1.00 | 2.02 | 2298 | 20260712-155154-confirm2-frozen-qwen35-2b |
| mlabonne-qwen3-4b | frozen | v2 | 0.64 [0.53,0.74] (n=53) | 0.93 [0.82,0.98] (n=30) | 0.94 | 0.00 | 1.00 | 1.69 | 1396 | 20260712-162352-confirm2-frozen-mlabonne-qwen3-4b |
| qwen3-06b | frozen | v2 | 0.58 [0.47,0.69] (n=53) | 0.93 [0.82,0.98] (n=30) | 0.89 | 0.20 | 1.00 | 1.72 | 1391 | 20260712-153715-confirm2-frozen-qwen3-06b |
| qwen3-1.7b | frozen | v2 | 0.49 [0.38,0.60] (n=53) | 0.87 [0.73,0.94] (n=30) | 0.87 | 0.00 | 1.00 | 1.7 | 1372 | 20260712-154101-confirm2-frozen-qwen3-1.7b |
| hermes-3-3b | frozen | v2 | 0.08 [0.03,0.16] (n=53) | 0.93 [0.82,0.98] (n=30) | 0.00 | 0.00 | — | 1.0 | 116 | 20260712-162156-confirm2-frozen-hermes-3-3b |
| smollm3-3b | frozen | v2 | 0.04 [0.01,0.11] (n=53) | 1.00 [0.92,1.00] (n=30) | 0.00 | 0.00 | — | 1.0 | 147 | 20260712-161657-confirm2-frozen-smollm3-3b |
| gemma-3-1b-q4 | frozen | v2 | 0.02 [0.00,0.08] (n=53) | 0.83 [0.70,0.92] (n=30) | 0.00 | 0.00 | — | 1.0 | 122 | 20260712-155824-confirm2-frozen-gemma-3-1b-q4 |
| gemma-3-4b | frozen | v2 | 0.02 [0.00,0.08] (n=53) | 0.17 [0.08,0.30] (n=30) | 0.00 | 0.00 | — | 1.0 | 122 | 20260712-155934-confirm2-frozen-gemma-3-4b |
| phi-4-mini | frozen | v2 | 0.00 [0.00,0.05] (n=53) | 0.73 [0.59,0.84] (n=30) | 0.00 | 0.00 | — | 1.0 | 106 | 20260712-161441-confirm2-frozen-phi-4-mini |
