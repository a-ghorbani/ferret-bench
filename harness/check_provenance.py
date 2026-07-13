#!/usr/bin/env python3
"""Enforce amendment #16: every frozen value must be DERIVED, not inherited.

A frozen value is only owned if, under the CURRENT regime (current config hash's dataset and
conditions), we ran at least one arm that varied it and lost. "We kept PocketPal's default" is
not a result; "we tested the alternatives under these conditions and the default won" is.

This is a hard gate, not a lint. It exists because "retained shipped default" appeared 8 times
in PROVENANCE.md and every instance was an abdication wearing the costume of a decision — and
because the identical failure ("quantization held constant") survived for days as prose while
being false in fact. Prose rots; checks do not.

Usage: python3 check_provenance.py [--tag revalidate --tag prompt3 ...]
Exit 1 if any frozen value has no counterfactual arm in the current regime.
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import REPO_DIR, read_jsonl
from configs import load_config

# Every factor that is FROZEN in the shipped deliverable must appear here with the arms that
# would refute it. If you add a factor to the config, you must add its counterfactual here.
COUNTERFACTUALS = {
    "tool_desc":         "an arm with a different tool_desc",
    "provider":          "an arm with a different provider",
    "result_format":     "an arm with a different result_format",
    "result_count":      "an arm with a different result_count",
    "snippet_chars":     "an arm with a different snippet_chars",
    "read_url_policy":   "an arm with a different read_url_policy",
    "max_turns":         "an arm with a different max_turns",
    "system_prompt":     "an arm with a different system_prompt",
    "enable_thinking":   "an arm with a different enable_thinking",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", nargs="+", default=["revalidate", "prompt3", "thinkon", "confirm3"],
                    help="sweep tags that constitute the CURRENT regime's evidence")
    args = ap.parse_args()

    frozen = load_config("frozen")
    rows = [r for r in read_jsonl(REPO_DIR / "analysis" / "scores.jsonl")
            if any(f"-{t}-" in r["run_id"] for t in args.tags)]

    # what value did each run actually use for each factor?
    import json
    seen = defaultdict(set)
    for r in rows:
        man = json.loads((REPO_DIR / "runs" / r["run_id"] / "manifest.json").read_text())
        for k in COUNTERFACTUALS:
            if k in man["config"]:
                seen[k].add(json.dumps(man["config"][k]))

    print(f"Frozen config: {frozen['config_hash'][:12]}…")
    print(f"Evidence tags: {args.tags}\n")
    unowned = []
    for k, need in COUNTERFACTUALS.items():
        frozen_val = json.dumps(frozen.get(k))
        alternatives = seen[k] - {frozen_val}
        if alternatives:
            alts = ", ".join(sorted(json.loads(a).__str__() for a in alternatives))
            print(f"  TESTED    {k:<18} = {json.loads(frozen_val)!r:<14} (vs: {alts})")
        else:
            print(f"  INHERITED {k:<18} = {json.loads(frozen_val)!r:<14} — NO counterfactual run. "
                  f"We do not own this value; we copied it.")
            unowned.append(k)

    if unowned:
        print(f"\nFAIL: {len(unowned)} frozen value(s) inherited rather than derived: {unowned}")
        print("Amendment #16: a value we did not test is a value we do not own. Run the arm, or")
        print("remove the value from frozen-config/ and say plainly that it is PocketPal's choice.")
        return 1
    print("\nPASS: every frozen value was tested against an alternative under the current regime.")
    print("(This gate proves the arm was RUN. Whether the frozen value WON is a judgment made in")
    print(" PROVENANCE.md with the numbers — the gate cannot make that call for you.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
