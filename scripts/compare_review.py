import csv, pathlib

CSV = pathlib.Path("results/summaries/review_metrics.csv")
OUT = pathlib.Path("results/summaries/review_compare.md")

rows = list(csv.DictReader(open(CSV, newline="", encoding="utf-8")))
by_diff = {}
for r in rows:
    by_diff.setdefault(r["diff"], {}).setdefault(r["stack"], r)

lines = []
lines.append("| diff | faster | speedup | rubric(O) | rubric(G) | Δrubric | major(O) | major(G) | tests(O) | tests(G) |")
lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")

for d, stacks in sorted(by_diff.items()):
    o = stacks.get("openai", {})
    g = stacks.get("gemini", {})
    lo = float(o.get("latency_s") or 0)
    lg = float(g.get("latency_s") or 0)
    faster = "gemini" if lg and lo and lg < lo else ("openai" if lo and lg and lo < lg else "tie")
    speed = round((max(lo, lg) / min(lo, lg)), 2) if lo and lg and min(lo,lg) > 0 else ""
    ro = int(o.get("rubric_sections_present") or 0)
    rg = int(g.get("rubric_sections_present") or 0)
    dr = ro - rg
    mo = int(o.get("major_issues_count") or 0); mg = int(g.get("major_issues_count") or 0)
    to = int(o.get("tests_suggested_count") or 0); tg = int(g.get("tests_suggested_count") or 0)
    lines.append(f"| {d} | {faster} | {speed} | {ro} | {rg} | {dr} | {mo} | {mg} | {to} | {tg} |")

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
