# ferret-bench 🦡→🔎

**Agentic web-search benchmark for small on-device LLMs** — which configuration (result count, prompts, formatting, provider, search→read policy) and which <8B model give the best model-driven internet search experience, built for [PocketPal AI](https://github.com/a-ghorbani/pocketpal-ai) (PR #808: `web_search` + `read_url` talents) but app-agnostic by design.

> Ferrets are small and relentless at finding things. So should your pocket LLM be.

**Status: experiment in progress** — see `STATE.md` for the live phase and `PROTOCOL.md` for the full experimental protocol. This README graduates into full run-it-yourself docs at the REPORT phase.

## What's here

```
PROTOCOL.md      # versioned experimental protocol (frame, metrics, stopping rules)
STATE.md         # live phase + next actions
JOURNAL.md       # append-only decision/finding log
factors.md       # factor table driving the design
datasets/        # question sets, pinned by hash + generator/refresh scripts
harness/         # the benchmark: agent loop replica, providers, judge, replay cache
frozen-config/   # deliverable: optimized parameters w/ provenance (filled at FREEZE)
runs/<id>/       # manifest.json + outputs.jsonl per run
analysis/        # machine-readable scores; the leaderboard source of truth
report.md        # final report, regenerable from analysis/
```

## Secrets

Search providers are BYOK. Keys come from a gitignored `.env` (`BRAVE_API_KEY`, `TAVILY_API_KEY`) — never committed, never in manifests, stripped from the replay cache at capture time.
