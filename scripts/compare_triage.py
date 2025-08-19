import csv, json, pathlib, sys
from typing import List, Dict

CSV_PATH = pathlib.Path("results/summaries/triage_metrics.csv")
OUT_JSON = pathlib.Path("results/summaries/triage_compare.json")
OUT_MD   = pathlib.Path("results/summaries/triage_compare.md")

def parse_labels(s: str) -> List[str]:
    # safe split for our CSV since labels were written as a single string with commas
    # examples: "bug,validation,api" or empty ""
    s = (s or "").strip()
    if not s:
        return []
    # remove stray quotes if any shell pretty-printer added them
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    return [x.strip() for x in s.split(",") if x.strip()]

def jaccard(a: List[str], b: List[str]) -> float:
    A, B = set(a), set(b)
    if not A and not B:
        return 1.0
    return len(A & B) / max(1, len(A | B))

# Load rows
rows: List[Dict[str,str]] = []
with open(CSV_PATH, newline="", encoding="utf-8") as f:
    r = csv.DictReader(f)
    rows = list(r)

# Group by issue
by_issue: Dict[str, Dict[str, Dict[str,str]]] = {}
for row in rows:
    by_issue.setdefault(row["issue"], {})[row["stack"]] = row

report = []
for issue, stacks in sorted(by_issue.items()):
    o = stacks.get("openai", {})
    g = stacks.get("gemini", {})

    labels_o = parse_labels(o.get("labels",""))
    labels_g = parse_labels(g.get("labels",""))

    jac = jaccard(labels_o, labels_g)
    prio_o = int(o.get("priority") or 0)
    prio_g = int(g.get("priority") or 0)
    pdelta = abs(prio_o - prio_g) if prio_o and prio_g else ""

    lo = float(o.get("latency_s") or 0)
    lg = float(g.get("latency_s") or 0)
    if lo and lg:
        faster = "gemini" if lg < lo else ("openai" if lo < lg else "tie")
        speedup = round((max(lo, lg) / max(1e-9, min(lo, lg))), 2) if min(lo, lg) > 0 else ""
    else:
        faster, speedup = "", ""

    entry = {
        "issue": issue,
        "labels_openai": labels_o,
        "labels_gemini": labels_g,
        "labels_jaccard": round(jac, 3),
        "priority_openai": prio_o,
        "priority_gemini": prio_g,
        "priority_delta": pdelta,
        "latency_openai_s": lo,
        "latency_gemini_s": lg,
        "faster": faster,
        "speedup_x": speedup,
    }
    report.append(entry)

# Write JSON + Markdown
OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

lines = []
lines.append("| issue | labels_openai | labels_gemini | jaccard | prio(O) | prio(G) | Δprio | faster | speedup |")
lines.append("|---|---|---|---:|---:|---:|---:|---|---:|")
for r in report:
    lines.append(
        f"| {r['issue']} | `{', '.join(r['labels_openai'])}` | `{', '.join(r['labels_gemini'])}` | "
        f"{r['labels_jaccard']:.3f} | {r['priority_openai']} | {r['priority_gemini']} | {r['priority_delta']} | "
        f"{r['faster']} | {r['speedup_x']} |"
    )
OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

# Print a compact table to stdout
print("\n".join(lines))
