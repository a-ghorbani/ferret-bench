#!/usr/bin/env python3
"""Aggregate runs → analysis/scores.jsonl (one row per run, cumulative leaderboard source).

Usage: python3 aggregate.py [--runs <run-id> ...]    (default: every run dir with judgments)
Recomputable at any time; rows are keyed by run_id and overwritten idempotently.
"""

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import REPO_DIR, read_jsonl

RUNS_DIR = REPO_DIR / "runs"
ANALYSIS = REPO_DIR / "analysis"


def wilson_interval(k, n, z=1.645):  # 90% CI
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (round(center - half, 4), round(center + half, 4))


def score_run(run_dir: Path):
    manifest = json.loads((run_dir / "manifest.json").read_text())
    outputs = read_jsonl(run_dir / "outputs.jsonl")
    jpath = run_dir / "judgments.jsonl"
    grades = {r["qid"]: r["grade"] for r in read_jsonl(jpath)} if jpath.is_file() else {}

    by_split = {}
    for rec in outputs:
        by_split.setdefault(rec["split"], []).append(rec)

    def correctness(split):
        recs = [r for r in by_split.get(split, []) if grades.get(r["qid"]) in ("CORRECT", "INCORRECT", "NOT_ATTEMPTED")]
        n = len(recs)
        k = sum(1 for r in recs if grades[r["qid"]] == "CORRECT")
        lo, hi = wilson_interval(k, n)
        return {"n": n, "correct": k, "rate": round(k / n, 4) if n else None, "ci90": [lo, hi],
                "not_attempted": sum(1 for r in recs if grades[r["qid"]] == "NOT_ATTEMPTED")}

    all_calls = [c for r in outputs for c in r["tool_calls"]]
    fresh = by_split.get("fresh", [])
    nosearch = by_split.get("no_search", [])
    row = {
        "run_id": manifest["run_id"],
        "model": manifest["model"],
        "config_id": manifest["config_id"],
        "config_hash": manifest["config_hash"],
        "dataset_version": manifest.get("dataset_version"),
        "dataset_sha256": manifest["dataset_sha256"],
        "judge": manifest.get("judge"),
        "n_questions": len(outputs),
        "correct_fresh": correctness("fresh"),
        "correct_stable": correctness("stable"),
        "tool_call_validity": round(sum(c["args_valid"] for c in all_calls) / len(all_calls), 4) if all_calls else None,
        "n_tool_calls": len(all_calls),
        "engagement_fresh": round(sum(1 for r in fresh if r["n_searches"] > 0) / len(fresh), 4) if fresh else None,
        "false_search_rate": round(sum(1 for r in nosearch if r["n_searches"] > 0) / len(nosearch), 4) if nosearch else None,
        "completion_rate": round(sum(1 for r in outputs if r["final_answer"]) / len(outputs), 4) if outputs else None,
        "error_rate": round(sum(1 for r in outputs if r["error"]) / len(outputs), 4) if outputs else None,
        "hit_max_turns_rate": round(sum(1 for r in outputs if r["hit_max_turns"]) / len(outputs), 4) if outputs else None,
        "avg_turns": round(sum(r["n_turns"] for r in outputs) / len(outputs), 2) if outputs else None,
        "avg_reads": round(sum(r["n_reads"] for r in outputs) / len(outputs), 2) if outputs else None,
        "avg_prompt_tokens": round(sum(r["usage"]["prompt_tokens"] for r in outputs) / len(outputs)) if outputs else None,
        "avg_completion_tokens": round(sum(r["usage"]["completion_tokens"] for r in outputs) / len(outputs)) if outputs else None,
    }
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="*", default=None)
    args = ap.parse_args()

    run_dirs = ([RUNS_DIR / r for r in args.runs] if args.runs
                else sorted(d for d in RUNS_DIR.iterdir() if (d / "outputs.jsonl").is_file()))
    ANALYSIS.mkdir(exist_ok=True)
    scores_path = ANALYSIS / "scores.jsonl"
    existing = {r["run_id"]: r for r in read_jsonl(scores_path)} if scores_path.is_file() else {}
    for d in run_dirs:
        row = score_run(d)
        existing[row["run_id"]] = row
        print(f"{row['run_id']}: fresh={row['correct_fresh']['rate']} stable={row['correct_stable']['rate']} "
              f"validity={row['tool_call_validity']} engage={row['engagement_fresh']}")
    with open(scores_path, "w") as f:
        for rid in sorted(existing):
            f.write(json.dumps(existing[rid], ensure_ascii=False) + "\n")
    print(f"wrote {len(existing)} rows → {scores_path}")


if __name__ == "__main__":
    main()
