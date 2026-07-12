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
import re
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


# Mirrored EXACTLY from the consumer's validator (raised 2026-07-12 after a 3-char overflow
# rejected a correction payload and pinned production to the wrong copy). Never trim a
# correction to fit a cap — ask for the cap to be raised.
CAPS = {"value": 12, "label": 32, "detail": 240, "config_note": 240,
        "metric_label": 32, "metric_description": 280, "gate_title": 90, "mechanism": 800,
        "limitation": 360, "tier_note": 160, "band_note": 600, "floor_note": 32,
        "config_lift_note": 600, "frontier_note": 400, "gate_failure_takeaway": 240}
TIER_KEYS = ("T1", "T2", "T3", "T4")
REQUIRED_CONTENT = ("content_schema_version", "headline_findings", "config_notes", "limitations")
_HTMLISH = re.compile(r"[<>]|&[a-z]+;|\*\*|\[.*\]\(.*\)")


def _check_text(field, s, cap, errs):
    if not isinstance(s, str):
        errs.append(f"{field}: not a string")
        return
    if len(s) > cap:
        errs.append(f"{field}: {len(s)} chars exceeds cap {cap}")
    if _HTMLISH.search(s):
        errs.append(f"{field}: contains HTML/markdown; plain text only")


def compute_tier_gradient(rows):
    """T1 (everyday lookup) vs T3+T4 (multi-source/multi-hop), per model, WITH Wilson CIs.

    Emitted as data, not prose: the site renders intervals everywhere, so a bare pooled point
    estimate would be the one unrigorous number on the page. Returns None if the dataset is untiered.
    """
    from aggregate import wilson_interval

    def pooled(tiers, keys):
        c = sum(tiers[k]["correct"] for k in keys if k in tiers)
        n = sum(tiers[k]["n"] for k in keys if k in tiers)
        if n == 0:
            return None
        lo, hi = wilson_interval(c, n)
        return {"correct": c, "n": n, "rate": round(c / n, 4), "ci90": [lo, hi]}

    out = []
    for r in rows:
        tiers = r.get("fresh_by_tier")
        if not tiers or not r["gate_pass"]:
            continue
        easy, hard = pooled(tiers, ["T1"]), pooled(tiers, ["T3", "T4"])
        if not (easy and hard):
            continue
        out.append({"model_id": r["model_id"], "display_name": r["display_name"], "class": r["class"],
                    "easy_T1": easy, "hard_T3_T4": hard, "drop": round(easy["rate"] - hard["rate"], 4)})
    return out or None


def compute_band_separation(rows):
    """Do any two gate-passing on-device models separate at 90% CI? Ground truth for band_note."""
    band = [r for r in rows if r["class"] in ("official", "variant") and r["gate_pass"]]
    if len(band) < 2:
        return {"separated": False, "detail": "fewer than two gate-passing models"}
    band.sort(key=lambda r: -(r["fresh"]["rate"] or 0))
    top, bottom = band[0], band[-1]
    top_lo = top["fresh"]["ci90"][0]
    bot_hi = bottom["fresh"]["ci90"][1]
    separated = top_lo > bot_hi
    return {
        "separated": separated,
        "detail": (f"top={top['model_id']} {top['fresh']['rate']:.3f} CI{top['fresh']['ci90']}; "
                   f"bottom={bottom['model_id']} {bottom['fresh']['rate']:.3f} CI{bottom['fresh']['ci90']}; "
                   f"{'non-overlapping' if separated else 'overlapping'} at 90%"),
    }


def load_page_content(doc_dataset_version, doc_config_hash, out_rows, config_values):
    """Load interpretive text, validate it, and cross-check its CLAIMS against the data.
    Hard-fails rather than shipping prose that no longer matches the runs."""
    p = HARNESS / "page_content.json"
    if not p.is_file():
        raise SystemExit("harness/page_content.json missing — the export carries the prose now")
    c = json.loads(p.read_text())
    errs = []

    for k in REQUIRED_CONTENT:
        if k not in c:
            errs.append(f"missing required field: {k}")

    # 1. Staleness: prose must be written against exactly these runs.
    if c.get("for_dataset_version") != doc_dataset_version:
        errs.append(f"page_content.for_dataset_version={c.get('for_dataset_version')!r} but exporting "
                    f"{doc_dataset_version!r} — REWRITE the prose for this dataset, then update the field")
    if c.get("for_config_hash") != doc_config_hash:
        errs.append(f"page_content.for_config_hash mismatch — the config changed; re-read the results "
                    f"and rewrite the notes (expected {doc_config_hash[:12]}…)")

    # 2. Shape/format constraints the consumer enforces on fetch.
    for i, h in enumerate(c.get("headline_findings", [])):
        _check_text(f"headline_findings[{i}].value", h.get("value"), CAPS["value"], errs)
        _check_text(f"headline_findings[{i}].label", h.get("label"), CAPS["label"], errs)
        _check_text(f"headline_findings[{i}].detail", h.get("detail"), CAPS["detail"], errs)
    if not 3 <= len(c.get("headline_findings", [])) <= 5:
        errs.append("headline_findings: expected 3-5 items")
    for k, v in (c.get("config_notes") or {}).items():
        if k not in config_values:
            errs.append(f"config_notes key {k!r} is not a config value key")
        _check_text(f"config_notes.{k}", v, CAPS["config_note"], errs)
    for i, m in enumerate(c.get("metric_definitions", [])):
        # label is now a COLUMN HEADER on the page — cap it like any other label
        _check_text(f"metric_definitions[{i}].label", m.get("label"), CAPS["metric_label"], errs)
        _check_text(f"metric_definitions[{i}].description", m.get("description"), CAPS["metric_description"], errs)
    for i, g in enumerate(c.get("gate_failures", [])):
        _check_text(f"gate_failures[{i}].title", g.get("title"), CAPS["gate_title"], errs)
        _check_text(f"gate_failures[{i}].mechanism", g.get("mechanism"), CAPS["mechanism"], errs)
    for i, l in enumerate(c.get("limitations", [])):
        _check_text(f"limitations[{i}]", l, CAPS["limitation"], errs)

    for f in ("band_note", "floor_note", "config_lift_note", "frontier_note", "gate_failure_takeaway"):
        if f in c:
            _check_text(f, c[f], CAPS[f], errs)

    # tier_notes: required when the dataset is tiered; keys must match presentation_rules.tiers
    tiered = any(r.get("fresh_by_tier") for r in out_rows)
    if tiered:
        tn = c.get("tier_notes")
        if not tn:
            errs.append("dataset is tiered but page_content.tier_notes is missing")
        else:
            if set(tn) != set(TIER_KEYS):
                errs.append(f"tier_notes keys {sorted(tn)} != tier keys {sorted(TIER_KEYS)}")
            for k, v in tn.items():
                _check_text(f"tier_notes.{k}", v, CAPS["tier_note"], errs)

    # 3. Cross-checks: the prose's factual claims vs the exported numbers.
    band = compute_band_separation(out_rows)
    if "band_separated" not in c:
        errs.append("page_content.band_separated missing — declare it; it is cross-checked against the data")
    elif bool(c["band_separated"]) != band["separated"]:
        errs.append(f"band_separated={c['band_separated']} contradicts the data ({band['detail']}). "
                    f"Rewrite band_note: the dataset now "
                    f"{'DOES separate' if band['separated'] else 'does NOT separate'} the top band")

    claimed_gate_fail = {m for g in c.get("gate_failures", []) for m in g.get("models", [])}
    actual_gate_fail = {r["display_name"] for r in out_rows if not r["gate_pass"]}
    if claimed_gate_fail != actual_gate_fail:
        errs.append(f"gate_failures list is stale: prose names {sorted(claimed_gate_fail)}, "
                    f"data shows {sorted(actual_gate_fail)}")

    if errs:
        raise SystemExit("page_content.json is out of date with the results:\n  - " + "\n  - ".join(errs))

    c = {k: v for k, v in c.items() if not k.startswith("_")}
    c["band_separation_computed"] = band
    return c


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
            "quant": r.get("quant"),
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
                         "read_content_chars", "max_turns", "untrusted_wrapper", "enable_thinking", "gen")
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
        "page_content": load_page_content(ds_version, rows[0].get("config_hash"), out_rows, config_values),
        "tier_gradient": compute_tier_gradient(out_rows),
        "rows": out_rows,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    print(f"wrote {len(out_rows)} rows → {out}")


if __name__ == "__main__":
    main()
