# Journal — 2026-07-10-web-search-agentic-config

Append-only. Decisions, findings, surprises, dead ends.

## 2026-07-10 — Session start / FRAME

- Scaffolded repo, git init (embedded repo inside rd-team; rd-team gitignores evaluation/experiments/).
- Verified environment: llama-swap at localhost:8080 serves 45 model ids incl. Qwen3-1.7B/4B, Gemma-3 1B/4B, Gemma-4-E2B, Ministral-3-3B, Phi-4-mini, SmolLM3-3B, LFM2.5-1.2B, and large models usable as judge/ceiling candidates (Qwen3.6-27B-Q8, Gemma-4-31B-Q8).
- BRAVE_API_KEY / TAVILY_API_KEY are NOT in the shell env; they live in `~/Dev/rd-team/.env`. Harness will load from a `.env` path (gitignored); manifests name providers only.
- Drafted `context/topics/web-search.md` in rd-team (didn't exist; FRAME output per skill).
- Spawned Explore subagent to extract the exact PR#808 talent contract (tool schemas, system prompt, result formatting, truncation, turn caps) from ~/Dev/pocketpal-ai — harness must be a faithful replica, and PocketPal's shipped values are the natural default config for screening.
- Wrote PROTOCOL.md v1 with RQ1–RQ7. Key design choices: record-replay HTTP cache for comparability + API budget; freshness-split dataset to prove mechanism engagement (contamination control); floor=no-tool, ceiling=frontier-through-same-harness.

## 2026-07-10 — Contract extracted (PR #808)

- Subagent extracted the full talent/loop contract from `origin/feature/TASK-20260625-1135` in ~/Dev/pocketpal-ai → pinned verbatim in `harness/CONTRACT.md`. Notable: PR #808 is on the feature branch, not local main.
- Shipped values now known and set as the default config: result_count 5 (1–8), snippet 280 chars, search-menu ceiling 1000 tok, read_url 4800 chars via r.jina.ai, max_turns 5 with forced no-tools final, dated grounding system line (budget=4 wording), nonce'd UNTRUSTED WEB CONTENT wrapper on every tool result, labeled plain-text result blocks, Tavily default provider.
- Surprise worth testing: `budgetHits`' 1000-token ceiling silently drops trailing hits — result_count>5 may be a no-op without raising the ceiling. Logged as confound in factors.md; harness will log hits-actually-included.
- Providers in app: tavily (default), brave, exa, parallel(gated). We have keys for brave+tavily → RQ4 scope stays brave-vs-tavily; exa/parallel noted as not-tested.
