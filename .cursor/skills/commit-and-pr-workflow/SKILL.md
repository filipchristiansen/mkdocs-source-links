---
name: commit-and-pr-workflow
description: >-
  Commit staged changes, open PRs to main, and release to PyPI (version bump + v* tag).
  Use when the user asks to commit and PR, ship it, commit and open PR, release, publish,
  ship a version, tag a release, bump version, or similar git/gh workflows in this repo.
---

# Commit and PR workflows

## Commit and open PR

When the user asks to **commit staged changes and create a PR** (or uses a short phrase like *"commit and PR"*, *"ship it"*, *"commit and open PR"*, *"do the usual commit and PR"*, or similar), do the following without asking for confirmation unless something is ambiguous:

1. **Branch**: Create a new branch from current state with a **suitable name** (e.g. `feat/github-line-anchors`, `fix/relative-path-rewriting`, `test/rewrite-edge-cases`, `refactor/plugin-config`, `chore/ci-matrix`). Use conventional prefixes when they fit: `docs/`, `fix/`, `feat/`, `chore/`, `refactor/`, `test/`, `enhance/`, etc.
2. **Commit**: Commit the **staged** changes with a **suitable commit message** (conventional style when appropriate: lowercase type + short summary, e.g. `fix: ...`, `feat: ...`, optional body with bullet points).
3. **Push**: Push the new branch to `origin` and set upstream.
4. **PR**: Create a pull request targeting **main** with a **suitable title** (lowercase, conventional prefix: e.g. `fix: ...`, `feat: ...`, `chore: ...`, `refactor: ...`, `test: ...`, `enhance: ...`) and **description** (summary of changes, what was added/fixed, and why if relevant). Use `gh pr create` when available.
5. **Label**: Add the label that matches the PR title prefix: **fix**, **feat**, **chore**, **docs**, **refactor**, **test**, **enhance** (and **release** for release PRs only). E.g. title `fix: ...` → `--label "fix"`. Use `gh pr create ... --label "<label>"` or `gh pr edit <number> --add-label "<label>"` after creating.

Infer branch name, commit message, and PR title/description from the staged changes and recent conversation. Do not include untracked or unstaged files unless the user explicitly asks.

Before pushing, run `uv run ruff check .` and `uv run pytest -q` when the changes touch Python code or tests.

---

## Release to PyPI

When the user asks to **release**, **publish**, **ship a version**, *"tag a release"*, *"bump version"*, or similar, do the following:

This repo publishes to PyPI when a **`v*`** tag is pushed (see `.github/workflows/publish.yml`). There is no `prod` branch.

1. **Fetch**: Ensure branches and tags are up to date (`git fetch origin main --tags`).
2. **Version**: Bump `version` in `pyproject.toml` (semver). Use the version the user requested, or infer the next patch/minor/major from context.
3. **Changelog**: List commits since the last release tag (e.g. `git log $(git describe --tags --abbrev=0 2>/dev/null)..HEAD --pretty=format:"- %s (%h)"` or `git log v0.1.0..HEAD` if the last tag is known). Use this as **release notes**.
4. **Commit**: Commit the version bump on **main** (or merge the release prep PR first). Message e.g. `chore: release v0.2.0`.
5. **Tag**: Create an annotated tag matching the version: `v0.2.0` (must match `v*` for the publish workflow).
6. **Push**: Push `main` and the tag: `git push origin main && git push origin v0.2.0`. The tag push triggers the Publish workflow.
7. **GitHub release** (optional but preferred): Create a GitHub release for the tag with the changelog from step 3 (`gh release create v0.2.0 --notes "..."`).

If release prep is not yet on `main`, open a PR to **main** instead of pushing directly — title e.g. `release: v0.2.0`, label **release**, description with the changelog. Merge after CI passes, then tag and push from `main`.

Use `gh` when available. If the user only wants a version bump without publishing yet, stop after step 4 and do not create or push a tag.
