import re, csv, time, glob, pathlib, subprocess
from datetime import datetime, timezone

ROOT = pathlib.Path(".")
DIFFS = sorted(glob.glob("datasets/prs/*.diff"))
OUTCSV = ROOT / "results/summaries/review_metrics.csv"
OUTCSV.parent.mkdir(parents=True, exist_ok=True)

SECTIONS = ["Summary","Major Issues","Minor Issues","Tests Suggested","Security","Performance"]

def run(cmd):
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True)
    t1 = time.time()
    return p, round(t1 - t0, 3)

def read_text(p: pathlib.Path) -> str:
    try: return p.read_text(encoding="utf-8", errors="replace")
    except: return ""

def section_span(md: str, name: str):
    # Match headings like # Name or ## Name (case-insensitive)
    pat = re.compile(rf"^#{{1,6}}\s+{re.escape(name)}\s*$", re.I | re.M)
    m = pat.search(md)
    if not m: return None
    start = m.end()
    # find next heading
    m2 = re.search(r"^#{1,6}\s+.+$", md[start:], re.M)
    end = start + m2.start() if m2 else len(md)
    return (start, end)

def count_bullets(block: str) -> int:
    n = 0
    for line in block.splitlines():
        s = line.strip()
        if s.startswith("-") or s.startswith("*") or re.match(r"^\d+\.", s):
            n += 1
    return n

ts = datetime.now(timezone.utc).isoformat(timespec="seconds")

rows = []
for diff_path in DIFFS:
    stem = pathlib.Path(diff_path).stem

    # --- OpenAI ---
    p, latency = run(["bash","runners/openai/run_review.sh", diff_path])
    openai_out = pathlib.Path(f"results/raw/openai/review/{stem}.md")
    otext = read_text(openai_out)
    o_lines = otext.count("\n")+1 if otext else 0
    o_chars = len(otext)
    o_present = sum(section_span(otext, s) is not None for s in SECTIONS)
    o_major_span = section_span(otext, "Major Issues")
    o_major_cnt = count_bullets(otext[o_major_span[0]:o_major_span[1]]) if o_major_span else 0
    o_tests_span = section_span(otext, "Tests Suggested")
    o_tests_cnt = count_bullets(otext[o_tests_span[0]:o_tests_span[1]]) if o_tests_span else 0

    rows.append({
        "timestamp_utc": ts, "diff": stem, "stack": "openai",
        "latency_s": latency, "lines": o_lines, "chars": o_chars,
        "rubric_sections_present": o_present,
        "major_issues_count": o_major_cnt, "tests_suggested_count": o_tests_cnt,
        "model": "gpt-4o-mini", "out_path": str(openai_out)
    })

    # --- Gemini ---
    p, latency = run(["bash","runners/gemini/run_review_sdk.sh", diff_path])
    gem_out = pathlib.Path(f"results/raw/gemini/review/{stem}.md")
    gtext = read_text(gem_out)
    g_lines = gtext.count("\n")+1 if gtext else 0
    g_chars = len(gtext)
    g_present = sum(section_span(gtext, s) is not None for s in SECTIONS)
    g_major_span = section_span(gtext, "Major Issues")
    g_major_cnt = count_bullets(gtext[g_major_span[0]:g_major_span[1]]) if g_major_span else 0
    g_tests_span = section_span(gtext, "Tests Suggested")
    g_tests_cnt = count_bullets(gtext[g_tests_span[0]:g_tests_span[1]]) if g_tests_span else 0

    rows.append({
        "timestamp_utc": ts, "diff": stem, "stack": "gemini",
        "latency_s": latency, "lines": g_lines, "chars": g_chars,
        "rubric_sections_present": g_present,
        "major_issues_count": g_major_cnt, "tests_suggested_count": g_tests_cnt,
        "model": "gemini-2.5-pro", "out_path": str(gem_out)
    })

with open(OUTCSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=[
        "timestamp_utc","diff","stack","latency_s","lines","chars",
        "rubric_sections_present","major_issues_count","tests_suggested_count",
        "model","out_path"
    ])
    w.writeheader()
    w.writerows(rows)

print(str(OUTCSV))
