# Running the model server

The harness talks to one OpenAI-compatible endpoint and refers to models by **alias**
(`qwen35-4b`, `ministral-3-3b`, …). Two things must line up before a sweep will run:

1. a server at `LLM_BASE_URL` (default `http://localhost:8080`) exposing `/v1/models` and `/v1/chat/completions`
2. a **models ini** mapping each alias to its GGUF file, so manifests can pin the exact weights

Aliases starting `openrouter:` bypass both and route to OpenRouter instead.

## Why the ini file is required

`resolve_weights()` (`harness/run_eval.py:45`) reads `~/llama-models.ini`, overridable with
`LLAMA_MODELS_INI`, and records the GGUF path, filename and quantization in every run
manifest. This is not optional bookkeeping: an uncontrolled quantization difference
(Q8_0 vs Q4_K_M) once reached a published comparison. If an alias is missing from the ini,
the run still executes but its weights degrade to `quant: "UNKNOWN"` — and
`tests/test_run_manifest_contract.py` fails on any such run, by design.

## Option A — llama-swap (what the published runs used)

[llama-swap](https://github.com/mostlygeek/llama-swap) fronts llama.cpp and loads models on
demand, one at a time. That serialization is why sweeps are grouped by model.

`~/llama-swap.yaml`:

```yaml
models:
  qwen35-4b:
    cmd: >
      /path/to/llama-server --model /models/Qwen3.5-4B-Q4_K_M.gguf
      --port ${PORT} --ctx-size 8192 --jinja
  ministral-3-3b:
    cmd: >
      /path/to/llama-server --model /models/Ministral-3-3B-Instruct-2512-Q4_K_M.gguf
      --port ${PORT} --ctx-size 8192 --jinja
```

`--jinja` matters: without it llama.cpp will not render tool schemas into the prompt, and
every model will trip the `schema_not_rendered` canary.

`~/llama-models.ini` — the alias→weights map the harness reads:

```ini
[qwen35-4b]
model = /models/Qwen3.5-4B-Q4_K_M.gguf

[ministral-3-3b]
model = /models/Ministral-3-3B-Instruct-2512-Q4_K_M.gguf
```

Aliases must match between the two files.

```bash
llama-swap --config ~/llama-swap.yaml --listen :8080
```

## Option B — plain llama.cpp, one model

```bash
llama-server --model /models/Qwen3.5-4B-Q4_K_M.gguf --port 8080 --ctx-size 8192 --jinja
```

Still add the alias to `~/llama-models.ini`, or manifests will not pin the weights.

## Worked example

```bash
export LLM_BASE_URL=http://localhost:8080
export LLAMA_MODELS_INI=~/llama-models.ini
curl -s $LLM_BASE_URL/v1/models | python3 -m json.tool | head   # alias should appear

cd harness
python3 run_eval.py --config frozen --model qwen35-4b \
    --dataset ../study-1/datasets/dev/questions.jsonl --limit 5 --tag smoke
```

Then check the manifest pinned real weights — this is the thing that goes wrong silently:

```bash
python3 -c "import json,glob; m=json.load(open(sorted(glob.glob('../runs/*smoke*'))[-1]+'/manifest.json')); print(m['weights'])"
# {'kind': 'local', 'gguf_path': '/models/Qwen3.5-4B-Q4_K_M.gguf', 'quant': 'Q4_K_M', ...}
```

`quant: "UNKNOWN"` means the alias is missing from the ini. Fix it before running a real sweep.

## Judging

Grading uses OpenRouter (`deepseek/deepseek-v4-flash`), so `OPENROUTER_API_KEY` must be in
the repo-root `.env`. Pass `--no-judge` to skip it, or `--judge-model` for a local judge —
note a local 27B judge is roughly 30× slower and cannot run concurrently with a sweep on a
single GPU.
