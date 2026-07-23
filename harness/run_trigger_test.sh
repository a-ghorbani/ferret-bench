#!/usr/bin/env bash
# Trigger-clause test — see PREREG-2026-07-21-trigger-clause.md
#
# Arms vary ONLY the tail of web_search's description (tool_desc); system_prompt stays
# `shipped` (PR #808 verbatim) in every cell. Replicates vary cfg.gen.seed — NOT the
# harness --seed flag, which drives nonces only and leaves llama.cpp sampling deterministic.
#
# Config order below is arms-within-seed on purpose: one model load, and any drift during
# the run is spread across arms instead of aligning with one.
set -euo pipefail
cd "$(dirname "$0")"

DATASET=../study-1/datasets/dev/questions.jsonl
QIDS=../study-1/datasets/dev/qids-trigger-test.txt
ARMS=(trig-a-s42 trig-b1-s42 trig-b2-s42
      trig-a-s43 trig-b1-s43 trig-b2-s43
      trig-a-s44 trig-b1-s44 trig-b2-s44)

STAGE="${1:-1}"

case "$STAGE" in
  1)  # decisive model only — if bonsai does not move, the hypothesis is dead and stage 2 is moot
      MODELS=(bonsai-27b-q1); TAG=trig1 ;;
  2)  # regression guards — run ONLY if stage 1 is positive
      MODELS=(qwen35-4b qwen35-2b lfm2-2.6b); TAG=trig2 ;;
  *)  echo "usage: $0 [1|2]" >&2; exit 1 ;;
esac

echo "stage=$STAGE models=${MODELS[*]} cells=$(( ${#MODELS[@]} * ${#ARMS[@]} ))"
python3 sweep.py \
  --configs "${ARMS[@]}" \
  --models "${MODELS[@]}" \
  --dataset "$DATASET" \
  --qids-file "$QIDS" \
  --tag "$TAG" \
  --http-mode replay-or-live \
  --skip-existing
