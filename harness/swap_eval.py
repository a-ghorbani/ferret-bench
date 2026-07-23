#!/usr/bin/env python3
"""Evidence-swap design: separate QUERY FORMULATION from READING.

Cell (i,j) = model j answering from model i's retrieved evidence. Row effects (source i)
= query quality; column effects (target j) = reading quality; the diagonal is the ordinary
end-to-end number. Because evidence is replayed from stored runs, no HTTP happens at all —
which also makes this immune to the evidence-freezing confound (review issue #1).

Method: take source run's stored `messages`, truncate after the LAST tool message, and ask
the target model to produce the final answer with tools withheld (so it must answer from
what it was given). Chat templating is applied by llama.cpp per target model, so a message
list captured from one model renders correctly for another.

Usage:
  python3 swap_eval.py --sources RUNDIR [RUNDIR ...] --targets model [model ...] \
      --per-fact 1 --tag swap1 [--no-judge]
"""

import argparse, json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import REPO_DIR, load_env
from judge import DEFAULT_JUDGE, judge_run
from llm import chat, warm_model, LLMError

RUNS_DIR = REPO_DIR / "runs"


def evidence_prefix(rec):
    """Messages up to and including the last tool result; None if the model never searched."""
    msgs = rec.get("messages") or []
    last = max((i for i, m in enumerate(msgs) if m.get("role") == "tool"), default=None)
    return msgs[: last + 1] if last is not None else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", nargs="+", required=True, help="run dirs supplying evidence")
    ap.add_argument("--targets", nargs="+", required=True, help="llama-swap model ids that read it")
    ap.add_argument("--per-fact", type=int, default=1, help="variants per fact_id to keep")
    ap.add_argument("--tag", default="swap")
    ap.add_argument("--judge-model", default=DEFAULT_JUDGE)
    ap.add_argument("--no-judge", action="store_true")
    args = ap.parse_args()
    load_env()

    qmeta = {q["id"]: q for q in (json.loads(l) for l in
             open(REPO_DIR / "study-1/datasets/dev/questions.jsonl"))}
    # one item per fact, deterministic
    keep, seen = [], {}
    for qid in sorted(qmeta):
        q = qmeta[qid]
        if q["split"] != "fresh":
            continue
        n = seen.get(q["fact_id"], 0)
        if n < args.per_fact:
            seen[q["fact_id"]] = n + 1
            keep.append(qid)
    keep = set(keep)
    print(f"items: {len(keep)} (<= {args.per_fact} per fact)")

    # evidence bundles per source
    bundles = {}
    for sd in args.sources:
        d = Path(sd) if Path(sd).is_dir() else RUNS_DIR / sd
        man = json.load(open(d / "manifest.json"))
        # Key on model+config, NOT model alone: two runs of the same model under different
        # configs are a legitimate source pair (e.g. read_url on vs off) and keying on the
        # model name silently made the second overwrite the first.
        cid = (man.get("config") or {}).get("config_id") or man.get("kind") or "cfg"
        src = f"{man['model']}|{cid}"
        recs = {}
        for line in open(d / "outputs.jsonl"):
            r = json.loads(line)
            if r["qid"] in keep:
                pre = evidence_prefix(r)
                if pre:
                    recs[r["qid"]] = pre
        bundles[src] = recs
        print(f"  source {src:16} evidence for {len(recs)}/{len(keep)} items")

    common = sorted(set.intersection(*[set(v) for v in bundles.values()]))
    print(f"  -> {len(common)} items have evidence from EVERY source (used for the matrix)\n")

    run_ids = []
    for tgt in args.targets:                      # target-outer: one model load per target
        warm_model(tgt); print(f"=== target {tgt} warmed ===", flush=True)
        for src, recs in bundles.items():
            slug = src.replace('|', '_')[:30]
            rid = f"{time.strftime('%Y%m%d-%H%M%S')}-{args.tag}-from-{slug}-to-{tgt.split('/')[-1][:18]}"
            rd = RUNS_DIR / rid; rd.mkdir(parents=True, exist_ok=True)
            json.dump({"run_id": rid, "kind": "evidence-swap", "source_model": src,
                       "target_model": tgt, "model": tgt, "n_items": len(common),
                       # judge.py:125 resolves acceptable_answers via this key — required
                       "dataset": "study-1/datasets/dev/questions.jsonl",
                       "per_fact": args.per_fact, "http_mode": "none-replayed-evidence",
                       "gen": {"temperature": 0.7, "top_p": 0.95, "max_tokens": 1024, "seed": 42},
                       "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "judge": None},
                      open(rd / "manifest.json", "w"), indent=2)
            t0 = time.time()
            with open(rd / "outputs.jsonl", "w") as f:
                for i, qid in enumerate(common):
                    q = qmeta[qid]
                    try:
                        resp = chat(tgt, recs[qid], tools=None,
                                    gen={"temperature": 0.7, "top_p": 0.95, "max_tokens": 1024, "seed": 42})
                        ans = (resp["choices"][0]["message"].get("content") or "").strip()
                        err = None
                    except (LLMError, Exception) as e:
                        ans, err = None, str(e)[:300]
                    f.write(json.dumps({"qid": qid, "split": "fresh", "question": q["question"],
                                        "gold_answer": q.get("gold_answer"),
                                        "acceptable_answers": q.get("acceptable_answers"),
                                        "final_answer": ans, "error": err,
                                        "source_model": src, "target_model": tgt},
                                       ensure_ascii=False) + "\n")
                    if (i + 1) % 25 == 0:
                        print(f"  [{src} -> {tgt}] {i+1}/{len(common)}", flush=True)
            print(f"  cell {src} -> {tgt}: {len(common)} items in {time.time()-t0:.0f}s", flush=True)
            run_ids.append(rid)

    if not args.no_judge:
        print("=== judging ===", flush=True)
        for rid in run_ids:
            try:
                judge_run(RUNS_DIR / rid, args.judge_model, warm=False)
            except Exception as e:
                print(f"JUDGE FAILED {rid}: {e}", flush=True)
    print(json.dumps({"tag": args.tag, "run_ids": run_ids}, indent=2))


if __name__ == "__main__":
    main()
