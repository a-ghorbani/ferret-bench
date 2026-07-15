#!/usr/bin/env python3
"""gold_verify_agentic — the TRUTH oracle for MULTI-HOP (origin_tier T3/T4) candidates.

Single-shot gold_verify.py hands the panel one page of snippets. A genuine multi-hop question
cannot be answered from one snippet page by construction, so single-shot would spuriously return
gold_uncertain on perfectly good multi-hop items. Instead we run each frontier panel model through
the SHIPPED ReAct loop (harness/agent_loop.run_agent) with real web_search + read_url tools, let it
search/read across multiple turns, and check its FINAL answer against the gold.

Verdict semantics mirror gold_verify.py:
  unanimous match  -> gold_confirmed
  unanimous miss   -> gold_disputed
  split            -> gold_uncertain

Reuses harness/agent_loop.run_agent (loop), harness/configs.load_config (shipped-ish cfg,
provider=brave), and gold_verify._matches / _norm (identical gold-matching). No reimplementation.
"""
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[2] / "harness"
sys.path.insert(0, str(HARNESS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_loop import run_agent            # noqa: E402  the shipped ReAct loop
from configs import load_config             # noqa: E402
from gold_verify import _matches            # noqa: E402  identical gold matcher

PANEL = ["openrouter:anthropic/claude-sonnet-5", "openrouter:openai/gpt-5.6-luna"]


def _agentic_cfg():
    """frozen config (provider=brave, enriched tools, markdown, read_url available, 5 turns),
    but temperature 0 and a small token budget for lean, deterministic curation."""
    cfg = load_config("frozen")
    cfg["gen"] = {"temperature": 0, "max_tokens": 512}
    return cfg


def probe_item(item, panel=PANEL, anchor_date="2026-07-14", http_mode="replay-or-live"):
    golds = [item["gold_answer"]] + list(item.get("acceptable_answers") or [])
    cfg = _agentic_cfg()
    panel_out = {}
    for m in panel:
        try:
            rec = run_agent(item["question"], m, cfg, anchor_date, http_mode, seed=0)
            if rec.get("error"):
                ans = f"[error: {rec['error']}]"
                matched = False
            else:
                ans = (rec.get("final_answer") or "").strip()
                matched = _matches(ans, golds)
        except Exception as e:  # never kill the batch
            ans, matched, rec = f"[error: {e}]", False, {}
        panel_out[m] = {
            "answer": ans[:600],
            "matches_gold": matched,
            "n_turns": rec.get("n_turns"),
            "n_searches": rec.get("n_searches"),
            "n_reads": rec.get("n_reads"),
        }
    matches = [v["matches_gold"] for v in panel_out.values() if not v["answer"].startswith("[error")]
    unanimous_match = bool(matches) and all(matches)
    unanimous_miss = bool(matches) and not any(matches)
    if unanimous_match:
        verdict = "gold_confirmed"
    elif unanimous_miss:
        verdict = "gold_disputed"
    else:
        verdict = "gold_uncertain"
    return {"verdict": verdict, "mode": "agentic", "panel": panel_out}
