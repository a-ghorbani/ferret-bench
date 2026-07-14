#!/usr/bin/env python3
"""Assemble datasets/v<N>/staging/*.jsonl → questions.jsonl + meta.json (validated, hashed).

Usage: python3 assemble.py v1 --anchor-date 2026-07-10
"""

import argparse
import difflib
import hashlib
import json
import sys
import time
from pathlib import Path

DATASETS_DIR = Path(__file__).resolve().parent
REQUIRED = {"id", "split", "question", "gold_answer", "category"}
SPLITS = {"fresh", "stable", "no_search", "unanswerable"}


def load_staging(vdir: Path):
    rows = []
    for p in sorted((vdir / "staging").glob("*.jsonl")):
        for i, line in enumerate(p.read_text().splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                sys.exit(f"{p.name}:{i+1}: bad JSON: {e}")
    return rows


def validate(rows, anchor_date):
    errs, warns = [], []
    ids = set()
    for r in rows:
        missing = REQUIRED - set(r)
        if missing:
            errs.append(f"{r.get('id','?')}: missing {missing}")
            continue
        if r["split"] not in SPLITS:
            errs.append(f"{r['id']}: bad split {r['split']}")
        if r["id"] in ids:
            errs.append(f"duplicate id {r['id']}")
        ids.add(r["id"])
        if r["split"] == "unanswerable":
            # the ONLY correct behaviour is refusal — a wrong item here punishes a model for being right
            if r.get("gold_answer") != "NOT_FOUND":
                errs.append(f"{r['id']}: unanswerable item must have gold_answer 'NOT_FOUND'")
            if not r.get("acceptable_behaviour"):
                errs.append(f"{r['id']}: unanswerable item needs acceptable_behaviour")
            if not r.get("source_urls"):
                warns.append(f"{r['id']}: unanswerable item without evidence it IS unanswerable")
        if r["split"] == "fresh":
            # `dated` makes the date-in-prompt question testable — the gap that nearly shipped as advice
            if "dated" not in r:
                warns.append(f"{r['id']}: fresh item missing `dated` flag (true if the question names a date/year)")
            if not r.get("source_urls"):
                errs.append(f"{r['id']}: fresh item without source_urls")
            ed = r.get("event_date", "")
            if not ed or ed >= anchor_date:
                errs.append(f"{r['id']}: fresh event_date {ed!r} missing or not before anchor {anchor_date}")
            if not r.get("gold_answer"):
                errs.append(f"{r['id']}: fresh item without gold_answer")
            tier = r.get("tier")
            if tier is not None:  # v2+ tiered datasets
                if tier not in ("T1", "T2", "T3", "T4"):
                    errs.append(f"{r['id']}: bad tier {tier!r}")
                if tier in ("T3", "T4") and not r.get("hops"):
                    warns.append(f"{r['id']}: {tier} item without hops description")
        if r["split"] != "no_search" and r.get("gold_answer") and len(str(r["gold_answer"]).split()) > 12:
            warns.append(f"{r['id']}: long gold answer ({r['gold_answer']!r})")
    qs = [r["question"].lower() for r in rows]
    for i in range(len(qs)):
        for j in range(i + 1, len(qs)):
            if difflib.SequenceMatcher(None, qs[i], qs[j]).ratio() > 0.85:
                warns.append(f"near-duplicate questions: {rows[i]['id']} / {rows[j]['id']}")
    return errs, warns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("version")
    ap.add_argument("--anchor-date", required=True)
    args = ap.parse_args()

    vdir = DATASETS_DIR / args.version
    rows = load_staging(vdir)
    errs, warns = validate(rows, args.anchor_date)
    for w in warns:
        print(f"WARN: {w}")
    if errs:
        for e in errs:
            print(f"ERROR: {e}")
        sys.exit(f"{len(errs)} errors — not assembling")

    order = {"fresh": 0, "stable": 1, "no_search": 2}
    rows.sort(key=lambda r: (order[r["split"]], r["id"]))
    out = vdir / "questions.jsonl"
    with open(out, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    counts = {s: sum(1 for r in rows if r["split"] == s) for s in SPLITS}
    meta = {"version": args.version, "anchor_date": args.anchor_date,
            "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "counts": counts, "sha256": sha}
    (vdir / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"assembled {len(rows)} questions {counts} → {out}\nsha256 {sha}")


if __name__ == "__main__":
    main()
