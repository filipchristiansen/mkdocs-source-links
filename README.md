# mkdocs-source-links

MkDocs plugin that rewrites `](../path)` links to your git forge in **built HTML only**. Source markdown keeps relative paths so GitHub and your IDE still work.

- **Files** → `https://…/blob/<branch>/<path>`
- **Directories** → `https://…/tree/<branch>/<path>`
- **v1:** GitHub only (other hosts: links left unchanged)

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
  - search
  - source-links
```

Optional branch override:

```yaml
plugins:
  - source-links:
      branch: develop
```

## Link conventions

| Target | Source markdown | Built HTML |
|--------|-----------------|------------|
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

## Not [mkdocs-repo-docs](https://pypi.org/project/mkdocs-repo-docs/)

| | **mkdocs-source-links** | **mkdocs-repo-docs** |
|--|-------------------------|----------------------|
| Approach | Rewrite outbound `../` links to the forge | Stage repo markdown into `docs/_repo/` |
| Source markdown | Keeps `../` paths | Files copied into docs tree |
| Use case | Link to source from hand-written docs | Auto-publish scattered READMEs |

## Development

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
```

## Publishing to PyPI

1. Create a [PyPI](https://pypi.org/) project `mkdocs-source-links`
2. Configure [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) for the `Publish` workflow (`environment: pypi`)
3. Tag a release: `git tag v0.1.0 && git push origin v0.1.0`

## License

MIT
