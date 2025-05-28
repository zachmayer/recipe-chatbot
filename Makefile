.PHONY: help format lint

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

format: ## Run ruff formatter and apply fixable lint rules
	uv run ruff format .
	uv run ruff check --fix-only --unsafe-fixes .

lint: ## Check code formatting and lint rules
	uv run ruff format --check .
	uv run ruff check .

bulk-test: ## Run bulk tests
	uv run scripts/bulk_test.py
