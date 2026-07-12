#!/usr/bin/env python3
"""Render the confirm leaderboard as a self-contained SVG bar chart → analysis/leaderboard.svg.

Regenerable: reads analysis/scores.jsonl (confirm rows only). No dependencies.
Usage: python3 chart.py [--tag confirm] [--out ../analysis/leaderboard.svg]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import REPO_DIR, read_jsonl

BAR = "#3b82f6"        # ranked models
CEIL = "#9ca3af"       # ceiling references
FAIL = "#ef4444"       # capability-gate failures
TEXT = "#6e7781"       # readable on light and dark
INK = "#8b949e"

PRETTY = {
    "huihui-qwen35-2b": "Qwen3.5-2B (huihui abliterated)",
    "qwen35-4b": "Qwen3.5-4B",
    "ministral-3-3b": "Ministral-3-3B",
    "gemma-4-e2b": "Gemma-4-E2B",
    "lfm25-1.2b": "LFM2.5-1.2B",
    "qwen3-06b": "Qwen3-0.6B",
    "qwen3-1.7b": "Qwen3-1.7B",
    "mlabonne-qwen3-4b": "Qwen3-4B (mlabonne)",
    "gemma-3-1b-q4": "Gemma-3-1B",
    "gemma-3-4b": "Gemma-3-4B",
    "phi-4-mini": "Phi-4-mini",
    "smollm3-3b": "SmolLM3-3B",
    "hermes-3-3b": "Hermes-3-3B",
    "ggml-org/Qwen3.6-27B-GGUF:Q8_0": "Qwen3.6-27B (ceiling ref)",
    "ggml-org/gemma-4-31B-it-GGUF:Q8_0": "Gemma-4-31B (ceiling ref)",
    "qwen35-2b": "Qwen3.5-2B",
    "openrouter:anthropic/claude-sonnet-5": "Claude Sonnet 5 (frontier anchor)",
    "openrouter:openai/gpt-5.6-sol": "GPT-5.6-sol (frontier anchor)",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="confirm2")
    ap.add_argument("--out", default=str(REPO_DIR / "analysis" / "leaderboard.svg"))
    args = ap.parse_args()

    rows = [r for r in read_jsonl(REPO_DIR / "analysis" / "scores.jsonl") if f"-{args.tag}-" in r["run_id"]]
    for r in rows:
        r["_ceil"] = "Q8_0" in r["model"] or r["model"].startswith("openrouter:")
        r["_fail"] = (r["engagement_fresh"] or 0) == 0
    rows.sort(key=lambda r: (r["_fail"], r["_ceil"], -(r["correct_fresh"]["rate"] or 0)))

    W, ROW, LEFT, RIGHT, TOP = 760, 26, 235, 60, 64
    H = TOP + ROW * len(rows) + 46
    scale = W - LEFT - RIGHT
    # caption derives from the data — never hardcode the dataset version or n
    ds = rows[0].get("dataset_version") or "?"
    n_fresh = max((r["correct_fresh"]["n"] or 0) for r in rows)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="ui-sans-serif,system-ui,sans-serif">']
    s.append(f'<text x="{LEFT}" y="24" font-size="15" font-weight="600" fill="{TEXT}">Agentic web search — fresh-question correctness (frozen config, dataset {ds})</text>')
    s.append(f'<text x="{LEFT}" y="42" font-size="11" fill="{INK}">{n_fresh} retrieval-required questions · whiskers = Wilson 90% CI · no-tool floor ≈ 0.00–0.02</text>')
    for gx in (0.0, 0.25, 0.5, 0.75, 1.0):
        x = LEFT + gx * scale
        s.append(f'<line x1="{x:.0f}" y1="{TOP-8}" x2="{x:.0f}" y2="{H-38}" stroke="{INK}" stroke-opacity="0.25" stroke-width="1"/>')
        s.append(f'<text x="{x:.0f}" y="{H-22}" font-size="10" fill="{INK}" text-anchor="middle">{gx:.2f}</text>')
    for i, r in enumerate(rows):
        y = TOP + i * ROW
        cf = r["correct_fresh"]
        rate = cf["rate"] or 0.0
        lo, hi = cf["ci90"]
        color = FAIL if r["_fail"] else (CEIL if r["_ceil"] else BAR)
        name = PRETTY.get(r["model"], r["model"])
        s.append(f'<text x="{LEFT-8}" y="{y+13}" font-size="11.5" fill="{TEXT}" text-anchor="end">{name}</text>')
        s.append(f'<rect x="{LEFT}" y="{y+2}" width="{max(rate*scale, 1.5):.1f}" height="15" rx="2.5" fill="{color}" fill-opacity="{0.55 if r["_ceil"] else 0.9}"/>')
        if not r["_fail"]:
            s.append(f'<line x1="{LEFT+lo*scale:.1f}" y1="{y+9.5}" x2="{LEFT+hi*scale:.1f}" y2="{y+9.5}" stroke="{TEXT}" stroke-width="1.4"/>')
            s.append(f'<line x1="{LEFT+lo*scale:.1f}" y1="{y+5}" x2="{LEFT+lo*scale:.1f}" y2="{y+14}" stroke="{TEXT}" stroke-width="1.4"/>')
            s.append(f'<line x1="{LEFT+hi*scale:.1f}" y1="{y+5}" x2="{LEFT+hi*scale:.1f}" y2="{y+14}" stroke="{TEXT}" stroke-width="1.4"/>')
        label = f"{rate:.3f}" if not r["_fail"] else f"{rate:.2f} — never calls tools"
        s.append(f'<text x="{LEFT+max(rate*scale,1.5)+ (48 if not r["_fail"] else 8):.1f}" y="{y+13}" font-size="10.5" fill="{TEXT}">{label}</text>')
    s.append("</svg>")
    Path(args.out).write_text("\n".join(s))
    print(f"wrote {args.out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
