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
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import load_env, read_jsonl
from llm import chat, warm_model

JUDGE_PROMPT_VERSION = "v1-simpleqa-3way"
DEFAULT_JUDGE = "ggml-org/Qwen3.6-27B-GGUF:Q8_0"

JUDGE_TEMPLATE = """You are grading an answer to a factual question against a gold answer.

Question: {question}
Gold answer: {gold}
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--judge-model", default=DEFAULT_JUDGE)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    load_env()
    run_dir = Path(args.run).resolve()
    outputs = read_jsonl(run_dir / "outputs.jsonl")
    out_path = run_dir / "judgments.jsonl"
    if out_path.exists() and not args.overwrite:
        raise SystemExit(f"{out_path} exists (use --overwrite)")
    if out_path.exists():
        out_path.unlink()

    print(f"warming judge {args.judge_model} …", flush=True)
    warm_model(args.judge_model)

    for i, rec in enumerate(outputs):
        if rec["split"] == "no_search" or not rec.get("gold_answer"):
            row = {"qid": rec["qid"], "grade": "N/A", "reason": "mechanical-only split"}
        elif rec.get("error") or rec.get("final_answer") is None:
            row = {"qid": rec["qid"], "grade": "NOT_ATTEMPTED", "reason": "run error / no final answer"}
        else:
            prompt = JUDGE_TEMPLATE.format(question=rec["question"], gold=rec["gold_answer"],
                                           pred=rec["final_answer"][:4000])
            resp = chat(args.judge_model, [{"role": "user", "content": prompt}],
                        gen={"temperature": 0, "max_tokens": 1024})
            text = (resp["choices"][0]["message"].get("content") or "")
            grade, reason = parse_grade(text)
            row = {"qid": rec["qid"], "grade": grade or "PARSE_FAIL", "reason": reason or text[:200]}
        with open(out_path, "a") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{i+1}/{len(outputs)} {rec['qid']} → {row['grade']}", flush=True)

    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["judge"] = {"model": args.judge_model, "prompt_version": JUDGE_PROMPT_VERSION,
                         "temperature": 0}
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"done → {out_path}")


if __name__ == "__main__":
    main()
