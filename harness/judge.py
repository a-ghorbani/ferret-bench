#!/usr/bin/env python3
"""Grade a run's final answers against gold → runs/<run-id>/judgments.jsonl.

Judge: local large model, temperature 0, SimpleQA-style 3-way grading. The judge prompt is
versioned here (JUDGE_PROMPT_VERSION); manifest is updated with the judge config.

Usage: python3 judge.py --run ../runs/<run-id> [--judge-model "ggml-org/Qwen3.6-27B-GGUF:Q8_0"]

NOTE (single-GPU discipline): judging loads a different model than the subject — never run
judge.py while run_eval.py is in flight.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import load_env, read_jsonl
from llm import chat, warm_model

JUDGE_PROMPT_VERSION = "v2-simpleqa-3way-acceptable"  # v2: acceptable_answers included (manual validation found v1 marked acceptable alternates INCORRECT)
DEFAULT_JUDGE = "google/gemini-3.5-flash"  # via OpenRouter (protocol amendment #5; grok-4.5 region-blocked)
OPENROUTER_URL = "https://openrouter.ai/api"  # chat() appends /v1/chat/completions
LOCAL_FALLBACK_JUDGE = "ggml-org/Qwen3.6-27B-GGUF:Q8_0"
JUDGE_WORKERS = 8

JUDGE_TEMPLATE = """You are grading an answer to a factual question against a gold answer.

Question: {question}
Gold answer: {gold}{acceptable}
Predicted answer: {pred}

Grade the predicted answer:
- CORRECT: it contains the gold answer's key fact(s), with no statement contradicting the gold answer. Extra correct detail, citations, or different phrasing are fine. Numbers must match to reasonable rounding.
- INCORRECT: it makes a factual claim about the asked fact that contradicts or differs from the gold answer.
- NOT_ATTEMPTED: it declines to answer, says it could not find the answer, or makes no factual claim about the asked fact.

Judge only against the gold answer, not your own knowledge or the answer's fluency.
Respond with exactly one JSON object: {{"grade": "CORRECT" | "INCORRECT" | "NOT_ATTEMPTED", "reason": "<one sentence>"}}"""


def parse_grade(text: str):
    m = re.search(r'"grade"\s*:\s*"(CORRECT|INCORRECT|NOT_ATTEMPTED)"', text or "")
    if m:
        reason = re.search(r'"reason"\s*:\s*"([^"]*)"', text or "")
        return m.group(1), reason.group(1) if reason else ""
    for g in ("NOT_ATTEMPTED", "INCORRECT", "CORRECT"):  # bare-word fallback, most specific first
        if g in (text or ""):
            return g, "(bare-word fallback)"
    return None, None


def _judge_endpoint(judge_model):
    """Remote (OpenRouter) for non-local judge ids; local llama-swap otherwise."""
    if "/" in judge_model and not judge_model.startswith("ggml-org") and ":" not in judge_model:
        key = os.environ.get("OPENROUTER_API_KEY", "")
        if not key:
            raise SystemExit("OPENROUTER_API_KEY not set (needed for remote judge)")
        return OPENROUTER_URL, key
    return None, None


def _grade_one(rec, judge_model, base_url, api_key):
    if rec["split"] == "no_search" or not rec.get("gold_answer"):
        return {"qid": rec["qid"], "grade": "N/A", "reason": "mechanical-only split"}
    if rec.get("error") or rec.get("final_answer") is None:
        return {"qid": rec["qid"], "grade": "NOT_ATTEMPTED", "reason": "run error / no final answer"}
    acc = rec.get("acceptable_answers") or []
    acc_line = ("\nAlso acceptable: " + "; ".join(acc)) if acc else ""
    prompt = JUDGE_TEMPLATE.format(question=rec["question"], gold=rec["gold_answer"],
                                   acceptable=acc_line, pred=rec["final_answer"][:4000])
    resp = chat(judge_model, [{"role": "user", "content": prompt}],
                gen={"temperature": 0, "max_tokens": 1024}, base_url=base_url, api_key=api_key)
    text = (resp["choices"][0]["message"].get("content") or "")
    grade, reason = parse_grade(text)
    return {"qid": rec["qid"], "grade": grade or "PARSE_FAIL", "reason": reason or text[:200]}


def judge_run(run_dir, judge_model=DEFAULT_JUDGE, overwrite=False, warm=True):
    """Grade one run. Returns path to judgments.jsonl (or None if skipped)."""
    load_env()
    run_dir = Path(run_dir).resolve()
    outputs = read_jsonl(run_dir / "outputs.jsonl")
    # join acceptable_answers from the dataset pinned in the manifest
    manifest = json.loads((run_dir / "manifest.json").read_text())
    ds_path = Path(manifest["dataset"])
    if not ds_path.is_absolute():
        ds_path = run_dir.parent.parent / manifest["dataset"]
    acc_by_qid = {q["id"]: q.get("acceptable_answers") for q in read_jsonl(ds_path)} if ds_path.is_file() else {}
    for rec in outputs:
        rec["acceptable_answers"] = acc_by_qid.get(rec["qid"])
    out_path = run_dir / "judgments.jsonl"
    if out_path.exists() and not overwrite:
        print(f"skip (exists): {out_path}")
        return None
    if out_path.exists():
        out_path.unlink()

    base_url, api_key = _judge_endpoint(judge_model)
    if warm and base_url is None:
        print(f"warming judge {judge_model} …", flush=True)
        warm_model(judge_model)

    if base_url:  # remote judge: parallel
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=JUDGE_WORKERS) as ex:
            rows = list(ex.map(lambda r: _grade_one(r, judge_model, base_url, api_key), outputs))
    else:  # local judge: strictly serial (single GPU)
        rows = [_grade_one(r, judge_model, None, None) for r in outputs]

    with open(out_path, "w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    from collections import Counter
    print(f"{run_dir.name}: {dict(Counter(r['grade'] for r in rows))}", flush=True)

    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["judge"] = {"model": judge_model, "prompt_version": JUDGE_PROMPT_VERSION,
                         "temperature": 0}
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"done → {out_path}")
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--judge-model", default=DEFAULT_JUDGE)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    judge_run(args.run, args.judge_model, args.overwrite)


if __name__ == "__main__":
    main()
