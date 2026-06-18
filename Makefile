.DEFAULT_GOAL := help

.PHONY: install sync lint test docs ci release-prep release-tag

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  ----------------- Install -----------------------"
	@echo "  install        Install dependencies"
	@echo "  sync           Sync all dependency groups"
	@echo "  ----------------- CI (local) --------------------"
	@echo "  lint           Run lint (auto-fix where supported)"
	@echo "  test           Run tests"
	@echo "  docs           Build documentation site (strict)"
	@echo "  ci             Pre-PR checks (lint, test, coverage)"
	@echo "  ----------------- Release -----------------------"
	@echo "  release-prep   Bump, roll changelog, open release PR   (VERSION=X.Y.Z)"
	@echo "  release-tag    Tag merged release + GitHub release     (VERSION=X.Y.Z)"

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

docs:
	uv run mkdocs build --strict

ci: sync lint test docs

release-prep:
	@test -n "$(VERSION)" || { echo "usage: make release-prep VERSION=X.Y.Z"; exit 1; }
	uv run python scripts/release.py prep $(VERSION)

release-tag:
	@test -n "$(VERSION)" || { echo "usage: make release-tag VERSION=X.Y.Z"; exit 1; }
	uv run python scripts/release.py tag $(VERSION)
