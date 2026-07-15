#!/usr/bin/env python3
"""admit_pilot.py — run the PILOT candidates through the FULL admit + resolve pipeline, ISOLATED.

The coordinator wants the pilot kept away from the verified pool: no re-split of the real
dev/holdout, no clobbering of the real ADMISSION/RESOLUTION summaries. So instead of calling
validate.main()/resolve.main() (which overwrite the real splits + study-root summaries), this driver
REUSES the exact probe functions and resolvers verbatim and writes only pilot-scoped artifacts:

  probes    : validate.probe_fresh / probe_stable / probe_unanswerable / probe_no_search
  receipts  : validate.build_receipt   -> verification/receipts_pilot/<id>.json
  resolve   : resolve.RESOLVERS (disputed / recurring / unanswerable auto-resolvers, NO human)

No clustering / split / merge here — that is deferred until the pilot is approved. Resumable: an
item whose pilot receipt already exists is skipped unless --force.
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

STUDY = Path(__file__).resolve().parent
for p in (str(STUDY.parent / "harness"), str(STUDY / "probes"), str(STUDY)):
    if p not in sys.path:
        sys.path.insert(0, p)

from common import load_env          # noqa: E402
import validate                      # noqa: E402  (SPLIT_FN, build_receipt, PANEL, ANCHOR)
import resolve                       # noqa: E402  (RESOLVERS)

PILOT_CAND = STUDY / "datasets" / "candidates" / "pilot.jsonl"
PILOT_RECEIPTS = STUDY / "verification" / "receipts_pilot"
PILOT_SUMMARY = STUDY / "PILOT_ADMISSION.md"


def probe_pass(rows, force):
    PILOT_RECEIPTS.mkdir(parents=True, exist_ok=True)
    for r in rows:
        rc_path = PILOT_RECEIPTS / f"{r['id']}.json"
        if rc_path.exists() and not force:
            continue
        split = r.get("split")
        fn = validate.SPLIT_FN.get(split)
        if not fn:
            rc = validate.build_receipt(r, "needs_human", f"unknown_split_{split}", {}, {})
        else:
            try:
                verdict, reason, attrs, probes = fn(r)
                rc = validate.build_receipt(r, verdict, reason, attrs, probes)
            except Exception as e:  # never kill the batch
                rc = validate.build_receipt(r, "needs_human", f"probe_error:{e}", {}, {"error": str(e)})
        rc_path.write_text(json.dumps(rc, ensure_ascii=False, indent=1))
        print(f"probe  {rc['verdict']:11} {r['id']:16} {split:12} {rc['reason']}", flush=True)


def resolve_pass(cand_by_id):
    receipts = {}
    for p in sorted(PILOT_RECEIPTS.glob("*.json")):
        rc = json.loads(p.read_text())
        receipts[rc["id"]] = rc
    todo = [i for i, rc in receipts.items() if rc["verdict"] == "needs_human"]
    print(f"\nresolving {len(todo)} needs_human pilot items (no human)...", flush=True)
    for i in todo:
        rc = receipts[i]
        item = cand_by_id.get(i, {})
        reason = rc.get("reason", "")
        cat, fn = resolve.RESOLVERS.get(reason, (None, None))
        if not fn:
            rc.update(verdict="drop", resolution=f"no resolver for '{reason}' -> drop", auto_resolved=True)
        else:
            try:
                verdict, patch = fn(item, rc)
            except Exception as e:
                verdict, patch = "drop", {"resolution": f"resolution error: {e} -> drop"}
            rc["verdict"] = verdict
            rc["auto_resolved"] = True
            for k, v in patch.items():
                rc[k] = v
        (PILOT_RECEIPTS / f"{i}.json").write_text(json.dumps(rc, ensure_ascii=False, indent=1))
        print(f"  resolve {rc['verdict']:6} {i:16} [{cat}] {rc.get('resolution','')[:80]}", flush=True)
    return receipts


def write_summary(receipts, cand_by_id):
    per_split = defaultdict(Counter)
    for rc in receipts.values():
        per_split[rc["split"]][rc["verdict"]] += 1
    grand = Counter()
    L = ["# study-1 — PILOT ADMISSION (isolated)", "",
         f"Anchor {validate.ANCHOR}. Panel {', '.join(validate.PANEL)}. Pilot kept OUT of the verified "
         "pool: no clustering/split/merge. Receipts in `verification/receipts_pilot/`.",
         "", "## Verdicts per split (post-resolve)", "",
         "| split | admit | drop | needs_human | total |", "|---|---|---|---|---|"]
    for split in ("fresh", "unanswerable", "stable", "no_search"):
        c = per_split.get(split, Counter())
        grand.update(c)
        L.append(f"| {split} | {c['admit']} | {c['drop']} | {c['needs_human']} | {sum(c.values())} |")
    L.append(f"| **all** | **{grand['admit']}** | **{grand['drop']}** | **{grand['needs_human']}** | "
             f"**{sum(grand.values())}** |")

    drops = [(rc["id"], rc["split"], rc.get("reason"), rc.get("resolution", "")) for rc in receipts.values()
             if rc["verdict"] == "drop"]
    L += ["", f"## Dropped ({len(drops)})", ""]
    for i, sp, reason, res in sorted(drops):
        L.append(f"- **{i}** ({sp}): {reason}" + (f" — {res[:120]}" if res else ""))

    overwritten = [(rc["id"], cand_by_id.get(rc["id"], {}).get("gold_answer"), rc.get("resolved_gold"))
                   for rc in receipts.values() if rc.get("resolved_gold")]
    L += ["", f"## Golds overwritten by panel during resolve ({len(overwritten)})", ""]
    for i, old, new in sorted(overwritten):
        L.append(f"- **{i}**: `{old}` -> `{new}`")

    admitted = [rc for rc in receipts.values() if rc["verdict"] == "admit"]
    L += ["", f"## Admitted fresh items ({sum(1 for r in admitted if r['split']=='fresh')}) — spot check", ""]
    for rc in sorted([r for r in admitted if r["split"] == "fresh"], key=lambda r: r["id"]):
        cand = cand_by_id.get(rc["id"], {})
        L.append(f"- **{rc['id']}** ({cand.get('category')}, {cand.get('event_date')}) "
                 f"gold={rc.get('gold_answer')!r} — {cand.get('question')}")
    PILOT_SUMMARY.write_text("\n".join(L) + "\n")
    print("\n" + "\n".join(L[:14]))
    print(f"\nwrote {PILOT_SUMMARY}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-resolve", action="store_true")
    args = ap.parse_args()
    load_env()
    rows = [json.loads(l) for l in PILOT_CAND.read_text().splitlines() if l.strip()]
    cand_by_id = {r["id"]: r for r in rows}
    print(f"pilot: {len(rows)} items from {PILOT_CAND.name}", flush=True)
    probe_pass(rows, args.force)
    if args.no_resolve:
        receipts = {json.loads(p.read_text())["id"]: json.loads(p.read_text())
                    for p in PILOT_RECEIPTS.glob("*.json")}
    else:
        receipts = resolve_pass(cand_by_id)
    write_summary(receipts, cand_by_id)


if __name__ == "__main__":
    main()
