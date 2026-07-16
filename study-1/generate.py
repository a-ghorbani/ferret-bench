#!/usr/bin/env python3
"""generate.py — produce NEW verified-benchmark CANDIDATES for study-1.

The dataset is the output of a validator (see CURATION-SPEC.md). This script only *proposes*
candidates; nothing here is admitted. Admission (gold re-verification, snippet_leak, temporal_guard,
resolve) is done by validate.py / resolve.py against whatever file we write. So generation aims for
plausible, well-sourced items and lets the existing pipeline filter.

Design (reuse only; no probe re-implementation):
  - Fresh items come from REAL recent events. We run harness/providers.search (brave, replay-or-live)
    with category-scoped, window-dated queries, collect real hits (title/snippet/url/publishedAt),
    and ask a frontier PANEL model to extract crisp Q&A facts that are supported by >=2 of the
    provided URLs and whose event_date falls in the freshness window. Each fact also gets 1-2
    phrasing VARIANTS (dated / undated / colloquial) sharing the same fact_id — variants are
    robustness probes, not new facts. Recurring-annual questions get an undated variant so
    temporal_guard exercises the valid_until path.
  - Unanswerable items: false-premise / unfindable questions about a REAL topic, citing real
    negative-evidence URLs from search, gold=NOT_FOUND, expires_on>anchor.
  - Stable items: timeless facts from the generator's own knowledge (gold_verify confirms later).
  - no_search items: creative/reasoning prompts a model should answer WITHOUT searching (no gold).

Anchor 2026-07-14, freshness window 60d -> fresh event_date in [2026-05-15, 2026-07-14).
Checkpointed: every item is appended to the output jsonl as soon as it is produced, and a small
state file records completed (split,category) chunks so a kill/re-run resumes without dup work.
Panel = openrouter:anthropic/claude-sonnet-5 + openrouter:openai/gpt-5.6-luna. temp 0.
"""
import argparse
import datetime
import json
import re
import sys
import urllib.parse
from collections import Counter
from pathlib import Path

STUDY = Path(__file__).resolve().parent
HARNESS = STUDY.parent / "harness"
sys.path.insert(0, str(HARNESS))

from common import load_env             # noqa: E402
from providers import search            # noqa: E402
from llm import chat                    # noqa: E402

ANCHOR = "2026-07-14"
ANCHOR_DATE = datetime.date.fromisoformat(ANCHOR)
WINDOW_DAYS = 60
WINDOW_START = ANCHOR_DATE - datetime.timedelta(days=WINDOW_DAYS)   # 2026-05-15
PROVIDER = "brave"
MODE = "replay-or-live"
GEN_MODEL = "openrouter:deepseek/deepseek-v4-flash"   # drafting model (in the panel)
GEN2_MODEL = "openrouter:openai/gpt-5.6-luna"         # second drafter, for a subset (diversity)
GEN = {"temperature": 0, "max_tokens": 2000}
ORIGIN = "gen1"

CAND_DIR = STUDY / "datasets" / "candidates"

# fresh category quotas (DISTINCT FACTS). CURATION-SPEC weights, scaled to the batch size.
FRESH_WEIGHTS = {
    "news": 0.20, "sports": 0.12, "tech": 0.12, "business": 0.12,
    "science": 0.12, "entertainment": 0.10, "politics": 0.10,
    "geography": 0.07, "other": 0.05,
}

PRESETS = {
    "pilot": {"out": "pilot.jsonl", "fresh": 24, "unanswerable": 6, "stable": 4, "no_search": 4},
    "full":  {"out": "generated_batch1.jsonl", "fresh": 150, "unanswerable": 30, "stable": 20, "no_search": 15},
}

# category -> search queries scoped to the window (May-Jul 2026)
FRESH_QUERIES = {
    "news": ["major world news June 2026", "breaking global headlines July 2026",
             "significant international events May 2026"],
    "sports": ["major sports championship result June 2026", "NBA Finals 2026 champion",
               "French Open 2026 winner", "Stanley Cup 2026 champion", "sports final July 2026 result"],
    "tech": ["major technology announcement June 2026", "new AI model released July 2026",
             "big tech product launch June 2026"],
    "business": ["major corporate acquisition June 2026", "company merger deal July 2026",
                 "notable business news June 2026 billion"],
    "science": ["scientific discovery June 2026", "space mission launch July 2026",
                "medical health breakthrough June 2026"],
    "entertainment": ["box office record June 2026", "major movie release July 2026",
                      "music award or album June 2026"],
    "politics": ["national election result June 2026", "government policy decision July 2026",
                 "world leaders summit June 2026"],
    "geography": ["major natural disaster June 2026", "notable local regional event July 2026"],
    "other": ["notable record-breaking event June 2026", "unusual newsworthy event July 2026"],
}

RECURRING_HINT_CATS = {"sports", "entertainment"}   # ask for an undated recurring variant here


# ------------------------------------------------------------------ small utilities

def quotas(total, weights):
    """Split `total` across weighted strata, largest-remainder so it sums exactly."""
    raw = {k: total * w for k, w in weights.items()}
    base = {k: int(v) for k, v in raw.items()}
    rem = total - sum(base.values())
    order = sorted(weights, key=lambda k: raw[k] - base[k], reverse=True)
    for k in order[:rem]:
        base[k] += 1
    return base


def _domain(u):
    try:
        return (urllib.parse.urlparse(u).hostname or "").lower().lstrip("www.")
    except ValueError:
        return ""


def collect_hits(queries, k=6):
    """Run each query through brave (replay-or-live), dedupe by url, keep title/snippet/url/date."""
    seen, pool = set(), []
    for q in queries:
        try:
            hits, _ = search(PROVIDER, q, k, MODE)
        except Exception as e:  # never kill the batch
            print(f"    [search failed {q!r}: {e}]", flush=True)
            continue
        for h in hits:
            u = h.get("url") or ""
            if not u or u in seen:
                continue
            seen.add(u)
            pool.append({"title": (h.get("title") or "")[:160],
                         "snippet": (h.get("snippet") or "")[:220],
                         "url": u, "publishedAt": h.get("publishedAt")})
    return pool


def _salvage_objects(text):
    """Recover every complete top-level {...} object from a (possibly TRUNCATED) JSON array.
    A large-n generation can exceed max_tokens and cut the array mid-way; rather than lose the
    whole chunk we parse object-by-object via brace-depth scanning and keep the ones that closed."""
    out, depth, start, in_str, esc = [], 0, None, False, False
    for k, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = k
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    out.append(json.loads(text[start:k + 1]))
                except json.JSONDecodeError:
                    pass
                start = None
    return out


def _parse_json_array(text):
    """Extract JSON objects from a model reply (tolerates ``` fences, prose, and TRUNCATION)."""
    if not text:
        return []
    text = re.sub(r"```(?:json)?", "", text).strip("` \n")
    i, j = text.find("["), text.rfind("]")
    if i >= 0 and j > i:
        try:
            return json.loads(text[i:j + 1])
        except json.JSONDecodeError:
            cleaned = re.sub(r",\s*([\]}])", r"\1", text[i:j + 1])
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass
    # whole-array parse failed (often truncation) -> salvage complete objects
    return _salvage_objects(text)


def _gen(model, prompt):
    resp = chat(model, [{"role": "user", "content": prompt}], gen=GEN)
    return (resp["choices"][0]["message"].get("content") or "").strip()


def in_window(ed):
    try:
        d = datetime.date.fromisoformat(ed)
    except (TypeError, ValueError):
        return False
    return WINDOW_START <= d < ANCHOR_DATE


# ------------------------------------------------------------------ checkpoint state

class Checkpoint:
    def __init__(self, out_path):
        self.out_path = out_path
        self.state_path = out_path.with_suffix(".state.json")
        self.done = set()
        self.ids = set()
        if out_path.exists():
            for l in out_path.read_text().splitlines():
                if l.strip():
                    self.ids.add(json.loads(l)["id"])
        if self.state_path.exists():
            self.done = set(json.loads(self.state_path.read_text()).get("done_chunks", []))

    def chunk_done(self, key):
        return key in self.done

    def append(self, item):
        if item["id"] in self.ids:
            return
        with open(self.out_path, "a") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
        self.ids.add(item["id"])

    def mark(self, key):
        self.done.add(key)
        self.state_path.write_text(json.dumps({"done_chunks": sorted(self.done)}, indent=1))


# ------------------------------------------------------------------ FRESH

FRESH_PROMPT = """You are curating a RETRIEVAL benchmark of RECENT real-world events. Today's date is {anchor}.
Using ONLY the search results below (do NOT use your own memory — it is stale for events this recent),
produce {n} distinct factual Q&A items about events in the "{cat}" category that happened
between {wstart} and {wend} (inclusive of the start, before the anchor).

Hard rules for every item:
- The answer must be a CRISP, unambiguous fact (a name, number, score, date, or short phrase).
- event_date must be a real date in [{wstart}, {wend}) that you can support from the results.
- source_urls: pick >=2 URLs FROM THE LIST BELOW that support the fact, and prefer different domains.
- Only include an item if the results genuinely support it. Fewer good items beats padded guesses.
- Each item's `question` should be self-contained. Set "dated": true if the question names its own
  year/month, false otherwise.
{recurring_note}
For each fact also give 1-2 "variants": alternate phrasings of the SAME fact (e.g. a dated version,
an undated version, and/or a colloquial/casual version). Variants share the fact; they are not new facts.

Return ONLY a JSON array; each element:
{{
  "question": "...",
  "gold_answer": "crisp answer",
  "acceptable_answers": ["equivalent phrasings of the answer"],
  "event_date": "YYYY-MM-DD",
  "dated": true,
  "recurring": false,
  "source_urls": ["https://...", "https://..."],
  "variants": [{{"question": "alt phrasing", "dated": false, "recurring": false}}]
}}

Search results (title — snippet — url — publishedAt):
{results}
"""

RECURRING_NOTE = ("- At least one item should be a RECURRING annual event (a championship / award "
                  "final). For that item, include an UNDATED colloquial variant that names the event "
                  "but NOT the year (e.g. \"who won the french open men's singles?\"), with "
                  "\"dated\": false and \"recurring\": true.\n")


def gen_fresh(cp, quota_map):
    for cat, n in quota_map.items():
        key = f"fresh:{cat}"
        if n <= 0 or cp.chunk_done(key):
            print(f"  skip fresh/{cat} (done or n=0)", flush=True)
            continue
        print(f"  fresh/{cat}: target {n} facts", flush=True)
        pool = collect_hits(FRESH_QUERIES.get(cat, []))
        if not pool:
            print(f"    no hits for {cat}; skipping", flush=True)
            cp.mark(key)
            continue
        results = "\n".join(f"- {h['title']} — {h['snippet']} — {h['url']} — {h.get('publishedAt')}"
                            for h in pool)
        pool_urls = {h["url"] for h in pool}
        prompt = FRESH_PROMPT.format(
            anchor=ANCHOR, n=n + 1, cat=cat, wstart=WINDOW_START.isoformat(),
            wend=ANCHOR, results=results,
            recurring_note=RECURRING_NOTE if cat in RECURRING_HINT_CATS else "")
        model = GEN_MODEL if cat not in {"tech", "business", "geography"} else GEN2_MODEL
        try:
            facts = _parse_json_array(_gen(model, prompt))
        except Exception as e:
            # gen call itself failed (e.g. 402/transient) -> do NOT mark done, so a re-run retries
            print(f"    [gen failed {cat}: {e}] (chunk left unmarked for resume)", flush=True)
            continue
        kept = 0
        for f in facts:
            if kept >= n:
                break
            if not isinstance(f, dict):
                continue
            q = (f.get("question") or "").strip()
            gold = (f.get("gold_answer") or "").strip()
            ed = f.get("event_date")
            if not q or not gold or not in_window(ed):
                continue
            urls = [u for u in (f.get("source_urls") or []) if u in pool_urls]
            if len({_domain(u) for u in urls}) < 2:
                # try to backfill from pool by keeping any >=2 distinct-domain cited urls
                continue
            fid = f"g1f-{cat}-{kept + 1:02d}"
            base = {
                "id": fid, "split": "fresh", "question": q,
                "gold_answer": gold,
                "acceptable_answers": [a for a in (f.get("acceptable_answers") or []) if a][:6],
                "category": cat, "source_urls": urls[:4], "event_date": ed,
                "dated": bool(f.get("dated", True)), "origin": ORIGIN,
                "origin_tier": None, "fact_id": fid,
                "notes": f"generated from {len(urls)} sources; recurring={bool(f.get('recurring'))}",
                "attributes": {}, "receipt": None,
            }
            cp.append(base)
            # variants (share fact_id) — separate rows, own dated/recurring flags
            for vi, v in enumerate(f.get("variants") or [], 1):
                if vi > 2:
                    break
                vq = (v.get("question") or "").strip()
                if not vq or vq.lower() == q.lower():
                    continue
                var = dict(base)
                var["id"] = f"{fid}v{vi}"
                var["question"] = vq
                var["dated"] = bool(v.get("dated", False))
                var["notes"] = f"phrasing variant of {fid} (not a new fact)"
                cp.append(var)
            kept += 1
        print(f"    kept {kept}/{n} facts for {cat}", flush=True)
        cp.mark(key)


# ------------------------------------------------------------------ UNANSWERABLE

UNANS_PROMPT = """You are curating UNANSWERABLE probes for a retrieval benchmark. Today is {anchor}.
Produce {n} questions that CANNOT be truthfully answered, of these flavours:
  - false_premise: presupposes an event/deal/record that never happened,
  - unfindable: asks for a specific fact that is not publicly available,
  - undetermined: asks for something not yet decided as of the anchor.
Use the REAL topics/entities in the search results so the questions are about real things but have
no true answer. For each, cite 1-2 real URLs FROM THE LIST as NEGATIVE evidence (pages that show the
true state of the entity, contradicting the false premise / showing the fact is absent).

Return ONLY a JSON array; each element:
{{
  "question": "...",
  "flavour": "false_premise | unfindable | undetermined",
  "acceptable_behaviour": "says it cannot find an answer / the premise is false / it is undetermined",
  "source_urls": ["https://..."],
  "expires_on": "2099-01-01",
  "category": "one of news/sports/tech/business/science/entertainment/politics/geography/other"
}}
Use expires_on 2099-01-01 for things that will NEVER be answerable; for 'undetermined' use a plausible
future date AFTER {anchor}.

Search results (title — snippet — url):
{results}
"""


def gen_unanswerable(cp, n):
    key = "unanswerable:all"
    if cp.chunk_done(key):
        print("  skip unanswerable (done)", flush=True)
        return
    print(f"  unanswerable: target {n}", flush=True)
    # topical pool from a few categories so the false premises are about real recent entities
    pool = collect_hits(["major technology company news June 2026", "business acquisition rumor 2026",
                         "sports transfer news June 2026", "science research June 2026"], k=6)
    results = "\n".join(f"- {h['title']} — {h['snippet']} — {h['url']}" for h in pool)
    pool_urls = {h["url"] for h in pool}
    prompt = UNANS_PROMPT.format(anchor=ANCHOR, n=n + 2, results=results)
    try:
        items = _parse_json_array(_gen(GEN_MODEL, prompt))
    except Exception as e:
        print(f"    [gen failed unanswerable: {e}] (chunk left unmarked for resume)", flush=True)
        return
    kept = 0
    for it in items:
        if kept >= n or not isinstance(it, dict):
            continue
        q = (it.get("question") or "").strip()
        if not q:
            continue
        urls = [u for u in (it.get("source_urls") or []) if u in pool_urls][:2]
        if not urls:
            continue
        exp = it.get("expires_on") or "2099-01-01"
        if exp <= ANCHOR:
            exp = "2099-01-01"
        cp.append({
            "id": f"g1u-{kept + 1:02d}", "split": "unanswerable", "question": q,
            "gold_answer": "NOT_FOUND",
            "acceptable_behaviour": it.get("acceptable_behaviour") or "cannot find a specific answer",
            "category": it.get("category") or "other", "source_urls": urls,
            "expires_on": exp, "flavour": it.get("flavour") or "false_premise",
            "origin": ORIGIN, "origin_tier": None,
            "notes": "generated unanswerable probe", "attributes": {}, "receipt": None,
        })
        kept += 1
    print(f"    kept {kept}/{n} unanswerable", flush=True)
    cp.mark(key)


# ------------------------------------------------------------------ STABLE + NO_SEARCH (from knowledge)

STABLE_PROMPT = """Produce {n} timeless general-knowledge Q&A facts (true regardless of date; NOT
recent-events). Vary the category (history/geography/science/tech/sports/entertainment). Each answer
must be a single crisp fact (name/number/year). Return ONLY a JSON array:
[{{"question": "...", "gold_answer": "...", "acceptable_answers": ["..."], "category": "..."}}]
"""

NOSEARCH_PROMPT = """Produce {n} prompts that a language model should answer WITHOUT any web search —
creative writing, reasoning, math, or explanation tasks (no lookup of current facts). These are
false-positive probes: a good model must NOT trigger a search. Return ONLY a JSON array:
[{{"question": "...", "category": "creative|math|reasoning|writing|explain"}}]
"""


def gen_stable(cp, n):
    key = "stable:all"
    if cp.chunk_done(key):
        print("  skip stable (done)", flush=True)
        return
    print(f"  stable: target {n}", flush=True)
    try:
        items = _parse_json_array(_gen(GEN_MODEL, STABLE_PROMPT.format(n=n + 1)))
    except Exception as e:
        print(f"    [gen failed stable: {e}] (chunk left unmarked for resume)", flush=True)
        return
    kept = 0
    for it in items:
        if kept >= n or not isinstance(it, dict):
            continue
        q = (it.get("question") or "").strip()
        gold = (it.get("gold_answer") or "").strip()
        if not q or not gold:
            continue
        cp.append({
            "id": f"g1s-{kept + 1:02d}", "split": "stable", "question": q,
            "gold_answer": gold,
            "acceptable_answers": [a for a in (it.get("acceptable_answers") or []) if a][:5] or [gold],
            "category": it.get("category") or "general", "origin": ORIGIN, "origin_tier": None,
            "notes": "generated stable fact", "attributes": {}, "receipt": None,
        })
        kept += 1
    print(f"    kept {kept}/{n} stable", flush=True)
    cp.mark(key)


def gen_no_search(cp, n):
    key = "no_search:all"
    if cp.chunk_done(key):
        print("  skip no_search (done)", flush=True)
        return
    print(f"  no_search: target {n}", flush=True)
    try:
        items = _parse_json_array(_gen(GEN_MODEL, NOSEARCH_PROMPT.format(n=n + 1)))
    except Exception as e:
        print(f"    [gen failed no_search: {e}] (chunk left unmarked for resume)", flush=True)
        return
    kept = 0
    for it in items:
        if kept >= n or not isinstance(it, dict):
            continue
        q = (it.get("question") or "").strip()
        if not q:
            continue
        cp.append({
            "id": f"g1n-{kept + 1:02d}", "split": "no_search", "question": q,
            "gold_answer": None, "category": it.get("category") or "creative",
            "origin": ORIGIN, "origin_tier": None, "notes": "generated no_search probe",
            "attributes": {}, "receipt": None,
        })
        kept += 1
    print(f"    kept {kept}/{n} no_search", flush=True)
    cp.mark(key)


# ------------------------------------------------------------------ driver

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", choices=list(PRESETS), default="pilot")
    ap.add_argument("--out", default="", help="override output filename (in datasets/candidates/)")
    ap.add_argument("--only", default="", help="comma splits to gen (fresh,unanswerable,stable,no_search)")
    args = ap.parse_args()
    load_env()

    cfg = PRESETS[args.preset]
    out_path = CAND_DIR / (args.out or cfg["out"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cp = Checkpoint(out_path)
    only = set(args.only.split(",")) if args.only else set(PRESETS[args.preset]) - {"out"}

    print(f"generate.py preset={args.preset} -> {out_path.name}  anchor={ANCHOR} "
          f"window=[{WINDOW_START},{ANCHOR})", flush=True)

    if "fresh" in only:
        qm = quotas(cfg["fresh"], FRESH_WEIGHTS)
        print("fresh quotas:", qm, flush=True)
        gen_fresh(cp, qm)
    if "unanswerable" in only:
        gen_unanswerable(cp, cfg["unanswerable"])
    if "stable" in only:
        gen_stable(cp, cfg["stable"])
    if "no_search" in only:
        gen_no_search(cp, cfg["no_search"])

    rows = [json.loads(l) for l in out_path.read_text().splitlines() if l.strip()]
    by_split = Counter(r["split"] for r in rows)
    facts = len({r.get("fact_id", r["id"]) for r in rows if r["split"] == "fresh"})
    print(f"\nwrote {out_path} : {len(rows)} items")
    print(f"  by split: {dict(by_split)}")
    print(f"  fresh distinct facts (by generator fact_id): {facts}")


if __name__ == "__main__":
    main()
