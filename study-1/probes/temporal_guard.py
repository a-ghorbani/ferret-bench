#!/usr/bin/env python3
"""temporal_guard — enforce the freshness floor and the valid_until expiry ceiling.

Two curation gates (see CURATION-SPEC.md §Temporal validity):
  freshness floor : anchor - FRESHNESS_WINDOW <= event_date < anchor   (primary contamination guard)
  expiry ceiling  : recurring-event golds need valid_until > anchor     (stale-gold inversion guard)

Recurring-event items ("who won the nba finals?") are time-relative: the gold is valid only until
the next occurrence. We propose valid_until = event_date + ~1 year for human confirmation; nothing
is auto-admitted with a machine-guessed expiry.

Pure/mechanical: dates only, no LLM, no network.
"""
import argparse
import datetime
import json
import re
from pathlib import Path

FRESHNESS_WINDOW_DAYS = 60

# recurring annual events whose undated phrasing makes the gold time-relative
RECURRING_RE = re.compile(
    r"\b(nba finals|stanley cup|champions league|french open|us open|wimbledon|"
    r"australian open|world cup|super bowl|world series|ballon d'?or|nobel|oscars?|"
    r"grammys?|tonys?|emmys?|grand prix|le mans|masters|album of the year|"
    r"best (musical|picture|album))\b", re.I)


def is_recurring(item):
    if item.get("dated"):        # question names its own year -> not time-relative
        return False
    return bool(RECURRING_RE.search(item.get("question", "")))


def check(item, anchor):
    ed = item.get("event_date")
    out = {"freshness": None, "age_days": None, "recurring": is_recurring(item),
           "valid_until": item.get("valid_until"), "flags": []}
    if not ed:
        out["flags"].append("no_event_date")
        return out
    d = datetime.date.fromisoformat(ed)
    age = (anchor - d).days
    out["age_days"] = age
    if d >= anchor:
        out["flags"].append("event_not_in_past")
    elif age > FRESHNESS_WINDOW_DAYS:
        out["flags"].append(f"stale_{age}d_over_{FRESHNESS_WINDOW_DAYS}d")
        out["freshness"] = "fail"
    else:
        out["freshness"] = "ok"
    if out["recurring"] and not out["valid_until"]:
        # propose next occurrence (~1yr) for HUMAN confirmation — not auto-admitted
        out["proposed_valid_until"] = (d + datetime.timedelta(days=358)).isoformat()
        out["flags"].append("recurring_needs_valid_until")
    if out["valid_until"] and out["valid_until"] <= anchor.isoformat():
        out["flags"].append("EXPIRED_gold_stale")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default=str(Path(__file__).resolve().parents[1] / "datasets/candidates/candidates.jsonl"))
    ap.add_argument("--anchor", default="2026-07-14")
    ap.add_argument("--split", default="fresh")
    args = ap.parse_args()
    anchor = datetime.date.fromisoformat(args.anchor)

    rows = [json.loads(l) for l in open(args.candidates) if l.strip()]
    rows = [r for r in rows if r.get("split") == args.split]

    stale, recurring, ok = [], [], 0
    results = []
    for r in rows:
        res = check(r, anchor)
        results.append({"id": r["id"], "question": r["question"], **res})
        if "fail" == res["freshness"]:
            stale.append((r["id"], res["age_days"]))
        if res["recurring"]:
            recurring.append((r["id"], res.get("proposed_valid_until")))
        if res["freshness"] == "ok" and not any(f.startswith("recurring") or f.startswith("EXPIRED") for f in res["flags"]):
            ok += 1

    print(f"anchor={args.anchor}  window={FRESHNESS_WINDOW_DAYS}d  n={len(rows)}")
    print(f"\nfreshness-clean & no temporal flag: {ok}/{len(rows)}")
    print(f"\nSTALE (event older than {FRESHNESS_WINDOW_DAYS}d) — would be rejected: {len(stale)}")
    for i, a in stale:
        print(f"  {i:14} {a}d old")
    print(f"\nRECURRING (needs valid_until before admission): {len(recurring)}")
    for i, pv in recurring:
        print(f"  {i:14} propose valid_until={pv}  (HUMAN must confirm)")

    out = Path(__file__).resolve().parents[1] / "verification" / f"temporal_guard.{args.split}.jsonl"
    with open(out, "w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
