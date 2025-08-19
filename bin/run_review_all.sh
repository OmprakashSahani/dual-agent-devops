#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# Activate venv
. .venv/bin/activate

# Load Gemini key if available
set -a; [ -f "${HOME}/.gemini/.env" ] && . "${HOME}/.gemini/.env" || true; set +a

# Ensure OpenAI key present
: "${OPENAI_API_KEY:?Need OPENAI_API_KEY in this shell (export OPENAI_API_KEY=...)}"

python scripts/eval_review.py
python scripts/compare_review.py

echo
echo "Outputs:"
echo "  results/summaries/review_metrics.csv"
echo "  results/summaries/review_compare.md"
