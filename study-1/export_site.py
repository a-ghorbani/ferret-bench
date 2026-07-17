#!/usr/bin/env python3
"""Export the study-1 leaderboard as site-consumable JSON → study-1/analysis/site/leaderboard.json.

Usage: python3 study-1/export_site.py [--generated-at 2026-07-17] [--out <path>]

This is the study-1 payload builder. It is NOT the v3 harness/export_site.py and does not touch it.
study-1 differs from v3:
  - NO difficulty tiers (dropped).
  - fresh accuracy is reported at the FACT level: variants are aggregated per fact_id, then averaged
    over the 80 fresh facts. The 90% CI is a Wilson interval over n_facts (k = round(rate * n_facts)).
    This reproduces study-1/LEADERBOARD.md exactly.
  - the fabrication (unanswerable) split is near-empty (4 questions / 3 facts) → NO per-row fabrication.
  - gate-FAILURES (schema never rendered) are emitted as a separate, unranked list.
  - adds a file-size Pareto view (accuracy vs on-disk GGUF size).

It aggregates directly from runs/*study1*frozen-<model>/{outputs,judgments}.jsonl joined with
study-1/datasets/dev/questions.jsonl (for split + fact_id), so it does not depend on analysis/scores.jsonl.
"""

import argparse
import configparser
import json
import math
import os
import re
from pathlib import Path

STUDY = Path(__file__).resolve().parent           # .../study-1
REPO = STUDY.parent                                # experiment repo root
RUNS = REPO / "runs"
HARNESS = REPO / "harness"
QUESTIONS = STUDY / "datasets" / "dev" / "questions.jsonl"
MODELS_INI = Path(os.path.expanduser("~/llama-models.ini"))

DATASET_SPLIT = "dev"
DATASET_ANCHOR_DATE = "2026-07-14"                 # curation anchor (study-1/LEADERBOARD.md)
JUDGE = {"model": "deepseek/deepseek-v4-flash", "prompt_version": "v3-simpleqa-3way + unanswerable-refusal"}
GOLD_PANEL = ["gpt-5.6-luna", "z-ai/glm-5.2"]      # disjoint from the judge

# Display names (mirrors harness/chart.py PRETTY, plus the two study-1 additions).
PRETTY = {
    "qwen35-4b": "Qwen3.5-4B", "qwen35-2b": "Qwen3.5-2B",
    "ministral-3-3b": "Ministral-3-3B", "gemma-4-e2b": "Gemma-4-E2B",
    "lfm2-2.6b": "LFM2-2.6B", "lfm25-1.2b": "LFM2.5-1.2B",
    "qwen3-06b": "Qwen3-0.6B", "qwen3-1.7b": "Qwen3-1.7B",
    "bonsai-27b-q1": "Bonsai-27B",
    "gemma-3-4b": "Gemma-3-4B", "gemma-3-1b-q4": "Gemma-3-1B",
    "phi-4-mini": "Phi-4-mini", "smollm3-3b": "SmolLM3-3B", "hermes-3-3b": "Hermes-3-3B",
}

GRADED = ("CORRECT", "INCORRECT", "NOT_ATTEMPTED", "PARSE_FAIL")


def read_jsonl(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def roster(name):
    p = HARNESS / name
    return [l.strip() for l in p.read_text().splitlines() if l.strip() and not l.startswith("#")]


def wilson_interval(k, n, z=1.645):  # 90% CI, matches harness/aggregate.py
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (round(center - half, 4), round(center + half, 4))


def find_run(alias):
    """The frozen study1 run dir for an alias (e.g. runs/*-study1-frozen-<alias>)."""
    hits = sorted(RUNS.glob(f"*-study1-frozen-{alias}"))
    hits = [h for h in hits if h.name.endswith(f"-{alias}") and (h / "outputs.jsonl").is_file()]
    if not hits:
        raise SystemExit(f"no study1 frozen run dir for {alias!r}")
    return hits[-1]   # newest


def gguf_size_gb():
    """alias -> on-disk GGUF size in decimal GB, by stat-ing the path in ~/llama-models.ini."""
    txt = MODELS_INI.read_text()
    paths, cur = {}, None
    for line in txt.splitlines():
        line = line.strip()
        m = re.match(r"\[(.+)\]", line)
        if m:
            cur = m.group(1)
        elif cur and line.startswith("model") and "=" in line:
            paths[cur] = line.split("=", 1)[1].strip()
    out = {}
    for alias, p in paths.items():
        try:
            out[alias] = round(os.stat(p).st_size / 1e9, 2)
        except OSError:
            pass
    return out


def fact_level(records, grades, meta, split):
    """Fact-level accuracy for a split.

    Each fact's score is the mean correctness across its phrasing variants; the reported rate is the
    unweighted mean over facts. CI is Wilson-90 over n_facts with k = round(rate * n_facts).
    This reproduces study-1/LEADERBOARD.md.
    """
    by_fact = {}
    for r in records:
        sp, fid = meta.get(r["qid"], (r.get("split"), None))
        if sp != split:
            continue
        g = grades.get(r["qid"])
        if g not in GRADED:            # PARSE_FAIL counts as not-correct, never dropped
            g = "PARSE_FAIL"
        by_fact.setdefault(fid, []).append(1 if g == "CORRECT" else 0)
    n_facts = len(by_fact)
    if n_facts == 0:
        return None
    fact_means = [sum(v) / len(v) for v in by_fact.values()]
    rate = sum(fact_means) / n_facts
    k = round(rate * n_facts)
    lo, hi = wilson_interval(k, n_facts)
    return {"n_facts": n_facts, "n_variants": sum(len(v) for v in by_fact.values()),
            "rate": round(rate, 4), "ci90": [lo, hi]}


def searched_fraction(records, meta):
    fresh = [r for r in records if meta.get(r["qid"], (r.get("split"), None))[0] == "fresh"]
    n = len(fresh)
    s = sum(1 for r in fresh if r.get("n_searches", 0) > 0)
    return {"n_fresh_questions": n, "n_searched": s,
            "searched_frac": round(s / n, 4) if n else None}


def mark_pareto(rows):
    """A gate-passer is on the accuracy-vs-file_size frontier if no OTHER row dominates it, i.e.
    is at least as accurate (fresh rate) AND at least as small, with at least one strict."""
    for r in rows:
        a, s = r["fresh"]["rate"], r["file_size_gb"]
        dominated = any(
            (o["fresh"]["rate"] >= a and o["file_size_gb"] <= s
             and (o["fresh"]["rate"] > a or o["file_size_gb"] < s))
            for o in rows if o is not r)
        r["pareto_frontier"] = not dominated


def load_page_content(gate_fail_aliases):
    p = STUDY / "page_content.json"
    if not p.is_file():
        raise SystemExit("study-1/page_content.json missing — the export carries the prose")
    c = json.loads(p.read_text())
    errs, warns = [], []
    for k in ("headline_findings", "gate_failures", "limitations", "metric_definitions"):
        if k not in c:
            errs.append(f"page_content missing required field: {k}")
    hf = c.get("headline_findings", [])
    if not 3 <= len(hf) <= 4:
        errs.append(f"headline_findings: expected 3-4, got {len(hf)}")
    # Cross-check: prose's gate-failure roster must equal the actual gate-failure roster.
    claimed = set(c.get("gate_failures", {}).get("model_aliases", []))
    if claimed != set(gate_fail_aliases):
        errs.append(f"gate_failures.model_aliases {sorted(claimed)} != actual {sorted(gate_fail_aliases)}")
    _HTMLISH = re.compile(r"[<>]|\*\*|\[.*\]\(.*\)")
    for i, h in enumerate(hf):
        if _HTMLISH.search(h.get("detail", "")):
            warns.append(f"headline_findings[{i}].detail contains HTML/markdown")
    if errs:
        raise SystemExit("study-1/page_content.json is out of date:\n  - " + "\n  - ".join(errs))
    for w in warns:
        print(f"WARNING: {w}")
    return {k: v for k, v in c.items() if not k.startswith("_")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generated-at", default="2026-07-17")
    ap.add_argument("--out", default=str(STUDY / "analysis" / "site" / "leaderboard.json"))
    args = ap.parse_args()

    meta = {q["id"]: (q["split"], q["fact_id"]) for q in read_jsonl(QUESTIONS)}
    questions = read_jsonl(QUESTIONS)
    # dataset counts: facts and questions per split
    facts_by_split, q_by_split = {}, {}
    for q in questions:
        facts_by_split.setdefault(q["split"], set()).add(q["fact_id"])
        q_by_split[q["split"]] = q_by_split.get(q["split"], 0) + 1
    dataset_counts = {
        "facts": {k: len(v) for k, v in sorted(facts_by_split.items())},
        "questions": dict(sorted(q_by_split.items())),
    }

    sizes = gguf_size_gb()
    passers = roster("models-confirm.txt")
    gate_fail_aliases = roster("models-gatefail.txt")

    # ---- gate-passer rows ----
    config_hash = config_id = None
    config_values = None
    rows = []
    for alias in passers:
        rd = find_run(alias)
        manifest = json.loads((rd / "manifest.json").read_text())
        outs = read_jsonl(rd / "outputs.jsonl")
        grades = {r["qid"]: r["grade"] for r in read_jsonl(rd / "judgments.jsonl")}
        if config_hash is None:
            config_hash, config_id = manifest["config_hash"], manifest["config_id"]
            CVK = ("provider", "result_count", "result_format", "tool_desc", "system_prompt",
                   "snippet_chars", "menu_token_ceiling", "read_url_policy", "read_content_chars",
                   "max_turns", "untrusted_wrapper", "enable_thinking", "gen")
            config_values = {k: manifest["config"].get(k) for k in CVK}
        quant = (manifest.get("weights") or {}).get("quant")
        size_gb = sizes.get(alias, round((manifest.get("weights") or {}).get("size_bytes", 0) / 1e9, 2) or None)
        rows.append({
            "model_id": alias,
            "display_name": PRETTY.get(alias, alias),
            "alias": alias,
            "class": "on-device",
            "quant": quant,
            "file_size_gb": size_gb,
            "gate_pass": True,
            "fresh": fact_level(outs, grades, meta, "fresh"),
            "stable": {"rate": (fact_level(outs, grades, meta, "stable") or {}).get("rate")},
            "searched": searched_fraction(outs, meta),
            "run_id": manifest["run_id"],
        })

    rows.sort(key=lambda r: -(r["fresh"]["rate"] or 0))
    mark_pareto(rows)

    # ---- gate-failure list (unranked) ----
    gate_failures = []
    for alias in gate_fail_aliases:
        rd = find_run(alias)
        outs = read_jsonl(rd / "outputs.jsonl")
        fresh = [o for o in outs if meta.get(o["qid"], (o.get("split"), None))[0] == "fresh"]
        gate_failures.append({
            "model_id": alias,
            "display_name": PRETTY.get(alias, alias),
            "alias": alias,
            "gate_pass": False,
            "schema_not_rendered": sum(1 for o in fresh if o.get("schema_not_rendered")),
            "n_fresh_questions": len(fresh),
            "n_searches": sum(o.get("n_searches", 0) for o in fresh),
            "reason": "tool schema never rendered by the GGUF chat template; the model was never offered the search tools",
        })

    pareto_frontier = [r["alias"] for r in rows if r["pareto_frontier"]]

    doc = {
        "benchmark": "ferret-bench — agentic web search for small on-device LLMs (study-1)",
        "source": "https://github.com/a-ghorbani/ferret-bench",
        "generated_at": args.generated_at,
        "study": "study-1",
        "sweep_tag": "study1",
        "config_id": config_id,
        "config_hash": config_hash,
        "config_values": config_values,
        "dataset_split": DATASET_SPLIT,
        "dataset_anchor_date": DATASET_ANCHOR_DATE,
        "dataset_counts": dataset_counts,
        "judge": JUDGE,
        "gold_panel": GOLD_PANEL,
        "presentation_rules": {
            "no_tiers": "study-1 dropped difficulty tiers; there is no per-tier gradient",
            "cluster_not_ranks": "the top five (0.80–0.87) are one statistical cluster; render groupings, not medal positions",
            "fact_level": "fresh/stable rates are fact-level: variants aggregated per fact_id, mean over facts; CI is Wilson-90 over n_facts",
            "no_fabrication_rate": "the unanswerable split is too small (4 questions / 3 facts) to state a fabrication rate",
            "pareto": "a gate-passer is on the frontier if no other model is >= as accurate AND <= in file size",
        },
        "pareto": {
            "x": "file_size_gb", "y": "fresh.rate",
            "frontier": pareto_frontier,
        },
        "page_content": load_page_content(gate_fail_aliases),
        "gate_failures": gate_failures,
        "rows": rows,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    print(f"wrote {len(rows)} gate-passer rows + {len(gate_failures)} gate-failures → {out}")
    print(f"pareto frontier: {', '.join(pareto_frontier)}")


if __name__ == "__main__":
    main()
