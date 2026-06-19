# MkDocs Source Links

[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/13299/badge)](https://www.bestpractices.dev/projects/13299)
[![OpenSSF Baseline](https://www.bestpractices.dev/projects/13299/baseline)](https://www.bestpractices.dev/projects/13299)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/filipchristiansen/mkdocs-source-links/badge)](https://scorecard.dev/viewer/?uri=github.com/filipchristiansen/mkdocs-source-links)
[![SLSA 3](https://slsa.dev/images/gh-badge-level3.svg)](https://github.com/filipchristiansen/mkdocs-source-links/releases/latest)
[![PyPI](https://img.shields.io/pypi/v/mkdocs-source-links?logo=pypi&logoColor=white)](https://pypi.org/project/mkdocs-source-links)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/filipchristiansen/mkdocs-source-links/blob/main/LICENSE)
[![CI](https://github.com/filipchristiansen/mkdocs-source-links/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/filipchristiansen/mkdocs-source-links/actions/workflows/ci.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/filipchristiansen/mkdocs-source-links/graph/badge.svg)](https://codecov.io/gh/filipchristiansen/mkdocs-source-links)
[![python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/downloads)
[![uv](https://img.shields.io/badge/uv-managed-DE5FE9?logo=astral)](https://docs.astral.sh/uv)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/mypy-checked-039dfc?logo=mypy&logoColor=white)](https://mypy-lang.org)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

MkDocs plugin that rewrites `](../path)` links to your git forge during **`on_page_markdown`** (before HTML is built). Source markdown on disk is unchanged; forge URLs appear in the built site.

- **Files** → `https://…/blob/<ref>/<path>` (GitHub/GitLab; forge-specific paths on Gitea, Bitbucket, Azure)
- **Directories** → `https://…/tree/<ref>/<path>` where the forge distinguishes files from directories
- **Pin ref:** `pin: branch` (default), `pin: commit` (HEAD SHA), or `pin: tag` (exact tag at `HEAD`; Gitea uses `/src/tag/…`, Azure uses `GT…`)
- **Forges:** GitHub, GitLab, Bitbucket Cloud, Gitea/Forgejo, Azure DevOps (autodetected; self-hosted via `forge:`)

**Documentation:** <https://filipchristiansen.github.io/mkdocs-source-links/>

## Install

```bash
pip install mkdocs-source-links
```

## Usage

```yaml
site_name: My project
repo_url: https://github.com/you/your-repo
edit_uri: edit/main/docs/

plugins:
  - source-links
```

Requires `repo_url` in `mkdocs.yml` (shown above). Without it, links are left unchanged.

Optional branch override:

```yaml
plugins:
  - source-links:
      branch: develop
```

## Advanced options

```yaml
plugins:
  - source-links:
      pin: commit             # embed HEAD SHA instead of branch name
      # pin: tag              # exact tag at HEAD (release builds); else resolved branch
      forge: gitlab           # override autodetection for custom domains
      warn_on_missing: false  # silence missing-target warnings
      log_rewrites: summary   # or verbose for per-page counts; false by default
      enabled: !ENV [SOURCE_LINKS, true]  # disable per environment
```

Line fragments in links (`#L10`, `#L10-L20`) are translated to each forge's line-reference
syntax. See the [configuration docs](https://filipchristiansen.github.io/mkdocs-source-links/configuration/)
for all options.

## Link conventions and branch resolution

Parent-directory links (`../path`) to repo files and directories are rewritten to forge blob/tree
URLs; links between pages inside `docs/` are unchanged. Branch names are resolved from plugin
config, `extra.git_branch`, or `edit_uri`.

See [Usage](https://filipchristiansen.github.io/mkdocs-source-links/usage/) and
[Configuration](https://filipchristiansen.github.io/mkdocs-source-links/configuration/) in the docs
for the full tables and resolution order.

## Contributing

This project uses [uv](https://docs.astral.sh/uv), [pre-commit](https://pre-commit.com), and a `Makefile`.

```bash
make install   # install Python 3.10, sync all groups, set up pre-commit hooks
make ci        # pre-PR checks: lint, audit, test (with coverage), docs build
```

Maintainers release with `make release-prep VERSION=X.Y.Z` (bump, roll the hand-written
`CHANGELOG.md`, open the release PR) and, once merged, `make release-tag VERSION=X.Y.Z` (signed tag
and publish to PyPI).

See [Contributing](https://filipchristiansen.github.io/mkdocs-source-links/contributing/) for the full workflow and [Changelog](https://filipchristiansen.github.io/mkdocs-source-links/changelog/) for
release notes. Further reading: [Governance](https://filipchristiansen.github.io/mkdocs-source-links/governance/), [Roadmap](https://filipchristiansen.github.io/mkdocs-source-links/roadmap/), [Support](https://filipchristiansen.github.io/mkdocs-source-links/support/), [Code of conduct](https://filipchristiansen.github.io/mkdocs-source-links/code-of-conduct/), [Maintainers](https://github.com/filipchristiansen/mkdocs-source-links/blob/main/MAINTAINERS.md), [Security policy](https://github.com/filipchristiansen/mkdocs-source-links/blob/main/SECURITY.md), and [Release verification](https://filipchristiansen.github.io/mkdocs-source-links/security/).

## License

MIT
