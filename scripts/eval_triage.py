import csv, json, subprocess, time, glob, pathlib, sys
from datetime import datetime

ROOT = pathlib.Path(".")
ISSUES = sorted(glob.glob("datasets/issues/*.md"))
OUTCSV = ROOT / "results/summaries/triage_metrics.csv"
OUTCSV.parent.mkdir(parents=True, exist_ok=True)

rows = []
ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"

def run(cmd):
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True)
    t1 = time.time()
    return p, round(t1 - t0, 3)

def read_json(path):
    try:
        return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}

for issue in ISSUES:
    stem = pathlib.Path(issue).stem

    # --- OpenAI ---
    p, latency = run(["bash","runners/openai/run_triage.sh", issue])
    openai_out = f"results/raw/openai/triage/{stem}.out.json"
    openai_api = f"results/raw/openai/triage/{stem}.api.json"
    o = read_json(openai_out)
    oa = read_json(openai_api)
    usage = oa.get("usage") or {}
    rows.append({
        "timestamp_utc": ts,
        "issue": stem,
        "stack": "openai",
        "latency_s": latency,
        "labels": ",".join(o.get("labels", [])),
        "priority": o.get("priority", ""),
        "rationale_len": len((o.get("rationale","") or "")),
        "tokens_in": usage.get("prompt_tokens",""),
        "tokens_out": usage.get("completion_tokens",""),
        "model": (oa.get("model") or oa.get("usage",{}).get("model") or "gpt-4o-mini"),
        "out_path": openai_out,
    })

    # --- Gemini (SDK) ---
    p, latency = run(["bash","runners/gemini/run_triage_sdk.sh", issue])
    gem_out = f"results/raw/gemini/triage/{stem}.out.json"
    gem_api = f"results/raw/gemini/triage/{stem}.api.json"
    g = read_json(gem_out)
    # token usage is not always available; leave blank if missing
    rows.append({
        "timestamp_utc": ts,
        "issue": stem,
        "stack": "gemini",
        "latency_s": latency,
        "labels": ",".join(g.get("labels", [])),
        "priority": g.get("priority", ""),
        "rationale_len": len((g.get("rationale","") or "")),
        "tokens_in": "",
        "tokens_out": "",
        "model": "gemini-2.5-pro",
        "out_path": gem_out,
    })

# Write CSV
fieldnames = ["timestamp_utc","issue","stack","latency_s","labels","priority","rationale_len","tokens_in","tokens_out","model","out_path"]
with open(OUTCSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in rows:
        w.writerow(r)

print(str(OUTCSV))
