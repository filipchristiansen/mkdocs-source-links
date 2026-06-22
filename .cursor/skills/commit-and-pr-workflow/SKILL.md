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

0. **Pre-flight (never skip)**: Run `git status` and `git branch --show-current` first. **Never commit on `main`** — there are no exceptions, including follow-ups or "add to the same PR" requests. If you are on `main` (e.g. because the PR you meant to amend has already merged, or a checkout switched branches), create a new branch before committing. Also confirm the target PR is still open (`gh pr view <n> --json state`) before assuming you can push more commits to it; if it has merged, branch off `main` and open a new PR.
1. **Branch**: Create a new branch from current state with a **suitable name** (e.g. `feat/github-line-anchors`, `fix/relative-path-rewriting`, `test/rewrite-edge-cases`, `refactor/plugin-config`, `chore/ci-matrix`). Use conventional prefixes when they fit: `docs/`, `fix/`, `feat/`, `chore/`, `refactor/`, `test/`, `enhance/`, etc.
2. **Changelog**: Consider whether `CHANGELOG.md` `[Unreleased]` needs an entry **before** committing, so it can ship in the same commit when warranted:
   - **Add** for user-facing plugin changes (`feat`, `fix`) and breaking changes.
   - **Usually add** for notable README or PyPI-facing documentation updates.
   - **Skip** for routine internal docs, refactors, tests-only, and contributor-only tooling — unless the user asks otherwise.
   - If unclear, mention the decision briefly in the PR description (e.g. "no changelog — docs-only").
   - Do not auto-generate prose; entries are hand-written (see [Release to PyPI](#release-to-pypi) below).
3. **Commit**: Commit the **staged** changes with a **suitable commit message** (conventional style when appropriate: lowercase type + short summary, e.g. `fix: ...`, `feat: ...`, optional body with bullet points). **Always commit with both `-s` and `-S`** (`git commit -s -S ...`): `-s` adds the `Signed-off-by` trailer required by the **DCO** check (CI fails without a trailer matching the commit author), and `-S` adds the cryptographic signature this repo expects (`commit.gpgsign` is enabled with SSH signing). This applies to amends and follow-up commits too (`git commit --amend -s -S`). Do **not** pass `--no-verify`/`--no-gpg-sign`. If signing fails because no key is reachable, fix the signing setup or ask the user rather than committing unsigned.
4. **Push**: Push the new branch to `origin` and set upstream.
5. **PR**: Create a pull request targeting **main** with a **suitable title** (lowercase, conventional prefix: e.g. `fix: ...`, `feat: ...`, `chore: ...`, `refactor: ...`, `test: ...`, `enhance: ...`) and **description** (summary of changes, what was added/fixed, and why if relevant). Use `gh pr create` when available.
6. **Label**: Add the label that matches the PR title prefix: **fix**, **feat**, **chore**, **docs**, **refactor**, **test**, **enhance** (and **release** for release PRs only). E.g. title `fix: ...` → `--label "fix"`. Use `gh pr create ... --label "<label>"` or `gh pr edit <number> --add-label "<label>"` after creating.

Infer branch name, commit message, and PR title/description from the staged changes and recent conversation. Do not include untracked or unstaged files unless the user explicitly asks.

Before pushing, run `make ci` (full lint, test, and coverage) when the changes touch Python code or tests.

---

## Release to PyPI

When the user asks to **release**, **publish**, **ship a version**, *"tag a release"*, *"bump version"*, or similar, use the two-step release helper at `scripts/release.py` (exposed as `make` targets). The changelog is hand-written: the user curates the `## [Unreleased]` section by hand; the script only handles the mechanics (version bump, promoting `[Unreleased]` to a dated section, compare-link footer, PR, tag, GitHub release). It never generates release-note prose.

This repo publishes to PyPI when a **`v*`** tag is pushed (see `.github/workflows/publish.yml`). There is no `prod` branch.

**Before running**, make sure the `## [Unreleased]` section of `CHANGELOG.md` is curated and complete for this release. Add/edit entries by hand if needed (do not auto-generate them from commit messages).

**Step 1 — open the release PR** (run from a clean tree):

```bash
make release-prep VERSION=0.4.0
```

This bumps `pyproject.toml`, rolls `[Unreleased]` into `## [0.4.0] - <today>` with updated compare links off `origin/main`, runs `make ci` (full lint + tests + coverage), commits `chore: release v0.4.0` on `release/v0.4.0`, pushes, and opens a PR to **main** (title `release: v0.4.0`, label **release**, body = the new changelog section).

**Step 2 — tag and publish** (after the PR is merged):

```bash
make release-tag VERSION=0.4.0
```

This checks out the latest `main`, verifies the bump landed, creates and pushes a signed annotated
`v0.4.0` tag (which triggers the Publish workflow → PyPI), and creates the GitHub release with the
changelog section as notes. Requires local GPG or SSH commit/tag signing configured and the public
key added to GitHub.

If the user only wants a version bump / PR without publishing yet, run **only** Step 1 and stop. Prefer the `make` targets over performing these steps by hand; fall back to manual git/`gh` only if the script cannot run.
