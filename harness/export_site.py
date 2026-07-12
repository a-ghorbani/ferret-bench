#!/usr/bin/env python3
"""Export the leaderboard as site-consumable JSON for pocketpal.dev → analysis/site/leaderboard.json.

Usage: python3 export_site.py [--tag confirm2] [--out ../analysis/site/leaderboard.json]

One row per (model, dataset_version) from analysis/scores.jsonl for the given sweep tag.
Model class comes from the roster files: official (models-confirm.txt), variant
(models-variants.txt), anchor (models-ceiling.txt). Bands, not ranks: rows carry point
estimates + CIs; the site must not render medal positions within a band.
"""

import argparse
import json
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chart import PRETTY
from common import REPO_DIR, read_jsonl

HARNESS = REPO_DIR / "harness"


def roster(path):
    p = HARNESS / path
    if not p.is_file():
        return set()
    return {l.strip() for l in p.read_text().splitlines() if l.strip() and not l.startswith("#")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="confirm2")
    ap.add_argument("--out", default=str(REPO_DIR / "analysis" / "site" / "leaderboard.json"))
    args = ap.parse_args()

    official = roster("models-confirm.txt")
    variants = roster("models-variants.txt")
    anchors = roster("models-ceiling.txt")

    rows = [r for r in read_jsonl(REPO_DIR / "analysis" / "scores.jsonl") if f"-{args.tag}-" in r["run_id"]]
    if not rows:
        raise SystemExit(f"no rows for tag {args.tag} in analysis/scores.jsonl")

    out_rows = []
    for r in sorted(rows, key=lambda r: -(r["correct_fresh"]["rate"] or 0)):
        m = r["model"]
        klass = ("official" if m in official else "variant" if m in variants
                 else "anchor" if m in anchors
                 # heuristic fallback: v1's local ceiling refs (Q8_0 GGUFs) and any remote
                 # model are reference rows, never on-device ranking entries
                 else "anchor" if ("Q8_0" in m or m.startswith("openrouter:")) else "unknown")
        gate_fail = (r["engagement_fresh"] or 0) == 0
        out_rows.append({
            "model_id": m,
            "display_name": PRETTY.get(m, m.replace("openrouter:", "")),
            "class": klass,
            "gate_pass": not gate_fail,
            "fresh": r["correct_fresh"],
            "fresh_by_tier": r.get("correct_fresh_by_tier"),
            "stable": r["correct_stable"],
            "engagement": r["engagement_fresh"],
            "false_search_rate": r["false_search_rate"],
            "tool_call_validity": r["tool_call_validity"],
            "avg_turns": r["avg_turns"],
            "avg_prompt_tokens": r["avg_prompt_tokens"],
            "run_id": r["run_id"],
        })

    # config values, authoritative from the first row's run manifest (full config dump)
    first_manifest = json.loads((REPO_DIR / "runs" / rows[0]["run_id"] / "manifest.json").read_text())
    CONFIG_VALUE_KEYS = ("provider", "result_count", "result_format", "tool_desc", "system_prompt",
                         "snippet_chars", "menu_token_ceiling", "read_url_policy",
                         "read_content_chars", "max_turns", "untrusted_wrapper", "gen")
    config_values = {k: first_manifest["config"].get(k) for k in CONFIG_VALUE_KEYS}

    # dataset counts + anchor date from the version's meta.json
    ds_version = rows[0].get("dataset_version")
    meta_path = REPO_DIR / "datasets" / (ds_version or "") / "meta.json"
    ds_meta = json.loads(meta_path.read_text()) if meta_path.is_file() else {}

    doc = {
        "benchmark": "ferret-bench — agentic web search for small on-device LLMs",
        "source": "https://github.com/a-ghorbani/ferret-bench",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sweep_tag": args.tag,
        "dataset_version": ds_version,
        "dataset_sha256": rows[0].get("dataset_sha256"),
        "dataset_counts": ds_meta.get("counts"),
        "dataset_anchor_date": ds_meta.get("anchor_date"),
        "judge": rows[0].get("judge"),
        "config_id": rows[0].get("config_id"),
        "config_hash": rows[0].get("config_hash"),
        "config_values": config_values,
        "presentation_rules": {
            "bands_not_ranks": "CIs overlap within the working band; do not render medal positions",
            "cross_version": "scores are only comparable within a dataset_version",
            "tiers": {"T1": "single-search (everyday lookups)", "T2": "read-required",
                      "T3": "multi-source", "T4": "multi-hop"},
        },
        "rows": out_rows,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    print(f"wrote {len(out_rows)} rows → {out}")


if __name__ == "__main__":
    main()
