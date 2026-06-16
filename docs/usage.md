# Usage

Enable the plugin in `mkdocs.yml` and make sure `repo_url` is set:

```yaml
site_name: My project
repo_url: https://github.com/you/your-repo
edit_uri: edit/main/docs/

plugins:
  - source-links
```

Without `repo_url`, links are left unchanged.

## Link conventions

| Target | Source markdown | Built HTML |
| ------ | --------------- | ---------- |
| Page in `docs/` | `[runbook](other.md)` | unchanged (MkDocs handles it) |
| Repo file outside `docs/` | `[config](../backend/config.py)` | forge blob URL |
| Repo directory | `[scripts](../scripts/)` | forge tree URL |

Only `](../...)` links whose target resolves to an existing file or directory inside the repository
are rewritten. URL fragments (`#anchor`) are preserved.

## What it does not touch

- In-`docs/` links between pages (MkDocs resolves those itself).
- Links whose target does not exist on disk.
- Absolute URLs and non-`../` relative links.

For the full list of caveats, see [Limitations](limitations.md).
