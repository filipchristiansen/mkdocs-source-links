.DEFAULT_GOAL := help

.PHONY: install sync lint audit test docs ci release-prep release-tag verify-tag

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  ----------------- Install -----------------------"
	@echo "  install        Install dependencies"
	@echo "  sync           Sync all dependency groups"
	@echo "  ----------------- CI (local) --------------------"
	@echo "  lint           Run lint (auto-fix where supported)"
	@echo "  audit          Scan dependencies for known vulnerabilities"
	@echo "  test           Run tests"
	@echo "  docs           Build documentation site (strict)"
	@echo "  ci             Pre-PR checks (lint, audit, test, coverage, docs)"
	@echo "  ----------------- Release -----------------------"
	@echo "  release-prep   Bump, roll changelog, open release PR   (VERSION=X.Y.Z)"
	@echo "  release-tag    Signed tag + GitHub release after merge  (VERSION=X.Y.Z)"
	@echo "  verify-tag     Preflight: verify signed tag on GitHub   (TAG=vX.Y.Z)"

install:
	uv python install 3.10
	$(MAKE) sync
	uv run pre-commit install

sync:
	uv sync --all-groups

lint:
	uv run pre-commit run --all-files

audit:
	uv sync --all-groups --frozen
	uv run pip-audit -l --desc on

test:
	uv run pytest --cov

docs:
	uv run mkdocs build --strict

ci: sync lint audit test docs

release-prep:
	@test -n "$(VERSION)" || { echo "usage: make release-prep VERSION=X.Y.Z"; exit 1; }
	uv run python scripts/release.py prep $(VERSION)

release-tag:
	@test -n "$(VERSION)" || { echo "usage: make release-tag VERSION=X.Y.Z"; exit 1; }
	uv run python scripts/release.py tag $(VERSION)

verify-tag:
	@test -n "$(TAG)" || { echo "usage: make verify-tag TAG=vX.Y.Z"; exit 1; }
	GITHUB_REPOSITORY=filipchristiansen/mkdocs-source-links TAG=$(TAG) bash .github/scripts/verify-release-tag.sh
