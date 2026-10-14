# Cadence: one-word entry points for setup, checks, demo and the full pipeline.
# Run `make` (or `make help`) to list targets.

SHELL := /bin/bash
export PYTHONHASHSEED := 0

DEMO_WAV  := data/demo/demo_T3_flawed.wav
DEMO_OUT  := results/demo_report.json
IMAGE     := cadence

.DEFAULT_GOAL := help
.PHONY: help setup test lint verify demo app web reproduce docker docker-run clean

help: ## List available targets
	@echo "Cadence make targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

setup: ## Install pinned deps from uv.lock (incl. dev extra)
	uv sync --frozen --extra dev

test: ## Run the unit test suite
	uv run pytest -q

lint: ## Lint cadence/, scripts/ and tests/ with ruff
	uv run --with ruff ruff check cadence scripts tests

verify: test ## Tests + byte-identical rerun check on the demo clips
	uv run python scripts/rerun_check.py

demo: ## Analyze the bundled flawed T3 demo clip -> results/demo_report.json
	@test -f $(DEMO_WAV) || { echo "missing $(DEMO_WAV)"; exit 1; }
	@mkdir -p results
	uv run cadence analyze $(DEMO_WAV) --text T3 --out $(DEMO_OUT)
	@echo "Report written to $(DEMO_OUT)"

app: ## Gradio dashboard on :7860
	uv run cadence app

web: ## Coach web app on http://localhost:8000
	uv run cadence web

reproduce: ## Full pipeline (fetch -> refs -> ladders -> evaluate) in the background
	@mkdir -p logs
	nohup uv run cadence all > logs/reproduce.log 2>&1 &
	@echo "Pipeline started in the background (single process). Follow it with: tail -f logs/reproduce.log"

docker: ## Build the Docker image
	docker build -t $(IMAGE) .

docker-run: ## Run the Docker image on :7860
	docker run --rm -p 7860:7860 $(IMAGE)

clean: ## Remove Python caches (never touches data/ or results/)
	find . -path ./.venv -prune -o -type d -name __pycache__ -print -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache
