#!/usr/bin/env python3
"""gold_verify probe — the TRUTH oracle.

For each candidate, a panel of FRONTIER models (disjoint from the leaderboard AND from the
scoring judge) answers the question using real search results. The item's gold is admitted
only if the panel UNANIMOUSLY converges on it. Small models are excluded by construction:
a small model beating the whole frontier panel on a searchable question is a flag on the
item, not skill (broken-clock). See CURATION-SPEC.md §Two oracles.

Verdict per item:
  unanimous & matches gold      -> gold_confirmed (admit the gold)
  unanimous but != gold         -> gold_disputed  (panel agrees on a DIFFERENT answer -> human)
  not unanimous                 -> gold_uncertain (drop or human)

Panel default: claude-sonnet-5 + gpt-5.6-sol (both != gemini judge). Reuses harness search+chat.
"""
import argparse
import json
import re
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[2] / "harness"
sys.path.insert(0, str(HARNESS))
from common import load_env            # noqa: E402
from providers import search           # noqa: E402
from llm import chat                    # noqa: E402

PANEL = ["openrouter:anthropic/claude-sonnet-5", "openrouter:openai/gpt-5.6-sol"]

ANSWER_PROMPT = """Answer the question using ONLY the search results below. Be concise: reply with just the answer (a name, number, or short phrase). If the results do not contain the answer, reply exactly NObodyKNOWS.

Question: {question}

Search results:
{results}

Answer (short):"""


def _norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def _matches(pred, golds):
    p = _norm(pred)
    if not p or "nobodyknows" in p:
        return False
    return any(_norm(g) and _norm(g) in p for g in golds)


def _results_block(item, provider, mode, k=6):
    hits, _ = search(provider, item["question"].rstrip("?"), k, mode)
    lines = []
    for h in hits[:k]:
        lines.append(f"- {h.get('title','')}: {h.get('snippet','')} ({h.get('url','')})")
    return "\n".join(lines) or "(no results)"


def probe_item(item, panel, provider="brave", mode="replay-or-live"):
    golds = [item["gold_answer"]] + list(item.get("acceptable_answers") or [])
    results = _results_block(item, provider, mode)
    prompt = ANSWER_PROMPT.format(question=item["question"], results=results)
    panel_out = {}
    for m in panel:
        try:
            resp = chat(m, [{"role": "user", "content": prompt}],
                        gen={"temperature": 0, "max_tokens": 120})
            ans = (resp["choices"][0]["message"].get("content") or "").strip()
        except Exception as e:
            ans = f"[error: {e}]"
        panel_out[m] = {"answer": ans, "matches_gold": _matches(ans, golds)}
    matches = [v["matches_gold"] for v in panel_out.values() if not v["answer"].startswith("[error")]
    unanimous_match = bool(matches) and all(matches)
    unanimous_miss = bool(matches) and not any(matches)
    if unanimous_match:
        verdict = "gold_confirmed"
    elif unanimous_miss:
        verdict = "gold_disputed"     # panel agrees, but not with our gold -> inspect
    else:
        verdict = "gold_uncertain"    # panel split
    return {"verdict": verdict, "panel": panel_out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default=str(Path(__file__).resolve().parents[1] / "datasets/candidates/candidates.jsonl"))
    ap.add_argument("--split", default="fresh")
    ap.add_argument("--ids", default="", help="comma-separated ids to probe (pilot subset)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--provider", default="brave")
    ap.add_argument("--mode", default="replay-or-live")
    args = ap.parse_args()
    load_env()

    rows = [json.loads(l) for l in open(args.candidates) if l.strip()]
    if args.ids:
        want = set(args.ids.split(","))
        rows = [r for r in rows if r["id"] in want]
    else:
        rows = [r for r in rows if r.get("split") == args.split]
        if args.limit:
            rows = rows[:args.limit]

    from collections import Counter
    verdicts = Counter()
    results = []
    for r in rows:
        res = probe_item(r, PANEL, args.provider, args.mode)
        verdicts[res["verdict"]] += 1
        results.append({"id": r["id"], "gold": r["gold_answer"], **res})
        ans = " | ".join(f"{m.split('/')[-1]}={v['answer'][:30]}" for m, v in res["panel"].items())
        print(f"{r['id']:14} {res['verdict']:15} gold={r['gold_answer'][:24]:24} :: {ans}", flush=True)

    print("\n=== verdicts ===")
    for v, n in verdicts.most_common():
        print(f"  {v}: {n}")
    out = Path(__file__).resolve().parents[1] / "verification" / f"gold_verify.{args.split}.jsonl"
    with open(out, "w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
