# MkDocs Source Links

[![PyPI](https://img.shields.io/pypi/v/mkdocs-source-links?logo=pypi&logoColor=white)](https://pypi.org/project/mkdocs-source-links)
[![CI](https://github.com/filipchristiansen/mkdocs-source-links/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/filipchristiansen/mkdocs-source-links/actions/workflows/ci.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/filipchristiansen/mkdocs-source-links/graph/badge.svg)](https://codecov.io/gh/filipchristiansen/mkdocs-source-links)
[![python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/downloads)
[![uv](https://img.shields.io/badge/uv-managed-DE5FE9?logo=astral)](https://docs.astral.sh/uv)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/mypy-checked-039dfc?logo=mypy&logoColor=white)](https://mypy-lang.org/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

MkDocs plugin that rewrites `](../path)` links to your git forge in **built HTML only**. Source markdown keeps relative paths so GitHub and your IDE still work.

- **Files** → `https://…/blob/<branch>/<path>`
- **Directories** → `https://…/tree/<branch>/<path>`
- **Forges:** GitHub, GitLab, Bitbucket, Gitea/Forgejo, Azure DevOps (autodetected; self-hosted via `forge:`)

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

## Link conventions

| Target | Source markdown | Built HTML |
| ------ | --------------- | ---------- |
| Page in `docs/` | `[runbook](other.md)` | unchanged (MkDocs handles it) |
| Repo file outside `docs/` | `[config](../backend/config.py)` | forge blob URL |
| Repo directory | `[scripts](../scripts/)` | forge tree URL |

## Branch configuration

Branch for forge URLs is resolved in order:

1. Plugin `branch:` config
2. `extra.git_branch` in `mkdocs.yml`
3. Parsed from `edit_uri` (`edit/<branch>/…` or `blob/<branch>/…`)
4. Fallback: `main`

If your default branch is not `main`, set `edit_uri`, `extra.git_branch`, or `source-links.branch`.

## Contributing

This project uses [uv](https://docs.astral.sh/uv), [pre-commit](https://pre-commit.com), and a `Makefile`.

```bash
make install   # install Python 3.10, sync all groups, set up pre-commit hooks
make ci        # run the full pre-PR suite: lint, test, coverage
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow and [CHANGELOG.md](CHANGELOG.md) for
release notes. Security issues: see [SECURITY.md](SECURITY.md).

## License

MIT
