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

For do/don't patterns, monorepo `../` depth, and shared root files, see
[Configuration recipes](recipes.md#choosing-link-styles).

--8<-- "docs/snippets/link_conventions_table.md"

Only complete inline `[text](../…)` links and `[ref]: ../…` definitions whose target resolves to an existing file or directory inside the repository
are rewritten. URL fragments (`#anchor`) are preserved. Lonely `](../…)` suffixes in prose are not matched.

## What it does not touch

- In-`docs/` links between pages (MkDocs resolves those itself).
- Links whose target does not exist on disk.
- Absolute URLs and non-`../` relative links.

For the full list of caveats, see [Limitations](limitations.md).
