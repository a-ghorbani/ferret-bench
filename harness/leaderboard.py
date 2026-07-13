#!/usr/bin/env python3
"""Render analysis/scores.jsonl → analysis/leaderboard.md (+ optional filtered views).

Usage:
  python3 leaderboard.py                     # all rows, grouped by dataset_version
  python3 leaderboard.py --tag confirm       # only run_ids containing '-confirm-'
  python3 leaderboard.py --config shipped    # only one config, compare models
  python3 leaderboard.py --model qwen3-1.7b  # only one model, compare configs
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import REPO_DIR, read_jsonl


def _variants():
    """Community variants are ablations, not board entries — excluded from published views."""
    p = REPO_DIR / "harness" / "models-variants.txt"
    if not p.is_file():
        return set()
    return {l.strip() for l in p.read_text().splitlines() if l.strip() and not l.startswith("#")}


VARIANTS = _variants()

ANALYSIS = REPO_DIR / "analysis"


def fmt_ci(cell):
    if not cell or cell.get("rate") is None:
        return "—"
    lo, hi = cell["ci90"]
    return f"{cell['rate']:.2f} [{lo:.2f},{hi:.2f}] (n={cell['n']})"


def fmt(v, spec="{}"):
    return "—" if v is None else spec.format(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="confirm2")
    ap.add_argument("--config", default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--out", default=str(ANALYSIS / "leaderboard.md"))
    args = ap.parse_args()

    rows = read_jsonl(ANALYSIS / "scores.jsonl")
    rows = [r for r in rows if r["model"] not in VARIANTS]
    if args.tag:
        rows = [r for r in rows if f"-{args.tag}-" in r["run_id"]]
    if args.config:
        rows = [r for r in rows if r["config_id"] == args.config]
    if args.model:
        rows = [r for r in rows if r["model"] == args.model]

    rows.sort(key=lambda r: -(r["correct_fresh"]["rate"] or 0))
    lines = [
        "# Leaderboard — agentic web search, small on-device LLMs",
        "",
        "Primary metric: **fresh-split correctness** (questions that require retrieval), judged "
        "3-way vs gold. `[..]` = Wilson 90% CI. Full metric definitions in PROTOCOL.md §Metrics; "
        "every row traces to `runs/<run_id>/`.",
        "",
        "| model | config | dataset | fresh ✓ | stable ✓ | engage | false-search | validity | avg turns | avg prompt tok | run |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['model']} | {r['config_id']} | {r.get('dataset_version') or '?'} "
            f"| {fmt_ci(r['correct_fresh'])} | {fmt_ci(r['correct_stable'])} "
            f"| {fmt(r['engagement_fresh'], '{:.2f}')} | {fmt(r['false_search_rate'], '{:.2f}')} "
            f"| {fmt(r['tool_call_validity'], '{:.2f}')} | {fmt(r['avg_turns'])} "
            f"| {fmt(r['avg_prompt_tokens'])} | {r['run_id']} |"
        )
    Path(args.out).write_text("\n".join(lines) + "\n")
    print(f"wrote {len(rows)} rows → {args.out}")


if __name__ == "__main__":
    main()
