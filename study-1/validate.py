#!/usr/bin/env python3
"""study-1 dataset-admission orchestrator.

For each candidate, run the probes applicable to its split (see study-1/CURATION-SPEC.md), emit
ONE receipt per item (study-1/verification/receipts/<id>.json), then cluster admitted items into
fact_ids, split dev/holdout by fact_id, and write the human queue + admission summary.

Probes are REUSED, never reimplemented:
  - snippet_leak.probe_item        (read-required attribute)
  - temporal_guard.check           (freshness floor + valid_until ceiling)
  - gold_verify.probe_item         (single-shot TRUTH oracle: T1/T2 fresh + all stable)
  - gold_verify_agentic.probe_item (ReAct-loop TRUTH oracle: T3/T4 multi-hop fresh)

Admission rules per split (verbatim from the task / CURATION-SPEC):
  fresh:  stale -> drop; gold not confirmed -> needs_human; recurring w/o valid_until -> needs_human;
          freshness not confirmable -> needs_human; else admit. answer_only_in_body set from snippet_leak.
  stable: gold single-shot confirmed -> admit; else needs_human.
  unanswerable: panel WITH search; any model finds a confident answer -> drop; else needs_human
                (human signs the negative). Records source_urls-present and expires_on>anchor checks.
  no_search: mechanical -> admit (false-positive probes; no gold to verify).

Everything network-bearing goes through the harness cache (replay-or-live, capture-on-miss).
Resumable: an item whose receipt already exists is skipped unless --force.
"""
import argparse
import datetime
import difflib
import json
import random
import re
import sys
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path

STUDY = Path(__file__).resolve().parent
HARNESS = STUDY.parent / "harness"
PROBES = STUDY / "probes"
for p in (str(HARNESS), str(PROBES)):
    if p not in sys.path:
        sys.path.insert(0, p)

from common import load_env               # noqa: E402
import snippet_leak                        # noqa: E402
import temporal_guard                      # noqa: E402
import gold_verify                         # noqa: E402
import gold_verify_agentic                 # noqa: E402

CANDIDATES = STUDY / "datasets" / "candidates" / "candidates.jsonl"
RECEIPTS_DIR = STUDY / "verification" / "receipts"
DEV_DIR = STUDY / "datasets" / "dev"
HOLDOUT_DIR = STUDY / "datasets" / "holdout.sealed"

ANCHOR = "2026-07-14"
ANCHOR_DATE = datetime.date.fromisoformat(ANCHOR)
PROVIDER = "brave"
MODE = "replay-or-live"
PANEL = gold_verify.PANEL
HOLDOUT_FRAC = 0.30
SEED = 42

# multi-hop origin tiers -> agentic gold-verify; everything else single-shot
AGENTIC_TIERS = {"T3", "T4"}

# phrases that count as the panel DECLINING to answer an unanswerable question
_DECLINE_RE = re.compile(
    r"\b(nobodyknows|no such|never happened|did not happen|does not exist|doesn'?t exist|"
    r"no record|no evidence|no information|could not find|couldn'?t find|not found|"
    r"no confirmed|no reliable|no credible|false premise|premise is false|"
    r"has not been|hasn'?t been|there is no|no publicly)\b", re.I)


def _norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


# ---------------------------------------------------------------- per-split probing

def probe_fresh(item):
    """Run gold_verify (agentic for T3/T4 else single-shot) + snippet_leak + temporal_guard."""
    tier = item.get("origin_tier")
    if tier in AGENTIC_TIERS:
        gv = gold_verify_agentic.probe_item(item, PANEL, ANCHOR, MODE)
    else:
        gv = gold_verify.probe_item(item, PANEL, PROVIDER, MODE)
        gv["mode"] = "single_shot"
    sl = snippet_leak.probe_item(item, PROVIDER, mode=MODE)
    tg = temporal_guard.check(item, ANCHOR_DATE)

    answer_only_in_body = not sl["gold_in_snippet"]
    freshness = tg.get("freshness")
    recurring = tg.get("recurring")
    has_valid_until = bool(tg.get("valid_until"))
    stale = freshness == "fail" or "EXPIRED_gold_stale" in tg.get("flags", [])

    if stale:
        verdict, reason = "drop", "stale_event_outside_freshness_window"
    elif gv["verdict"] != "gold_confirmed":
        verdict, reason = "needs_human", (
            "gold_disputed_panel_agrees_other" if gv["verdict"] == "gold_disputed"
            else "gold_uncertain_panel_split")
    elif recurring and not has_valid_until:
        verdict, reason = "needs_human", "recurring_needs_valid_until"
    elif freshness != "ok":
        verdict, reason = "needs_human", "freshness_not_confirmable_" + (",".join(tg.get("flags")) or "no_event_date")
    else:
        verdict, reason = "admit", "gold_confirmed_and_fresh"

    attrs = {"answer_only_in_body": answer_only_in_body, "dependent_search": tier in AGENTIC_TIERS, "memorable": None}
    probes = {
        "gold_verify": {"panel": gv["panel"], "verdict": gv["verdict"], "mode": gv["mode"],
                        "unanimous": gv["verdict"] in ("gold_confirmed", "gold_disputed")},
        "snippet_leak": {k: sl[k] for k in ("gold_in_snippet", "matched_query", "queries_tried", "n_snippets")},
        "temporal_guard": tg,
    }
    return verdict, reason, attrs, probes


def probe_stable(item):
    gv = gold_verify.probe_item(item, PANEL, PROVIDER, MODE)
    gv["mode"] = "single_shot"
    if gv["verdict"] == "gold_confirmed":
        verdict, reason = "admit", "gold_confirmed"
    else:
        verdict, reason = "needs_human", (
            "gold_disputed_panel_agrees_other" if gv["verdict"] == "gold_disputed"
            else "gold_uncertain_panel_split")
    attrs = {"answer_only_in_body": None, "dependent_search": False, "memorable": None}
    probes = {"gold_verify": {"panel": gv["panel"], "verdict": gv["verdict"], "mode": gv["mode"],
                              "unanimous": gv["verdict"] in ("gold_confirmed", "gold_disputed")}}
    return verdict, reason, attrs, probes


def probe_unanswerable(item):
    """Panel WITH search: confirm it is genuinely unanswerable (both decline). If any model returns
    a confident specific answer the item is answerable -> drop. Also check negative-evidence URLs
    and a valid expires_on > anchor. Genuinely-unanswerable -> needs_human (human signs the negative)."""
    results = gold_verify._results_block(item, PROVIDER, MODE)
    prompt = gold_verify.ANSWER_PROMPT.format(question=item["question"], results=results)
    panel_out = {}
    for m in PANEL:
        try:
            resp = gold_verify.chat(m, [{"role": "user", "content": prompt}],
                                    gen={"temperature": 0, "max_tokens": 120})
            ans = (resp["choices"][0]["message"].get("content") or "").strip()
            err = False
        except Exception as e:
            ans, err = f"[error: {e}]", True
        declined = err or bool(_DECLINE_RE.search(ans)) or "nobodyknows" in _norm(ans) or not ans.strip()
        panel_out[m] = {"answer": ans[:400], "declined": declined, "error": err}

    non_err = [v for v in panel_out.values() if not v["error"]]
    found_answer = any((not v["declined"]) for v in non_err)
    all_declined = bool(non_err) and all(v["declined"] for v in non_err)

    src_ok = bool(item.get("source_urls"))
    exp = item.get("expires_on")
    expires_ok = bool(exp) and exp > ANCHOR

    if found_answer:
        verdict, reason = "drop", "panel_found_confident_answer_item_is_answerable"
    else:
        verdict = "needs_human"
        missing = []
        if not all_declined:
            missing.append("panel_not_unanimous_decline")
        if not src_ok:
            missing.append("no_negative_evidence_url")
        if not expires_ok:
            missing.append("expires_on_missing_or_past_anchor")
        reason = "unanswerable_confirmed_awaiting_negative_signoff" if not missing \
            else "unanswerable_but_" + ",".join(missing)

    attrs = {"answer_only_in_body": None, "dependent_search": False, "memorable": None}
    probes = {"unanswerable_verify": {"panel": panel_out, "all_declined": all_declined,
                                      "found_answer": found_answer,
                                      "source_urls_present": src_ok, "expires_on_valid": expires_ok}}
    return verdict, reason, attrs, probes


def probe_no_search(item):
    # mechanical: no gold to verify; these are false-positive probes -> admit as-is
    attrs = {"answer_only_in_body": None, "dependent_search": False, "memorable": None}
    probes = {"no_search": {"note": "mechanical false-positive probe; no gold to verify"}}
    return "admit", "mechanical_no_search_admit", attrs, probes


SPLIT_FN = {"fresh": probe_fresh, "stable": probe_stable,
            "unanswerable": probe_unanswerable, "no_search": probe_no_search}


def build_receipt(item, verdict, reason, attrs, probes):
    return {
        "id": item["id"],
        "split": item.get("split"),
        "origin_tier": item.get("origin_tier"),
        "question": item.get("question"),
        "gold_answer": item.get("gold_answer"),
        "verdict": verdict,
        "reason": reason,
        "attributes": attrs,
        "fact_id": None,          # assigned in clustering pass
        "probes": probes,
        "curator_panel": PANEL,
        "anchor": ANCHOR,
        "human_signed": False,
    }


# ---------------------------------------------------------------- fact_id clustering

class UF:
    def __init__(self, items):
        self.p = {i: i for i in items}

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def _host_paths(item):
    out = set()
    for u in item.get("source_urls") or []:
        try:
            pu = urllib.parse.urlparse(u)
            hp = (pu.hostname or "").lower() + pu.path.rstrip("/").lower()
            if hp:
                out.add(hp)
        except ValueError:
            continue
    return out


def cluster_fact_ids(items):
    """Union items that share (source host+path) OR identical normalized gold OR question
    similarity > 0.85. Returns (fact_id_by_id, clusters, ambiguous_pairs).

    Ambiguity = a near-threshold question-similarity pair (0.80..0.85) that is NOT otherwise
    linked -> flag for human, do not force a merge (CURATION-SPEC §fact_cluster)."""
    ids = [it["id"] for it in items]
    uf = UF(ids)
    by_id = {it["id"]: it for it in items}

    # signal 1: shared source host+path
    hp_index = defaultdict(list)
    for it in items:
        for hp in _host_paths(it):
            hp_index[hp].append(it["id"])
    for hp, group in hp_index.items():
        for other in group[1:]:
            uf.union(group[0], other)

    # signal 2: identical normalized gold
    gold_index = defaultdict(list)
    for it in items:
        g = _norm(it.get("gold_answer"))
        if g:
            gold_index[g].append(it["id"])
    for g, group in gold_index.items():
        for other in group[1:]:
            uf.union(group[0], other)

    # signal 3: question similarity > 0.85 ; 0.80..0.85 = ambiguous (flag, don't merge)
    ambiguous_pairs = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i], items[j]
            r = difflib.SequenceMatcher(None, _norm(a["question"]), _norm(b["question"])).ratio()
            if r > 0.85:
                uf.union(a["id"], b["id"])
            elif r >= 0.80 and uf.find(a["id"]) != uf.find(b["id"]):
                ambiguous_pairs.append((a["id"], b["id"], round(r, 3)))

    # name clusters deterministically: fact_id = "fact_<NNN>" ordered by smallest member id
    root_members = defaultdict(list)
    for i in ids:
        root_members[uf.find(i)].append(i)
    ordered_roots = sorted(root_members.values(), key=lambda m: sorted(m)[0])
    fact_by_id, clusters = {}, {}
    for n, members in enumerate(ordered_roots, 1):
        fid = f"fact_{n:03d}"
        clusters[fid] = sorted(members)
        for m in members:
            fact_by_id[m] = fid
    return fact_by_id, clusters, ambiguous_pairs


def split_by_fact(clusters):
    """~30% of DISTINCT fact_ids -> holdout, rest -> dev. Deterministic seeded shuffle.
    No fact_id in both (we partition fact_ids, not items)."""
    fids = sorted(clusters)
    rng = random.Random(SEED)
    rng.shuffle(fids)
    n_hold = max(1, round(len(fids) * HOLDOUT_FRAC)) if fids else 0
    holdout = set(fids[:n_hold])
    dev = set(fids[n_hold:])
    return dev, holdout


# ---------------------------------------------------------------- driver

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="re-probe items even if a receipt exists")
    ap.add_argument("--only", default="", help="comma-separated split filter (e.g. fresh,stable)")
    ap.add_argument("--ids", default="", help="comma-separated ids (debug subset)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--candidates", default=str(CANDIDATES),
                    help="path to the candidate .jsonl (default: datasets/candidates/candidates.jsonl)")
    args = ap.parse_args()
    candidates_path = Path(args.candidates)
    load_env()
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)

    rows = [json.loads(l) for l in open(candidates_path) if l.strip()]
    if args.only:
        want = set(args.only.split(","))
        rows = [r for r in rows if r.get("split") in want]
    if args.ids:
        want = set(args.ids.split(","))
        rows = [r for r in rows if r["id"] in want]
    if args.limit:
        rows = rows[:args.limit]

    # ---- probe pass (resumable) ----
    for r in rows:
        rc_path = RECEIPTS_DIR / f"{r['id']}.json"
        if rc_path.exists() and not args.force:
            print(f"skip  {r['id']:16} (receipt exists)", flush=True)
            continue
        split = r.get("split")
        fn = SPLIT_FN.get(split)
        if not fn:
            receipt = build_receipt(r, "needs_human", f"unknown_split_{split}", {}, {})
        else:
            try:
                verdict, reason, attrs, probes = fn(r)
                receipt = build_receipt(r, verdict, reason, attrs, probes)
            except Exception as e:
                receipt = build_receipt(r, "needs_human", f"probe_error:{e}", {}, {"error": str(e)})
        rc_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=1))
        print(f"{receipt['verdict']:12} {r['id']:16} {split:12} {receipt['reason']}", flush=True)

    # ---- load ALL receipts on disk for clustering + reporting ----
    receipts = {}
    for p in sorted(RECEIPTS_DIR.glob("*.json")):
        rc = json.loads(p.read_text())
        receipts[rc["id"]] = rc
    cand_by_id = {r["id"]: r for r in (json.loads(l) for l in open(candidates_path) if l.strip())}

    admitted = [cand_by_id[i] for i, rc in receipts.items() if rc["verdict"] == "admit" and i in cand_by_id]
    fact_by_id, clusters, ambiguous_pairs = cluster_fact_ids(admitted)

    # write fact_id back into receipts
    for i, fid in fact_by_id.items():
        receipts[i]["fact_id"] = fid
        (RECEIPTS_DIR / f"{i}.json").write_text(json.dumps(receipts[i], ensure_ascii=False, indent=1))

    dev_facts, holdout_facts = split_by_fact(clusters)

    DEV_DIR.mkdir(parents=True, exist_ok=True)
    HOLDOUT_DIR.mkdir(parents=True, exist_ok=True)

    def emit_split(fact_set, out_path):
        n = 0
        with open(out_path, "w") as f:
            for it in admitted:
                fid = fact_by_id[it["id"]]
                if fid in fact_set:
                    rec = dict(it)
                    rec["fact_id"] = fid
                    rec.pop("receipt", None)
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    n += 1
        return n

    n_dev = emit_split(dev_facts, DEV_DIR / "questions.jsonl")
    n_hold = emit_split(holdout_facts, HOLDOUT_DIR / "questions.jsonl")

    write_reports(receipts, cand_by_id, clusters, ambiguous_pairs, fact_by_id,
                  dev_facts, holdout_facts, n_dev, n_hold)
    print(f"\ndev={n_dev} items / {len(dev_facts)} facts   holdout={n_hold} items / {len(holdout_facts)} facts")
    print("done.")


def write_reports(receipts, cand_by_id, clusters, ambiguous_pairs, fact_by_id,
                  dev_facts, holdout_facts, n_dev, n_hold):
    # ---- counts ----
    per_split = defaultdict(Counter)
    for rc in receipts.values():
        per_split[rc["split"]][rc["verdict"]] += 1
    drops = [(rc["id"], rc["split"], rc["reason"]) for rc in receipts.values() if rc["verdict"] == "drop"]
    needs = [rc for rc in receipts.values() if rc["verdict"] == "needs_human"]

    # ---- HUMAN_QUEUE.md ----
    disputed = [rc for rc in needs if rc["split"] in ("fresh", "stable") and "gold_" in rc["reason"]]
    freshflag = [rc for rc in needs if rc["split"] == "fresh" and rc["reason"].startswith("freshness_not_confirmable")]
    recurring = [rc for rc in needs if rc["reason"] == "recurring_needs_valid_until"]
    unans = [rc for rc in needs if rc["split"] == "unanswerable"]
    multi_facts = {fid: mem for fid, mem in clusters.items() if len(mem) > 1}

    def panel_answers(rc):
        gv = rc.get("probes", {}).get("gold_verify", {})
        return " | ".join(f"{m.split('/')[-1]}={v.get('answer','')[:60]!r}" for m, v in (gv.get("panel") or {}).items())

    L = ["# study-1 — HUMAN QUEUE",
         "",
         f"Anchor {ANCHOR}. Every item here is `needs_human` (or an ambiguous cluster). Splits contain only `admit` items; nothing here is in dev/holdout yet.",
         "",
         f"Totals: {len(needs)} needs_human receipts + {len(ambiguous_pairs)} ambiguous cluster pairs.",
         ""]

    L += [f"## 1. Disputed / uncertain golds ({len(disputed)}) — panel did not confirm our gold",
          "The panel (with search) either agreed on a DIFFERENT answer (disputed) or split (uncertain). Decide: fix gold, or drop.",
          ""]
    for rc in sorted(disputed, key=lambda r: r["id"]):
        L.append(f"- **{rc['id']}** ({rc['split']}, {rc['reason']})  our_gold={rc['gold_answer']!r}")
        L.append(f"  - Q: {rc['question']}")
        L.append(f"  - panel: {panel_answers(rc)}")
    L.append("")

    L += [f"## 2. Recurring-event items needing valid_until ({len(recurring)})",
          "Gold is confirmed but the question is time-relative; sign a `valid_until` (proposed = event_date + ~358d).",
          ""]
    for rc in sorted(recurring, key=lambda r: r["id"]):
        tg = rc.get("probes", {}).get("temporal_guard", {})
        L.append(f"- **{rc['id']}**  gold={rc['gold_answer']!r}  proposed valid_until={tg.get('proposed_valid_until')}")
        L.append(f"  - Q: {rc['question']}")
    L.append("")

    if freshflag:
        L += [f"## 2b. Fresh items whose freshness could not be auto-confirmed ({len(freshflag)})",
              "Gold confirmed but event_date is missing / not in the past. Human: set/verify event_date.", ""]
        for rc in sorted(freshflag, key=lambda r: r["id"]):
            L.append(f"- **{rc['id']}**  ({rc['reason']})  Q: {rc['question']}")
        L.append("")

    L += [f"## 3. Unanswerable items — sign the negative ({len(unans)})",
          "Panel with search did not surface a specific answer. Human confirms the negative against the archived evidence URLs and the expires_on.",
          ""]
    for rc in sorted(unans, key=lambda r: r["id"]):
        uv = rc.get("probes", {}).get("unanswerable_verify", {})
        cand = cand_by_id.get(rc["id"], {})
        L.append(f"- **{rc['id']}**  ({rc['reason']})")
        L.append(f"  - Q: {rc['question']}")
        L.append(f"  - all_declined={uv.get('all_declined')}  src_urls={uv.get('source_urls_present')}  expires_ok={uv.get('expires_on_valid')} (expires_on={cand.get('expires_on')})")
        L.append(f"  - panel: " + " | ".join(f"{m.split('/')[-1]}={v.get('answer','')[:70]!r}" for m, v in (uv.get('panel') or {}).items()))
    L.append("")

    L += [f"## 4. Ambiguous fact clusters ({len(ambiguous_pairs)} near-threshold pairs)",
          "Question similarity in [0.80, 0.85): possibly the same fact. Human decides whether to merge fact_ids (matters for holdout leakage).",
          ""]
    for a, b, r in ambiguous_pairs:
        L.append(f"- {a}  ~{r}~  {b}")
    L.append("")
    L += [f"## 5. Multi-item fact clusters to confirm ({len(multi_facts)})",
          "These admitted items were auto-merged into one fact_id (shared source URL / identical gold / Q-sim>0.85). Confirm they are truly variants (holdout is split by fact_id).",
          ""]
    for fid, mem in sorted(multi_facts.items()):
        L.append(f"- {fid}: {', '.join(mem)}")
    (STUDY / "datasets" / "HUMAN_QUEUE.md").write_text("\n".join(L) + "\n")

    # ---- ADMISSION_SUMMARY.md ----
    S = ["# study-1 — ADMISSION SUMMARY", "",
         f"Anchor {ANCHOR}. Curator panel: {', '.join(PANEL)}. Provider: {PROVIDER}. Freshness window: 60d.",
         "", "## Verdicts per split", "",
         "| split | admit | drop | needs_human | total |", "|---|---|---|---|---|"]
    grand = Counter()
    for split in ("fresh", "stable", "unanswerable", "no_search"):
        c = per_split.get(split, Counter())
        tot = sum(c.values())
        grand.update(c)
        S.append(f"| {split} | {c['admit']} | {c['drop']} | {c['needs_human']} | {tot} |")
    S.append(f"| **all** | **{grand['admit']}** | **{grand['drop']}** | **{grand['needs_human']}** | **{sum(grand.values())}** |")
    S += ["",
          "## Splits (admit items only, split by fact_id)", "",
          f"- distinct admitted fact_ids: {len(clusters)}",
          f"- dev: {n_dev} items / {len(dev_facts)} facts",
          f"- holdout.sealed: {n_hold} items / {len(holdout_facts)} facts",
          f"- no fact_id appears in both (partitioned by fact_id).",
          "",
          f"## Dropped items ({len(drops)})", ""]
    for i, sp, reason in sorted(drops):
        S.append(f"- **{i}** ({sp}): {reason}")
    S += ["", "## needs_human queue composition", "",
          f"- total needs_human: {sum(1 for rc in receipts.values() if rc['verdict']=='needs_human')}"]
    reason_counts = Counter(rc["reason"].split(":")[0] for rc in receipts.values() if rc["verdict"] == "needs_human")
    for reason, n in reason_counts.most_common():
        S.append(f"  - {reason}: {n}")
    S += ["", f"- ambiguous fact-cluster pairs: {len(ambiguous_pairs)}",
          f"- multi-item fact clusters (auto-merged, confirm): {sum(1 for m in clusters.values() if len(m)>1)}",
          "", "See HUMAN_QUEUE.md for the actionable per-item list."]
    (STUDY / "ADMISSION_SUMMARY.md").write_text("\n".join(S) + "\n")


if __name__ == "__main__":
    main()
