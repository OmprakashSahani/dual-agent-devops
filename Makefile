SHELL := /bin/bash
.ONESHELL:
.DEFAULT_GOAL := help

help: ## Show this help
@grep -E '^[a-zA-Z0-9_\-]+:.*## ' Makefile | sed -e 's/:.*##/: /' | sort

setup: ## Create venv and install deps
python3 -m venv .venv
. .venv/bin/activate; pip install -U pip openai google-genai pydantic

triage: ## Run triage benchmark and refresh README tables
: "${OPENAI_API_KEY:?Set OPENAI_API_KEY in env}"
. .venv/bin/activate; bin/run_triage_all.sh
. .venv/bin/activate; python scripts/update_readme.py

review: ## Run review benchmark and refresh README tables
: "${OPENAI_API_KEY:?Set OPENAI_API_KEY in env}"
. .venv/bin/activate; bin/run_review_all.sh
. .venv/bin/activate; python scripts/update_readme.py

all: ## Run triage + review + README refresh
make triage
make review

clean: ## Remove venv and results
rm -rf .venv results
