# Report — Agentic web search for small on-device LLMs (DRAFT — filled at REPORT phase)

Status: **in progress**; sections below fill as phases complete. Every numeric claim must cite a run id under `runs/`. Regenerable from `analysis/` (tables via `harness/leaderboard.py`).

## Executive summary

(filled at REPORT)

## Answers to research questions

### RQ1 — result count
### RQ2 — result formatting
### RQ3 — prompting (system prompt + tool descriptions)
### RQ4 — provider (Brave vs Tavily)
### RQ5 — search→read loop (read_url policy, content limit, turn cap)
### RQ6 — model ranking (<8B) + capability gate
### RQ7 — baselines: floor (no-tool) and ceiling (large local models)

## Frozen configuration (with provenance)

(see `frozen-config/`; summarized here)

## Leaderboard

(from `analysis/leaderboard.md`)

## Judge validation

(agreement stats vs manual labels; prompt version)

## Limitations & not tested

- Exa and Parallel providers not tested (no keys / gated in app).
- Quality measured on workstation llama.cpp (same GGUF quants as phones); on-device latency/thermals not measured here — turn/token counts are the cost proxy.
- Judge validated against control-agent manual labels, not independent human labels.
- (extend at REPORT)

## Reproducing

See README.md — one command re-runs the confirmation sweep through the packaged harness.
