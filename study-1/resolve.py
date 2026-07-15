#!/usr/bin/env python3
"""resolve.py — auto-clear the 28 `needs_human` receipts with an LLM/agentic loop, NO human review.

Guiding rule (owner): dropping is cheap, candidates are abundant. Anything that does not cleanly
settle is DROPPED, not escalated. The frontier panel is the truth oracle for golds.

Per queue category (receipt['reason']):
  gold_disputed_* / gold_uncertain_*  -> re-run the AGENTIC panel (search+read). Judge answer-equality
      with a small LLM (semantic, not substring). Panel agrees on one specific answer -> overwrite gold
      + admit. Otherwise -> drop.
  recurring_needs_valid_until         -> one agentic lookup for the next occurrence date -> set
      valid_until + admit. Not determinable -> keep the +358d proposal + admit (low risk).
  unanswerable_confirmed_*            -> run the panel WITH search, told to try hard. All decline ->
      admit unanswerable (gold=NOT_FOUND). Any credible specific answer -> drop (it was answerable).

After resolving: rewrite each receipt (verdict/resolution/resolved_gold/valid_until), rebuild the
dev + holdout.sealed splits from ALL admitted items (recluster by fact_id, ~30% of facts to holdout),
and write RESOLUTION_SUMMARY.md + a JOURNAL.md entry.

Reuses: harness/agent_loop.run_agent, configs.load_config, llm.chat, gold_verify._matches/_norm,
and validate.cluster_fact_ids / split_by_fact. temp 0, small token budgets, replay-or-live search.
On per-item error: record and continue — never abort the batch.
"""
import argparse
import datetime
import json
import re
import sys
from collections import Counter
from pathlib import Path

STUDY = Path(__file__).resolve().parent
HARNESS = STUDY.parent / "harness"
for p in (str(HARNESS), str(STUDY / "probes"), str(STUDY)):
    if p not in sys.path:
        sys.path.insert(0, p)

from common import load_env            # noqa: E402
from llm import chat                   # noqa: E402
from agent_loop import run_agent       # noqa: E402
from configs import load_config        # noqa: E402
from gold_verify import _norm          # noqa: E402
import validate                        # noqa: E402  (cluster_fact_ids, split_by_fact, SEED, HOLDOUT_FRAC)

CANDIDATES = STUDY / "datasets" / "candidates" / "candidates.jsonl"
RECEIPTS_DIR = STUDY / "verification" / "receipts"
DEV = STUDY / "datasets" / "dev" / "questions.jsonl"
HOLDOUT = STUDY / "datasets" / "holdout.sealed" / "questions.jsonl"

PANEL = ["openrouter:anthropic/claude-sonnet-5", "openrouter:openai/gpt-5.6-luna"]
EQ_JUDGE = "openrouter:openai/gpt-4o-mini"   # small LLM, disjoint family for equality/credibility calls
ANCHOR = "2026-07-14"
ANCHOR_DATE = datetime.date.fromisoformat(ANCHOR)
MODE = "replay-or-live"

DECLINE_RE = re.compile(
    r"nobodyknows|not ?found|cannot (find|determine|be answered|be found)|could ?n.?t find|"
    r"unable to (find|determine)|no (specific|credible|reliable|confirmed|public|official|record|"
    r"evidence|information|answer|such)|does ?n.?t exist|no such|has (not|n.?t) (been )?"
    r"(announced|awarded|disclosed|released|decided|happened|occurred)|not (yet )?(been )?"
    r"(announced|awarded|disclosed|public|available)|hasn.?t (happened|occurred|been)|"
    r"i (don.?t|do not) know|unknown|false premise|premise is (false|incorrect)|hypothetical|"
    r"fictional|did not (happen|occur)|never (happened|occurred)",
    re.I)


# ------------------------------------------------------------------ LLM helpers

def _agentic(question, model):
    """Run one question through the shipped ReAct loop (search+read). Returns (answer_or_None, rec)."""
    cfg = load_config("frozen")
    cfg["gen"] = {"temperature": 0, "max_tokens": 512}
    try:
        rec = run_agent(question, model, cfg, ANCHOR, MODE, seed=0)
    except Exception as e:
        return None, {"error": str(e)}
    if rec.get("error"):
        return None, rec
    return (rec.get("final_answer") or "").strip(), rec


def _small(prompt, max_tokens=8):
    resp = chat(EQ_JUDGE, [{"role": "user", "content": prompt}],
                gen={"temperature": 0, "max_tokens": max_tokens})
    return (resp["choices"][0]["message"].get("content") or "").strip()


def is_decline(ans):
    return (not ans) or bool(DECLINE_RE.search(ans))


def answers_equal(a, b):
    """Small-LLM semantic equality: 'Évian'=='Evian', 'PSG'=='Paris Saint-Germain', word-order etc."""
    prompt = (
        "Do these two answers refer to the SAME answer, allowing differences in spelling, "
        "diacritics, word order, abbreviations, or extra descriptive words "
        "(e.g. 'Évian-les-Bains'=='Evian', 'PSG'=='Paris Saint-Germain')? "
        "Reply with exactly YES or NO.\n\nAnswer A: " + a + "\nAnswer B: " + b)
    try:
        return "yes" in _small(prompt).lower()
    except Exception:
        return _norm(a) == _norm(b) and bool(_norm(a))


def concise_gold(question, a, b):
    """Collapse two agreeing verbose answers into one short canonical gold (substring-matchable)."""
    prompt = (
        "Question: " + question + "\nTwo answers that agree:\n1) " + a + "\n2) " + b +
        "\n\nReply with the single canonical answer as a SHORT phrase (a name, number, or a few "
        "words) with no explanation, no punctuation-heavy formatting.")
    try:
        out = _small(prompt, max_tokens=30).strip().strip('"').strip()
        return out or a
    except Exception:
        return a


def is_specific(question, ans):
    """Small-LLM: does `ans` give a concrete credible answer, or decline? Conservative on error."""
    if is_decline(ans):
        return False
    prompt = (
        "Question: " + question + "\nResponse: " + ans +
        "\n\nDoes the response give a SPECIFIC, credible factual answer to the question "
        "(a concrete name/number/date/fact), or does it decline / say it cannot find one / "
        "that no answer exists? Reply with exactly SPECIFIC or DECLINE.")
    try:
        return "specific" in _small(prompt).lower()
    except Exception:
        return False


# ------------------------------------------------------------------ per-category resolvers
# each returns (verdict, patch) where patch may hold resolved_gold / valid_until / resolution / probe

def resolve_disputed(item, rc):
    q = item["question"]
    a1, r1 = _agentic(q, PANEL[0])
    a2, r2 = _agentic(q, PANEL[1])
    probe = {"mode": "agentic", "panel": {
        PANEL[0]: {"answer": (a1 or "[error]")[:400], "n_reads": (r1 or {}).get("n_reads")},
        PANEL[1]: {"answer": (a2 or "[error]")[:400], "n_reads": (r2 or {}).get("n_reads")}}}
    if is_decline(a1) or is_decline(a2):
        return "drop", {"resolution": f"agentic panel did not both produce a specific answer "
                        f"(a='{(a1 or '')[:40]}', b='{(a2 or '')[:40]}') -> drop", "resolution_probe": probe}
    if answers_equal(a1, a2):
        gold = concise_gold(q, a1, a2)
        return "admit", {"resolved_gold": gold, "resolution":
                         f"agentic panel converged; gold overwritten '{item['gold_answer']}' -> '{gold}'",
                         "resolution_probe": probe}
    return "drop", {"resolution": f"agentic panel disagreed (a='{(a1 or '')[:40]}', "
                    f"b='{(a2 or '')[:40]}') -> drop", "resolution_probe": probe}


def resolve_recurring(item, rc):
    q = item["question"]
    gold = item.get("gold_answer")
    proposed = (rc.get("probes", {}).get("temporal_guard", {}) or {}).get("proposed_valid_until")
    lookup = (f'Recurring event in this question: "{q}" (most recent result: {gold}). '
              f'When is the NEXT edition expected to conclude/be decided after {ANCHOR}? '
              f'Reply with just the expected date as YYYY-MM-DD, or UNKNOWN.')
    ans, _ = _agentic(lookup, PANEL[0])
    m = re.search(r"\d{4}-\d{2}-\d{2}", ans or "")
    vu, src = None, None
    if m:
        try:
            d = datetime.date.fromisoformat(m.group(0))
            if d > ANCHOR_DATE:
                vu, src = m.group(0), "agentic_lookup"
        except ValueError:
            pass
    if not vu:
        vu, src = proposed, "fallback_proposed_+358d"
    return "admit", {"valid_until": vu, "resolution":
                     f"recurring; valid_until={vu} ({src}); lookup='{(ans or '')[:50]}'"}


def resolve_unanswerable(item, rc):
    q = item["question"]
    nudge = (q + "\n\n(Search thoroughly across multiple sources and give the specific factual "
             "answer if one genuinely exists. Only conclude no answer exists if you truly cannot "
             "find a credible specific answer.)")
    a1, _ = _agentic(nudge, PANEL[0])
    a2, _ = _agentic(nudge, PANEL[1])
    s1, s2 = is_specific(q, a1), is_specific(q, a2)
    probe = {"mode": "agentic_tryhard", "panel": {
        PANEL[0]: {"answer": (a1 or "[error]")[:400], "specific": s1},
        PANEL[1]: {"answer": (a2 or "[error]")[:400], "specific": s2}}}
    if s1 or s2:
        who = PANEL[0] if s1 else PANEL[1]
        return "drop", {"resolution": f"a panel model ({who.split('/')[-1]}) found a credible "
                        f"specific answer -> answerable -> drop", "resolution_probe": probe}
    return "admit", {"resolution": "panel declined with search -> admit as unanswerable "
                     "(gold=NOT_FOUND)", "resolution_probe": probe}


RESOLVERS = {
    "gold_disputed_panel_agrees_other": ("disputed", resolve_disputed),
    "gold_uncertain_panel_split": ("disputed", resolve_disputed),
    "recurring_needs_valid_until": ("recurring", resolve_recurring),
    "unanswerable_confirmed_awaiting_negative_signoff": ("unanswerable", resolve_unanswerable),
}


# ------------------------------------------------------------------ split rebuild

def rebuild_splits(receipts, cand_by_id):
    """Recluster ALL admitted items by fact_id and re-split ~30% of facts to holdout.
    Admitted candidate records carry resolved_gold / valid_until. NOT_FOUND golds are blanked
    for clustering only, so the 13 unanswerables don't collapse into one sentinel fact."""
    admitted_ids = [i for i, rc in receipts.items() if rc["verdict"] == "admit" and i in cand_by_id]

    def resolved_record(i):
        rec = dict(cand_by_id[i])
        rc = receipts[i]
        if rc.get("resolved_gold"):
            rec["gold_answer"] = rc["resolved_gold"]
        if rc.get("valid_until"):
            rec["valid_until"] = rc["valid_until"]
        return rec

    records = {i: resolved_record(i) for i in admitted_ids}
    # clustering input: blank NOT_FOUND gold so signal-2 (identical gold) doesn't merge unanswerables
    cluster_in = []
    for i in admitted_ids:
        c = dict(records[i])
        if _norm(c.get("gold_answer")) == _norm("NOT_FOUND"):
            c["gold_answer"] = ""
        cluster_in.append(c)

    fact_by_id, clusters, _amb = validate.cluster_fact_ids(cluster_in)
    dev_facts, holdout_facts = validate.split_by_fact(clusters)

    def emit(fact_set, path):
        n = 0
        with open(path, "w") as f:
            for i in admitted_ids:
                fid = fact_by_id[i]
                if fid in fact_set:
                    rec = records[i]
                    rec["fact_id"] = fid
                    rec.pop("receipt", None)
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    n += 1
        return n

    # write fact_id back into all receipts for consistency
    for i, fid in fact_by_id.items():
        receipts[i]["fact_id"] = fid
        (RECEIPTS_DIR / f"{i}.json").write_text(json.dumps(receipts[i], ensure_ascii=False, indent=1))

    n_dev = emit(dev_facts, DEV)
    n_hold = emit(holdout_facts, HOLDOUT)
    return n_dev, len(dev_facts), n_hold, len(holdout_facts)


# ------------------------------------------------------------------ driver

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", default="", help="comma-separated receipt ids (smoke test subset)")
    ap.add_argument("--no-rebuild", action="store_true", help="resolve only, skip split rebuild")
    args = ap.parse_args()
    load_env()

    receipts = {}
    for p in sorted(RECEIPTS_DIR.glob("*.json")):
        rc = json.loads(p.read_text())
        receipts[rc["id"]] = rc
    cand_by_id = {r["id"]: r for r in (json.loads(l) for l in open(CANDIDATES) if l.strip())}

    todo = [i for i, rc in receipts.items() if rc["verdict"] == "needs_human"]
    if args.ids:
        want = set(args.ids.split(","))
        todo = [i for i in todo if i in want]

    cat_counts = Counter()   # (category, verdict)
    overwritten = []         # (id, old, new)
    print(f"resolving {len(todo)} needs_human items...\n", flush=True)

    for i in todo:
        rc = receipts[i]
        item = cand_by_id.get(i, {})
        reason = rc.get("reason", "")
        cat, fn = RESOLVERS.get(reason, (None, None))
        if not fn:
            cat_counts[("unknown", "drop")] += 1
            rc.update(verdict="drop", resolution=f"no resolver for reason '{reason}' -> drop")
            (RECEIPTS_DIR / f"{i}.json").write_text(json.dumps(rc, ensure_ascii=False, indent=1))
            print(f"  drop   {i:14} unknown reason {reason}", flush=True)
            continue
        try:
            verdict, patch = fn(item, rc)
        except Exception as e:  # never kill the batch
            verdict, patch = "drop", {"resolution": f"resolution error: {e} -> drop"}
        rc["verdict"] = verdict
        rc["human_signed"] = False
        rc["auto_resolved"] = True
        for k, v in patch.items():
            rc[k] = v
        if patch.get("resolved_gold"):
            overwritten.append((i, item.get("gold_answer"), patch["resolved_gold"]))
        (RECEIPTS_DIR / f"{i}.json").write_text(json.dumps(rc, ensure_ascii=False, indent=1))
        cat_counts[(cat, verdict)] += 1
        print(f"  {verdict:6} {i:14} [{cat}] {patch.get('resolution','')[:80]}", flush=True)

    if args.no_rebuild:
        print("\n--no-rebuild set; skipping split rebuild.")
        return

    n_dev, f_dev, n_hold, f_hold = rebuild_splits(receipts, cand_by_id)
    print(f"\nrebuilt splits: dev={n_dev} items / {f_dev} facts   holdout={n_hold} items / {f_hold} facts")

    write_summary(receipts, cand_by_id, cat_counts, overwritten, n_dev, f_dev, n_hold, f_hold)
    append_journal(cat_counts, overwritten, n_dev, f_dev, n_hold, f_hold)
    print("done.")


def write_summary(receipts, cand_by_id, cat_counts, overwritten, n_dev, f_dev, n_hold, f_hold):
    cats = ["disputed", "recurring", "unanswerable", "unknown"]
    L = ["# study-1 — RESOLUTION SUMMARY", "",
         f"Anchor {ANCHOR}. Auto-resolution of the 28 `needs_human` items — NO human review "
         "(owner rule: anything that does not cleanly settle is DROPPED). Panel (agentic, "
         "search+read) = openrouter:anthropic/claude-sonnet-5 + openrouter:openai/gpt-5.6-luna; "
         "equality/credibility judge = openrouter:openai/gpt-4o-mini.", "",
         "## Resolved per queue category", "",
         "| category | admit | drop |", "|---|---|---|"]
    for c in cats:
        a, d = cat_counts.get((c, "admit"), 0), cat_counts.get((c, "drop"), 0)
        if a or d:
            L.append(f"| {c} | {a} | {d} |")
    total_admit = sum(v for (c, v_), v in cat_counts.items() if v_ == "admit")
    total_drop = sum(v for (c, v_), v in cat_counts.items() if v_ == "drop")
    L += ["", f"**Total: {total_admit} resolved-admit, {total_drop} dropped.**", "",
          "## Golds overwritten (panel is the oracle)", ""]
    if overwritten:
        for i, old, new in overwritten:
            L.append(f"- **{i}**: `{old}` -> `{new}`")
    else:
        L.append("- (none)")
    # dropped list with reasons
    dropped = [(i, rc.get("reason", ""), rc.get("resolution", "")) for i, rc in receipts.items()
               if rc.get("verdict") == "drop" and rc.get("auto_resolved")]
    L += ["", "## Dropped items", ""]
    if dropped:
        for i, reason, res in sorted(dropped):
            L.append(f"- **{i}** ({reason}): {res}")
    else:
        L.append("- (none)")
    n_admit = sum(1 for rc in receipts.values() if rc["verdict"] == "admit")
    L += ["", "## Splits (rebuilt from ALL admitted items, split by fact_id)", "",
          f"- total admitted items: {n_admit}",
          f"- dev: {n_dev} items / {f_dev} facts",
          f"- holdout.sealed: {n_hold} items / {f_hold} facts",
          f"- no fact_id appears in both (partitioned by fact_id).", ""]
    (STUDY / "RESOLUTION_SUMMARY.md").write_text("\n".join(L) + "\n")


def append_journal(cat_counts, overwritten, n_dev, f_dev, n_hold, f_hold):
    ta = sum(v for (c, v_), v in cat_counts.items() if v_ == "admit")
    td = sum(v for (c, v_), v in cat_counts.items() if v_ == "drop")
    today = datetime.date.today().isoformat()
    entry = [
        "", f"## {today} — auto-resolution of the 28 needs_human items (resolve.py)", "",
        f"Ran `resolve.py`: cleared the human queue with an agentic panel + small-LLM judges, no "
        f"human review. Owner rule applied — anything that did not cleanly settle was DROPPED.",
        f"- **{ta} resolved-admit, {td} dropped** across disputed / recurring / unanswerable.",
        f"- Golds overwritten (panel oracle): "
        + ("; ".join(f"{i} '{old}'->'{new}'" for i, old, new in overwritten) if overwritten else "none")
        + ".",
        f"- Rebuilt splits from ALL admitted items: dev={n_dev} items/{f_dev} facts, "
        f"holdout.sealed={n_hold} items/{f_hold} facts (split by fact_id, ~30% facts to holdout).",
        "- Method: disputed -> agentic panel re-run + small-LLM equality (Évian==Evian) -> converge "
        "= overwrite gold+admit else drop; recurring -> agentic next-occurrence lookup -> set "
        "valid_until (fallback +358d) + admit; unanswerable -> agentic try-hard panel -> all decline "
        "= admit NOT_FOUND, any specific answer = drop.",
    ]
    with open(STUDY / "JOURNAL.md", "a") as f:
        f.write("\n".join(entry) + "\n")


if __name__ == "__main__":
    main()
