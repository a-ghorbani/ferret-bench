#!/usr/bin/env bash
# Does read_url degrade evidence quality? ministral-3-3b is the only roster model that
# meaningfully uses it (0.31 reads/q vs 0.03-0.05), and its retrieved evidence scored worst
# in the swap matrix (row 0.833 vs 0.908/0.896).
#
# Both arms run TODAY so the contrast is not confounded with web drift — the July-17 source
# run is 5 days stale and must not be used as the control.
#
# Caveat: disabling read_url also removes "and open pages with read_url" from the system
# prompt (configs.py build_system_prompt). Tool availability and prompt text move together;
# they cannot be separated without an unnatural config.
set -euo pipefail
cd "$(dirname "$0")"
DATASET=../study-1/datasets/dev/questions.jsonl
QIDS=../study-1/datasets/dev/qids-trigger-test.txt

echo "=== 1/2 end-to-end: control (read_url available) vs treatment (disabled) ==="
python3 sweep.py --configs rep-s42 frozen-readoff --models ministral-3-3b \
  --dataset "$DATASET" --qids-file "$QIDS" --tag readoff --http-mode replay-or-live

CTRL=$(ls -d ../runs/*readoff-rep-s42-ministral* | tail -1)
TREAT=$(ls -d ../runs/*readoff-frozen-readoff-ministral* | tail -1)
echo "control=$CTRL"; echo "treatment=$TREAT"

echo "=== 2/2 swap: both as evidence SOURCES, read by all three models ==="
python3 -u swap_eval.py --sources "$CTRL" "$TREAT" \
  --targets qwen35-4b gemma-4-e2b ministral-3-3b \
  --per-fact 1 --tag swapro
