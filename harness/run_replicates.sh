#!/usr/bin/env bash
# k=5 replicate sweep — put an error bar on study-1's top-5 ranking.
#
# Config is `frozen` throughout; ONLY cfg.gen.seed varies (42..46). Note the harness
# --seed flag drives wrapper nonces, not sampling: rep-s42 is byte-identical to `frozen`
# (hash bbb5cdbf...), so seed must live in the config or the replicates are fake.
#
# bonsai-27b-q1 seeds 42/43/44 already exist as runs/*trig1-trig-a-s4?-bonsai* — those
# configs hash-match rep-s42/43/44, so only s45/s46 are run here. Pool by config_hash,
# not by run tag, when analysing.
#
# http-mode is replay-or-live, NOT replay-only: each seed generates fresh queries, and
# replay-only raises CacheMiss on any query not already recorded (http_cache.py:66),
# which would fail most items. This sweep therefore does NOT fix the evidence-freezing
# confound (review issue #1) — it measures run-to-run variance, which is a within-model
# quantity and unaffected by it. Cross-model cache asymmetry persists; report the
# per-cell from_cache rate alongside any ranking claim.
set -euo pipefail
cd "$(dirname "$0")"

DATASET=../study-1/datasets/dev/questions.jsonl
QIDS=../study-1/datasets/dev/qids-trigger-test.txt
TAG=rep5

echo "=== 4 models x 5 seeds ==="
python3 sweep.py \
  --configs rep-s42 rep-s43 rep-s44 rep-s45 rep-s46 \
  --models qwen35-4b ministral-3-3b gemma-4-e2b qwen35-2b \
  --dataset "$DATASET" --qids-file "$QIDS" --tag "$TAG" \
  --http-mode replay-or-live --skip-existing

echo "=== bonsai: only the 2 seeds not already run under tag trig1 ==="
python3 sweep.py \
  --configs rep-s45 rep-s46 \
  --models bonsai-27b-q1 \
  --dataset "$DATASET" --qids-file "$QIDS" --tag "$TAG" \
  --http-mode replay-or-live --skip-existing
