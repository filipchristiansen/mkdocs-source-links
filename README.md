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

## Development

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
```

## License

MIT
