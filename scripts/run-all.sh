#!/usr/bin/env bash
# One full pass: clean up, seed 49/50/51/249/250/251 in turn, read the probe after each step.
# Usage: STORE_PASSWORD=... run-all.sh <store>.myshopify.com <theme-id> <app-folder> <label>
# Writes results/merchant-<label>.txt and results/app-<label>.txt
set -euo pipefail
STORE="$1"; THEME="$2"; APP="$3"; LABEL="$4"
cd "$(dirname "$0")/.."
python3 scripts/cleanup.py "$STORE" repro_item || true
APP_PATH="$APP" python3 scripts/cleanup.py "$STORE" '$app:repro_entry' || true
rm -f "results/merchant-$LABEL.txt" "results/app-$LABEL.txt"
python3 scripts/run_steps.py "$STORE" "$THEME" repro_item "results/merchant-$LABEL.txt" &
APP_PATH="$APP" PROBE_PATH=/cart python3 scripts/run_steps.py "$STORE" "$THEME" '$app:repro_entry' "results/app-$LABEL.txt" &
wait
