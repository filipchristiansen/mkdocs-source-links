.DEFAULT_GOAL := help

.PHONY: install sync lint test ci

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  ----------------- Install -----------------------"
	@echo "  install   Install dependencies"
	@echo "  sync      Sync all dependency groups"
	@echo "  ----------------- CI (local) --------------------"
	@echo "  lint      Run lint (auto-fix where supported)"
	@echo "  test      Run tests"
	@echo "  ci        Pre-PR checks (lint, test, coverage)"

install:
	uv python install 3.10
	$(MAKE) sync
	uv run pre-commit install

sync:
	uv sync --all-groups

lint:
	uv run pre-commit run --all-files

test:
	uv run pytest --cov

ci: sync lint test
