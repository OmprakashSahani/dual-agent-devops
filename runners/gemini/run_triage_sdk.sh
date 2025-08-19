#!/usr/bin/env bash
set -euo pipefail
if [ "${1-}" = "" ]; then
  echo "Usage: runners/gemini/run_triage_sdk.sh <issue.md>" >&2
  exit 1
fi
OUTDIR="results/raw/gemini/triage"
mkdir -p "$OUTDIR"
stem="$(basename "$1" .md)"
python scripts/gemini_triage.py "$1" "$OUTDIR/${stem}.out.json" "$OUTDIR/${stem}.api.json"
echo "$OUTDIR/${stem}.out.json"
