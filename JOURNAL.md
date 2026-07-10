# Journal — 2026-07-10-web-search-agentic-config

Append-only. Decisions, findings, surprises, dead ends.

## 2026-07-10 — Session start / FRAME

- Scaffolded repo, git init (embedded repo inside rd-team; rd-team gitignores evaluation/experiments/).
- Verified environment: llama-swap at localhost:8080 serves 45 model ids incl. Qwen3-1.7B/4B, Gemma-3 1B/4B, Gemma-4-E2B, Ministral-3-3B, Phi-4-mini, SmolLM3-3B, LFM2.5-1.2B, and large models usable as judge/ceiling candidates (Qwen3.6-27B-Q8, Gemma-4-31B-Q8).
- BRAVE_API_KEY / TAVILY_API_KEY are NOT in the shell env; they live in `~/Dev/rd-team/.env`. Harness will load from a `.env` path (gitignored); manifests name providers only.
- Drafted `context/topics/web-search.md` in rd-team (didn't exist; FRAME output per skill).
- Spawned Explore subagent to extract the exact PR#808 talent contract (tool schemas, system prompt, result formatting, truncation, turn caps) from ~/Dev/pocketpal-ai — harness must be a faithful replica, and PocketPal's shipped values are the natural default config for screening.
- Wrote PROTOCOL.md v1 with RQ1–RQ7. Key design choices: record-replay HTTP cache for comparability + API budget; freshness-split dataset to prove mechanism engagement (contamination control); floor=no-tool, ceiling=frontier-through-same-harness.
