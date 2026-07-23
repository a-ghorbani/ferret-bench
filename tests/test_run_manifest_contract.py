"""Every run directory must carry the keys its downstream consumers require.

Motivated by two live failures on 2026-07-22: a run written without `dataset` made
judge.py:125 raise KeyError (silently producing zero judgments for 9 cells) and
aggregate.py:40 crash at the end of an otherwise successful sweep. Both consumers read
the key positionally with no default, so any new producer of run dirs must supply it.
"""
import json
import unittest
from pathlib import Path

from _harness_path import HARNESS_DIR  # noqa: E402

RUNS_DIR = HARNESS_DIR.parent / "runs"

# Keys read without a default by judge.py / aggregate.py / export_site.py
REQUIRED = ("run_id", "model", "dataset")


def _manifests():
    if not RUNS_DIR.is_dir():
        return []
    return sorted(RUNS_DIR.glob("*/manifest.json"))


class TestManifestContract(unittest.TestCase):
    def test_runs_dir_present(self):
        if not _manifests():
            self.skipTest("no runs/ present (fresh clone) — nothing to validate")

    def test_every_manifest_has_required_keys(self):
        missing = []
        for p in _manifests():
            try:
                m = json.loads(p.read_text())
            except json.JSONDecodeError:
                missing.append((p.parent.name, "UNPARSEABLE"))
                continue
            for k in REQUIRED:
                if k not in m:
                    missing.append((p.parent.name, k))
        self.assertEqual(missing, [],
                         f"{len(missing)} manifest(s) missing keys consumers read without a "
                         f"default; judge.py and aggregate.py will fail on these: {missing[:10]}")

    def test_judged_runs_declare_their_judge(self):
        bad = []
        for p in _manifests():
            if not (p.parent / "judgments.jsonl").is_file():
                continue
            m = json.loads(p.read_text())
            if not m.get("judge"):
                bad.append(p.parent.name)
        self.assertEqual(bad, [], f"runs have judgments but no judge recorded: {bad[:10]}")

    def test_local_runs_identify_their_weights(self):
        """resolve_weights exists so a published number can always name the exact GGUF.
        A run whose weights degraded to UNKNOWN must never be shipped."""
        bad = []
        for p in _manifests():
            m = json.loads(p.read_text())
            w = m.get("weights") or {}
            if w.get("kind") == "local" and w.get("quant") in (None, "UNKNOWN"):
                bad.append(p.parent.name)
        self.assertEqual(bad, [], f"local runs with unidentifiable weights: {bad[:10]}")


if __name__ == "__main__":
    unittest.main()
