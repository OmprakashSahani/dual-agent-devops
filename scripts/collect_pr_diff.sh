#!/usr/bin/env bash
set -euo pipefail
if [ "${1-}" = "" ]; then
  echo "Usage: scripts/collect_pr_diff.sh <PR_NUMBER>" >&2
  exit 1
fi
PR="$1"
mkdir -p datasets/prs
gh pr diff "$PR" > "datasets/prs/${PR}.diff"
echo "Saved datasets/prs/${PR}.diff"
