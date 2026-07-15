#!/usr/bin/env python3
"""snippet_leak probe — does the gold answer appear in a search SNIPPET (no page read needed)?

An item labelled "read-required" is a lie if the answer is already in the result snippets.
This probe runs a small query battery through the real provider (via the record-replay cache)
and checks whether the gold (or an acceptable answer) is present in any snippet text.

Verdict per item:
  gold_in_snippet = True   -> NOT read-required. The answer is reachable without opening a page.
  gold_in_snippet = False  -> candidate for read-required (needs a body-fetch confirmation before certifying).

This is a mechanical probe: no LLM, no judgement. Reuses harness/providers.search.
"""
import argparse
import json
import re
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[2] / "harness"
sys.path.insert(0, str(HARNESS))
from common import load_env          # noqa: E402
from providers import search, ProviderError  # noqa: E402


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def _contains(haystack: str, needle: str) -> bool:
    n = _norm(needle)
    if not n or len(n) < 3:
        return False
    return n in _norm(haystack)


def query_battery(question: str):
    """The obvious query a model would issue, plus light variants. Kept small and deterministic.
    (A frontier-generated adversarial battery is a later upgrade — see CURATION-SPEC.)"""
    q = question.strip().rstrip("?")
    variants = [q]
    # drop a leading interrogative to get a keyword-ish query
    m = re.match(r"^(who|what|which|when|where|how much|how many)\b\s+(.*)", q, re.I)
    if m:
        variants.append(m.group(2))
    return list(dict.fromkeys(variants))  # dedupe, preserve order


def probe_item(item, provider="brave", max_results=5, mode="replay-only"):
    golds = [item["gold_answer"]] + list(item.get("acceptable_answers") or [])
    hit_query = None
    all_snips = []
    for q in query_battery(item["question"]):
        try:
            hits, _ = search(provider, q, max_results, mode)
        except Exception as e:  # ProviderError, CacheMiss, transient net — never kill the batch
            all_snips.append(f"[query {q!r} failed: {e}]")
            continue
        for h in hits:
            snip = (h.get("title") or "") + " — " + (h.get("snippet") or "")
            all_snips.append(snip)
            if any(_contains(snip, g) for g in golds):
                hit_query = q
                break
        if hit_query:
            break
    return {
        "gold_in_snippet": hit_query is not None,
        "matched_query": hit_query,
        "queries_tried": query_battery(item["question"]),
        "n_snippets": len(all_snips),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default=str(Path(__file__).resolve().parents[1] / "datasets/candidates/candidates.jsonl"))
    ap.add_argument("--split", default="fresh", help="only probe this split (fresh by default)")
    ap.add_argument("--provider", default="brave")
    ap.add_argument("--mode", default="replay-or-live",
                    choices=["replay-only", "replay-or-live", "live"],
                    help="replay-only=cache only (miss is error); replay-or-live=capture-on-miss")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    load_env()

    rows = [json.loads(l) for l in open(args.candidates) if l.strip()]
    rows = [r for r in rows if r.get("split") == args.split]
    if args.limit:
        rows = rows[:args.limit]

    from collections import Counter
    by_tier = Counter()
    leak_by_tier = Counter()
    results = []
    for r in rows:
        res = probe_item(r, args.provider, mode=args.mode)
        r_out = {"id": r["id"], "origin_tier": r.get("origin_tier"),
                 "question": r["question"], "gold": r["gold_answer"], **res}
        results.append(r_out)
        t = r.get("origin_tier") or "?"
        by_tier[t] += 1
        if res["gold_in_snippet"]:
            leak_by_tier[t] += 1
        flag = "LEAK" if res["gold_in_snippet"] else "no-leak"
        print(f"{r['id']:14} {t:3} {flag:8} q={res['matched_query'] or '-'}", flush=True)

    print("\n=== gold-in-snippet by origin_tier (LEAK / total) ===")
    for t in sorted(by_tier):
        print(f"  {t}: {leak_by_tier[t]}/{by_tier[t]}")
    total = sum(by_tier.values())
    leaks = sum(leak_by_tier.values())
    print(f"  ALL: {leaks}/{total}  ({leaks/total*100:.0f}% of items have the gold in a snippet)")

    out = Path(__file__).resolve().parents[1] / "verification" / f"snippet_leak.{args.split}.jsonl"
    with open(out, "w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
