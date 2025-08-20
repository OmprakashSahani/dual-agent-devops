# Dual-Agent DevOps: Gemini vs OpenAI
[![CI](https://github.com/OmprakashSahani/dual-agent-devops/actions/workflows/triage-compare.yml/badge.svg?branch=main)](https://github.com/OmprakashSahani/dual-agent-devops/actions/workflows/triage-compare.yml)

A reproducible benchmark comparing **Google Gemini (SDK)** and **OpenAI (CLI/SDK)** on developer tasks:

- **Issue triage** → labels, priority, rationale  
- **PR review** → rubric sections, issues raised, tests suggested

This repo favors **scriptable, deterministic runs** (JSON/CSV/MD outputs) and clean CI artifacts for forensic comparisons.

---

## Why this matters (SWE interview + research)
- **Systems engineering**: Agent vs API orchestration, reproducibility, CI ergonomics
- **Evaluation**: task-specific metrics (label overlap, rubric coverage, latency)
- **Practicality**: GitHub-ready runners, secrets hygiene, artifacted results

---

## Setup (local)
**Prereqs**
- Python 3.12+, `python3-venv`
- Node not required for benchmarks (Gemini CLI proved less scriptable; we use SDK)
- Accounts/keys:
  - `OPENAI_API_KEY`
  - `GEMINI_API_KEY` (Google AI Studio)

**Create venv + install**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip openai google-genai pydantic
