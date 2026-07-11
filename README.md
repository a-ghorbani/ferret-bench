# ferret-bench 🦡→🔎

**Agentic web-search benchmark for small on-device LLMs** — which configuration (result count, prompts, formatting, provider, search→read policy) and which <8B model give the best model-driven internet search experience. Built for [PocketPal AI](https://github.com/a-ghorbani/pocketpal-ai) (PR #808: `web_search` + `read_url` talents, BYOK), app-agnostic by design: the harness is a faithful replica of PocketPal's OpenAI tool-calling ReAct loop (`harness/CONTRACT.md` pins the contract verbatim).

> Ferrets are small and relentless at finding things. So should your pocket LLM be.

- **`frozen-config/`** — the optimized configuration PocketPal can consume directly (tool definitions, prompt, formatting, provider), every value annotated with the runs that justified it (`PROVENANCE.md`).
- **`report.md`** — findings for all research questions; **`analysis/leaderboard.md`** — the model ranking.
- **`PROTOCOL.md`** — the full experimental protocol with amendment log; **`JOURNAL.md`** — decision log.

## Quick start

Requirements: Python 3.10+ with `requests`; an OpenAI-compatible LLM server (llama.cpp `llama-server` or llama-swap) at `http://localhost:8080` (override with `LLM_BASE_URL`); a `.env` in the repo root (gitignored):

```
BRAVE_API_KEY=…        # search provider (recommended default)
TAVILY_API_KEY=…       # optional second provider
OPENROUTER_API_KEY=…   # judge (google/gemini-3.5-flash)
```

### Re-run the confirmation sweep (the leaderboard)

```bash
cd harness
python3 sweep.py --configs frozen --models-file models-confirm.txt \
    --dataset ../datasets/v1/questions.jsonl --tag confirm --skip-existing
python3 leaderboard.py --tag confirm
```

Runs every model × 89 questions through the agent loop, judges answers (3-way vs gold, judge + prompt version pinned in each run manifest), and appends to `analysis/scores.jsonl` (cumulative; rows keyed by run id). `--skip-existing` makes the sweep resumable.

**Single-GPU discipline**: the sweep is strictly serial per model and warms each model with retries. Never run two harness processes against the same server. (Judging is remote and parallel — it can overlap with nothing else on this list.)

### Add a model

Append its llama-swap/llama.cpp model id to `harness/models-confirm.txt`, then re-run the sweep command above — only the new model executes. A model that cannot emit valid tool calls fails the capability gate; that is a reported result (validity column), not an exclusion.

### Try a config variant

Configs are JSON overrides of the shipped PocketPal defaults (`harness/configs.py` documents every knob):

```bash
cat > configs/my-idea.json << 'EOF'
{"config_id": "my-idea", "result_count": 3, "system_prompt": "guided-v2"}
EOF
python3 sweep.py --configs my-idea shipped --models qwen3-1.7b \
    --dataset ../datasets/v1/questions.jsonl --tag mytest
```

### Refresh the dataset (fresh questions go stale)

Follow `datasets/README.md`: re-run the fresh-split curation for a new date window, `python3 assemble.py v2 --anchor-date YYYY-MM-DD`, capture a new replay cache with `--http-mode live`, then **re-run the reference models before comparing anything across versions** (re-anchoring rule — scores are only comparable within a dataset version; the leaderboard keys rows by `dataset_version`).

### Regenerate the report tables

```bash
python3 aggregate.py && python3 leaderboard.py
```

Everything in `report.md` is derived from `analysis/scores.jsonl`; every numeric claim cites a run id under `runs/<run-id>/` (manifest + full transcripts).

## Reproducibility

- **Web state is pinned**: all provider/reader HTTP goes through a record-replay cache (`cache/http/`, capture-on-miss, API keys stripped at capture). `--http-mode replay-only` forces strict replay.
- **Run manifests** pin config hash + full dump, model id, dataset sha256, judge model + prompt version, seeds, timestamps.
- **The grounding prompt's "today"** is the dataset `anchor_date`, not wall clock, so replayed evidence stays consistent.

## Secrets

BYOK only: keys live in the gitignored `.env`, are never written to manifests or the replay cache, and the repo history is secret-scanned before any visibility change.
