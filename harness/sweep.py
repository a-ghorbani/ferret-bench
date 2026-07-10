#!/usr/bin/env python3
"""Batch driver: run (configs × models) serially — grouped by model to minimize llama-swap
model loads (single GPU: one model in flight, ever) — then judge every run, then aggregate.

Usage:
  python3 sweep.py --configs shipped screen-rc3 … --models qwen3-1.7b gemma-3-4b \
      --dataset ../datasets/v1/questions.jsonl [--qids-file slice.txt] [--tag screen] \
      [--http-mode replay-or-live] [--no-judge] [--skip-existing]

Adding a model to the ongoing benchmark = appending its llama-swap id to --models
(or to the sweep manifest file passed via --models-file).
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aggregate import main as _  # noqa: F401  (import check)
from common import REPO_DIR, load_env
from judge import DEFAULT_JUDGE, judge_run
from llm import LLMError, warm_model
from run_eval import run_one

RUNS_DIR = REPO_DIR / "runs"


def existing_run(tag, config_id, model):
    model_short = model.split("/")[-1].split(":")[0].lower().replace("_", "-")[:24]
    pat = f"*-{tag}-{config_id}-{model_short}"
    return next((d for d in RUNS_DIR.glob(pat) if (d / "outputs.jsonl").is_file()), None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", nargs="+", required=True)
    ap.add_argument("--models", nargs="+", default=None)
    ap.add_argument("--models-file", default=None, help="file with one llama-swap model id per line")
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--qids-file", default=None)
    ap.add_argument("--split", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--tag", default="sweep")
    ap.add_argument("--http-mode", default="replay-or-live")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--judge-model", default=DEFAULT_JUDGE)
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--skip-existing", action="store_true",
                    help="skip (tag,config,model) cells that already have a run with outputs")
    args = ap.parse_args()

    load_env()
    models = list(args.models or [])
    if args.models_file:
        models += [l.strip() for l in Path(args.models_file).read_text().splitlines()
                   if l.strip() and not l.startswith("#")]
    if not models:
        sys.exit("no models given")

    run_ids, failures = [], []
    t0 = time.time()
    for model in models:
        warmed = False
        for config in args.configs:
            if args.skip_existing:
                prior = existing_run(args.tag, config, model)
                if prior:
                    print(f"skip existing: {prior.name}")
                    run_ids.append(prior.name)
                    continue
            try:
                if not warmed:
                    print(f"=== warming {model} ===", flush=True)
                    warm_model(model)
                    warmed = True
                rid = run_one(config, model, args.dataset, limit=args.limit, split=args.split,
                              qids_file=args.qids_file, http_mode=args.http_mode,
                              seed=args.seed, tag=args.tag, warm=False)
                run_ids.append(rid)
            except (LLMError, Exception) as e:  # a failing cell must not kill the sweep
                print(f"FAILED cell config={config} model={model}: {e}", flush=True)
                failures.append({"config": config, "model": model, "error": str(e)})

    if not args.no_judge and run_ids:
        print("=== judging ===", flush=True)
        warm_model(args.judge_model)
        for rid in run_ids:
            try:
                judge_run(RUNS_DIR / rid, args.judge_model, warm=False)
            except Exception as e:
                print(f"JUDGE FAILED {rid}: {e}", flush=True)
                failures.append({"judge_run": rid, "error": str(e)})

    print("=== aggregating ===", flush=True)
    import subprocess
    subprocess.run([sys.executable, str(Path(__file__).parent / "aggregate.py")], check=False)

    summary = {"tag": args.tag, "run_ids": run_ids, "failures": failures,
               "wall_seconds": round(time.time() - t0, 1)}
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
