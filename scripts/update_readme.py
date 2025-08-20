import os, re, subprocess, pathlib

root = pathlib.Path(".")
tmpl_path = root / "README.tmpl"
readme_path = root / "README.md"

# Derive repo slug from git remote
try:
    remote = subprocess.check_output(["git","remote","get-url","origin"], text=True).strip()
    # supports https and ssh forms
    m = re.search(r'github\.com[:/](.+?)(?:\.git)?$', remote)
    repo_slug = m.group(1) if m else "OmprakashSahani/dual-agent-devops"
except Exception:
    repo_slug = "OmprakashSahani/dual-agent-devops"

workflow = "triage-compare.yml"
badge_md = f"[![CI](https://github.com/{repo_slug}/actions/workflows/{workflow}/badge.svg?branch=main)](https://github.com/{repo_slug}/actions/workflows/{workflow})"

triage_table = (root/"results/summaries/triage_compare.md").read_text(encoding="utf-8") if (root/"results/summaries/triage_compare.md").exists() else "| (no triage results yet) |"
review_table = (root/"results/summaries/review_compare.md").read_text(encoding="utf-8") if (root/"results/summaries/review_compare.md").exists() else "| (no review results yet) |"

if tmpl_path.exists():
    s = tmpl_path.read_text(encoding="utf-8")
else:
    s = readme_path.read_text(encoding="utf-8") if readme_path.exists() else "# Dual-Agent DevOps: Gemini vs OpenAI\n\n%BADGE%\n\n## Results (latest run)\n\n### Triage (OpenAI vs Gemini)\n%TRIAGE_TABLE%\n\n### Review (OpenAI vs Gemini)\n%REVIEW_TABLE%\n"

def inject(content: str) -> str:
    out = content.replace("%BADGE%", badge_md)
    out = out.replace("%TRIAGE_TABLE%", triage_table)
    out = out.replace("%REVIEW_TABLE%", review_table)

    # If placeholders missing (older README), append a Results section
    if "%TRIAGE_TABLE%" not in content and "## Results (latest run)" not in out:
        out += "\n\n## Results (latest run)\n\n### Triage (OpenAI vs Gemini)\n" + triage_table + "\n\n### Review (OpenAI vs Gemini)\n" + review_table + "\n"
    return out

readme_path.write_text(inject(s), encoding="utf-8")
print("README updated with latest tables and badge for", repo_slug)
