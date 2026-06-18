# MkDocs Source Links

[![PyPI](https://img.shields.io/pypi/v/mkdocs-source-links?logo=pypi&logoColor=white)](https://pypi.org/project/mkdocs-source-links)
[![CI](https://github.com/filipchristiansen/mkdocs-source-links/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/filipchristiansen/mkdocs-source-links/actions/workflows/ci.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/filipchristiansen/mkdocs-source-links/graph/badge.svg)](https://codecov.io/gh/filipchristiansen/mkdocs-source-links)
[![python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/downloads)
[![uv](https://img.shields.io/badge/uv-managed-DE5FE9?logo=astral)](https://docs.astral.sh/uv)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/mypy-checked-039dfc?logo=mypy&logoColor=white)](https://mypy-lang.org)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

MkDocs plugin that rewrites `](../path)` links to your git forge in **built HTML only**. Source markdown keeps relative paths so GitHub and your IDE still work.

- **Files** → `https://…/blob/<branch>/<path>`
- **Directories** → `https://…/tree/<branch>/<path>`
- **Forges:** GitHub, GitLab, Bitbucket, Gitea/Forgejo, Azure DevOps (autodetected; self-hosted via `forge:`)

**Documentation:** <https://filipchristiansen.github.io/mkdocs-source-links>

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
      forge: gitlab           # override autodetection for custom domains
      warn_on_missing: false  # silence missing-target warnings
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
make ci        # run the full pre-PR suite: lint, test, coverage
```

Maintainers release with `make release-prep VERSION=X.Y.Z` (bump, roll the hand-written
`CHANGELOG.md`, open the release PR) and, once merged, `make release-tag VERSION=X.Y.Z` (tag and
publish to PyPI).

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow and [CHANGELOG.md](CHANGELOG.md) for
release notes. Security issues: see [SECURITY.md](SECURITY.md).

## License

MIT
