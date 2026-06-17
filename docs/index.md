# MkDocs Source Links

[![PyPI](https://img.shields.io/pypi/v/mkdocs-source-links?logo=pypi&logoColor=white)](https://pypi.org/project/mkdocs-source-links)

MkDocs plugin that rewrites `](../path)` links to your git forge in **built HTML only**. Your
source markdown keeps relative paths, so links still work on GitHub and in your IDE.

- **Files** -> `https://.../blob/<branch>/<path>`
- **Directories** -> `https://.../tree/<branch>/<path>`

## Why

In a typical repo, documentation lives in `docs/` but references files that live outside it
(`../pyproject.toml`, `../src/...`, `../scripts/`). Those relative links are correct on GitHub and
in your editor, but they break in a built MkDocs site because the file isn't part of the rendered
docs. This plugin rewrites only those parent-directory links to point at the forge, leaving the
source untouched.

!!! note "This site dogfoods the plugin"
    These docs are built with `source-links` enabled. The link to
    [the plugin source](../src/mkdocs_source_links/plugin.py) below the `docs/` directory is a
    relative `../` link in markdown, but in this built page it points at GitHub.

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
