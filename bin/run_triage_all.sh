#!/usr/bin/env bash
set -euo pipefail

# Always run from repo root
cd "$(git rev-parse --show-toplevel)"

# Activate venv
if [ -f ".venv/bin/activate" ]; then
  . .venv/bin/activate
else
  echo "ERROR: .venv not found. Create it with: python3 -m venv .venv && . .venv/bin/activate && pip install -U pip openai google-genai pydantic" >&2
  exit 2
fi

# Load Gemini key if present
set -a; [ -f "${HOME}/.gemini/.env" ] && . "${HOME}/.gemini/.env" || true; set +a

# Ensure OpenAI key is present
: "${OPENAI_API_KEY:?Need OPENAI_API_KEY in this shell (export OPENAI_API_KEY=...)}"

# Re-run evaluation over all issues and produce summaries
python scripts/eval_triage.py
python scripts/compare_triage.py

echo
echo "Outputs:"
echo "  results/summaries/triage_metrics.csv"
echo "  results/summaries/triage_compare.md"
