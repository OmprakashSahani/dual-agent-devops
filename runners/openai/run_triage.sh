#!/usr/bin/env bash
set -euo pipefail
if [ "${1-}" = "" ]; then
  echo "Usage: runners/openai/run_triage.sh <issue.md>" >&2
  exit 1
fi
if [ -z "${OPENAI_API_KEY-}" ]; then
  echo "ERROR: OPENAI_API_KEY is not set in this shell." >&2
  exit 2
fi
ISSUE="$1"
OUTDIR="results/raw/openai/triage"
mkdir -p "$OUTDIR"

python - "$ISSUE" "$OUTDIR" <<'PY'
import os, sys, json, pathlib
from openai import OpenAI

issue_path = pathlib.Path(sys.argv[1])
outdir = pathlib.Path(sys.argv[2])

prompt = open("prompts/triage.md","r",encoding="utf-8").read()
issue = open(issue_path,"r",encoding="utf-8").read()

client = OpenAI()
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    temperature=0.2,
    messages=[
        {"role":"system","content":"You are a precise software issue triage assistant. Reply ONLY with minified JSON."},
        {"role":"user","content": f"{prompt}\n\n---\nISSUE:\n{issue}"}
    ],
    response_format={"type":"json_object"},
)

assistant = resp.choices[0].message.content.strip()

out_json_path = outdir / (issue_path.stem + ".out.json")
with open(out_json_path, "w", encoding="utf-8") as f:
    f.write(assistant)

full_resp_path = outdir / (issue_path.stem + ".api.json")
with open(full_resp_path, "w", encoding="utf-8") as f:
    f.write(resp.model_dump_json(indent=2))

print(str(out_json_path))
PY
