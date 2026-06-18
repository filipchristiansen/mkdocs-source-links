# MkDocs Source Links

[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/13299/badge)](https://www.bestpractices.dev/projects/13299)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/filipchristiansen/mkdocs-source-links/badge)](https://scorecard.dev/viewer/?uri=github.com/filipchristiansen/mkdocs-source-links)
[![PyPI](https://img.shields.io/pypi/v/mkdocs-source-links?logo=pypi&logoColor=white)](https://pypi.org/project/mkdocs-source-links)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/filipchristiansen/mkdocs-source-links/blob/main/LICENSE)
[![CI](https://github.com/filipchristiansen/mkdocs-source-links/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/filipchristiansen/mkdocs-source-links/actions/workflows/ci.yml?query=branch%3Amain)
[![python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/downloads)

MkDocs plugin that rewrites `](../path)` links to your git forge in **built HTML only**. Your
source markdown keeps relative paths, so links stay **clickable in your IDE and on GitHub** while
the published site points readers at the right blob/tree URL on your forge.

- **Files** -> `https://.../blob/<branch>/<path>`
- **Directories** -> `https://.../tree/<branch>/<path>`

## Why

Documentation often lives in `docs/` but links to files outside it (`../pyproject.toml`,
`../src/...`, `../scripts/`). Relative `../` paths are the right choice in source markdown: they
work on GitHub and in editors that resolve repo paths, so you can click through to the real file.
They break in a built MkDocs site because those files are not part of the rendered docs tree.

This plugin rewrites only parent-directory links in **built HTML**, leaving your markdown unchanged.
You keep IDE- and GitHub-friendly source links; site visitors get working forge URLs.

!!! note "This site dogfoods the plugin"
    These docs are built with `source-links` enabled. In the source markdown the link below points
    at [`../src/mkdocs_source_links/plugin.py`](../src/mkdocs_source_links/plugin.py) (a relative
    `../` path), but in this built page its destination is a GitHub URL.

## Install

```bash
pip install mkdocs-source-links
```

## Quick start

```yaml
# mkdocs.yml
site_name: My project
repo_url: https://github.com/you/your-repo
edit_uri: edit/main/docs/

plugins:
  - source-links
```

See [Usage](usage.md) for link conventions and [Configuration](configuration.md) for options.

## Get involved

- **Obtain:** install from [PyPI](https://pypi.org/project/mkdocs-source-links) (`pip install mkdocs-source-links`) or clone the [repository](https://github.com/filipchristiansen/mkdocs-source-links).
- **Feedback:** open a [bug report](https://github.com/filipchristiansen/mkdocs-source-links/issues/new?template=bug_report.md) or [feature request](https://github.com/filipchristiansen/mkdocs-source-links/issues/new?template=feature_request.md) on GitHub Issues.
- **Contribute:** see [Contributing](contributing.md) for setup, coding standards, and the pull request workflow.
