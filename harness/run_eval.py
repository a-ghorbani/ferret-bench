#!/usr/bin/env python3
"""Run one (config × model × dataset) evaluation batch → runs/<run-id>/{manifest.json,outputs.jsonl}.

Usage:
  python3 run_eval.py --config shipped --model qwen3-1.7b --dataset ../datasets/v1/questions.jsonl \
      [--limit N] [--split fresh,stable,no_search] [--http-mode replay-or-live] [--seed 42] [--tag screen]
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_loop import run_agent
from common import REPO_DIR, load_env, read_jsonl, sha256_file
from configs import load_config
from llm import warm_model

RUNS_DIR = REPO_DIR / "runs"


def make_run_id(tag, config_id, model):
    stamp = time.strftime("%Y%m%d-%H%M%S")
    model_short = model.split("/")[-1].split(":")[0].lower().replace("_", "-")[:24]
    return f"{stamp}-{tag}-{config_id}-{model_short}"


def git_rev():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_DIR, text=True).strip()
    except Exception:
        return None


MODELS_INI = os.environ.get("LLAMA_MODELS_INI", str(Path.home() / "llama-models.ini"))


def resolve_weights(model: str):
    """Resolve a model alias to the actual GGUF: path + quantization + size.

    The protocol requires manifests to pin the weights, not just an alias. They did not, and it
    let an uncontrolled quantization difference (Q8_0 vs Q4_K_M) into a published comparison.
    Never ship a run whose weights cannot be identified from its manifest.
    """
    if model.startswith("openrouter:"):
        return {"kind": "remote", "model_id": model.split(":", 1)[1], "quant": None}
    try:
        ini = Path(MODELS_INI).read_text()
        m = re.search(rf"^\[{re.escape(model)}\]\s*\n(?:.*\n)*?model\s*=\s*(\S+)", ini, re.M)
        if not m:
            return {"kind": "local", "quant": "UNKNOWN", "gguf_path": None, "warning": f"{model} not in {MODELS_INI}"}
        p = Path(m.group(1))
        q = re.search(r"(IQ\d[_A-Za-z0-9]*|Q\d[_A-Za-z0-9]*|BF16|F16|F32)", p.name, re.I)
        return {"kind": "local", "gguf_path": str(p), "gguf_name": p.name,
                "quant": q.group(1) if q else "UNKNOWN",
                "size_bytes": p.stat().st_size if p.is_file() else None}
    except Exception as e:
        return {"kind": "local", "quant": "UNKNOWN", "error": str(e)}


def run_one(config_name, model, dataset, *, limit=None, split=None, qids_file=None,
            http_mode="replay-or-live", seed=42, tag="run", warm=True):
    """Run one (config × model × dataset) batch. Returns run_id."""
    load_env()
    cfg = load_config(config_name)
    dataset_path = Path(dataset)
    if not dataset_path.is_absolute():
        dataset_path = (Path.cwd() / dataset_path).resolve()
    questions = read_jsonl(dataset_path)
    meta_path = dataset_path.parent / "meta.json"
    ds_meta = json.loads(meta_path.read_text()) if meta_path.is_file() else {}
    anchor_date = ds_meta.get("anchor_date") or time.strftime("%Y-%m-%d")

    if qids_file:
        keep_ids = {l.strip() for l in Path(qids_file).read_text().splitlines() if l.strip()}
        questions = [q for q in questions if q["id"] in keep_ids]
    if split:
        keep = set(split.split(","))
        questions = [q for q in questions if q["split"] in keep]
    if limit:
        questions = questions[:limit]

    run_id = make_run_id(tag, cfg["config_id"] or "cfg", model)
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    manifest = {
        "run_id": run_id,
        "config_id": cfg["config_id"],
        "config_hash": cfg["config_hash"],
        "config": cfg,
        "model": model,
        "weights": resolve_weights(model),
        "dataset": str(dataset_path.relative_to(REPO_DIR)) if str(dataset_path).startswith(str(REPO_DIR)) else str(dataset_path),
        "dataset_sha256": sha256_file(dataset_path),
        "dataset_version": ds_meta.get("version"),
        "anchor_date": anchor_date,
        "n_questions": len(questions),
        "splits": sorted({q["split"] for q in questions}),
        "qids_file": str(qids_file) if qids_file else None,
        "http_mode": http_mode,
        "seed": seed,
        "engine": {"kind": "llama.cpp via llama-swap", "base_url": "http://localhost:8080"},
        "environment_tier": "workstation-dgx",
        "harness_git_rev": git_rev(),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "judge": None,  # filled by judge.py
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

    if warm:
        print(f"[{run_id}] warming {model} …", flush=True)
        warm_model(model)

    out_path = run_dir / "outputs.jsonl"
    t0 = time.time()
    for i, q in enumerate(questions):
        rec = run_agent(q["question"], model, cfg, anchor_date, http_mode, seed=seed + i)
        rec = {"qid": q["id"], "split": q["split"], "question": q["question"],
               "gold_answer": q.get("gold_answer"), **rec}
        with open(out_path, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        status = "ERR" if rec["error"] else ("MAX" if rec["hit_max_turns"] else "ok")
        print(f"[{run_id}] {i+1}/{len(questions)} {q['id']} {status} "
              f"turns={rec['n_turns']} searches={rec['n_searches']} reads={rec['n_reads']}", flush=True)

    manifest["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    manifest["wall_seconds"] = round(time.time() - t0, 1)
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"[{run_id}] done in {manifest['wall_seconds']}s → {run_dir}")
    return run_id


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--split", default=None, help="comma-separated splits to include")
    ap.add_argument("--qids-file", default=None, help="file with one question id per line (slice)")
    ap.add_argument("--http-mode", default="replay-or-live", choices=["replay-or-live", "replay-only", "live"])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--tag", default="run")
    args = ap.parse_args()
    run_one(args.config, args.model, args.dataset, limit=args.limit, split=args.split,
            qids_file=args.qids_file, http_mode=args.http_mode, seed=args.seed, tag=args.tag)


if __name__ == "__main__":
    main()
