#!/usr/bin/env bash
set -euo pipefail
if [ "${1-}" = "" ]; then
  echo "Usage: runners/gemini/run_triage.sh <issue.md>" >&2
  exit 1
fi
if ! command -v gemini >/dev/null 2>&1; then
  echo "ERROR: gemini CLI not found. Install with: npm i -g @google/gemini-cli" >&2
  exit 2
fi
if [ -z "${GEMINI_API_KEY-}" ]; then
  echo "NOTE: GEMINI_API_KEY not set in env; assuming ~/.gemini/.env is configured." >&2
fi

ISSUE="$1"
OUTDIR="results/raw/gemini/triage"
mkdir -p "$OUTDIR"

stem="$(basename "$ISSUE" .md)"
RAW="$OUTDIR/${stem}.raw.txt"
OUT="$OUTDIR/${stem}.out.json"

# Build a single prompt string for -p (no stdin)
TRIAGE_PROMPT="$(cat prompts/triage.md)"
ISSUE_TEXT="$(cat "$ISSUE")"
FULL_PROMPT=$'### TRIAGE PROMPT\n'"$TRIAGE_PROMPT"$'\n\n---\nISSUE:\n'"$ISSUE_TEXT"$'\n\nReply ONLY with minified JSON. No prose.'

# Call Gemini CLI in non-interactive mode and capture raw output
gemini -m gemini-2.5-pro -p "$FULL_PROMPT" > "$RAW"

# Normalize to JSON (strip ANSI, fenced blocks, then brace-balance)
python - "$RAW" "$OUT" <<'PY'
import json, re, sys, pathlib
raw_path = pathlib.Path(sys.argv[1]); out_path = pathlib.Path(sys.argv[2])
raw = raw_path.read_text(encoding="utf-8")

# Strip ANSI
raw = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', raw)

def write(o):
    out_path.write_text(json.dumps(o, separators=(",",":")), encoding="utf-8")
    print(str(out_path))

# 1) Direct JSON
try:
    write(json.loads(raw.strip())); raise SystemExit
except Exception:
    pass

# 2) ```json ... ```
m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, flags=re.S|re.I)
if m:
    try:
        write(json.loads(m.group(1))); raise SystemExit
    except Exception:
        pass

# 3) Brace-balance extractor (ignores braces inside strings)
def extract_first_object(s: str):
    in_str = False; esc = False; depth = 0; start = -1
    for i,ch in enumerate(s):
        if esc: esc=False; continue
        if ch == '\\\\': esc=True; continue
        if ch == '"': in_str = not in_str; continue
        if not in_str:
            if ch == '{':
                if depth == 0: start = i
                depth += 1
            elif ch == '}' and depth>0:
                depth -= 1
                if depth==0 and start!=-1:
                    return s[start:i+1]
    return None

chunk = extract_first_object(raw)
if chunk:
    try:
        write(json.loads(chunk)); raise SystemExit
    except Exception:
        pass

# 4) Fallback
write({"labels":[],"priority":3,"rationale":"Failed to parse JSON from Gemini output","raw":raw[:2000]})
PY
