# Configuration

For scenario-based setup (monorepos, release builds, self-hosted forges), see
[Configuration recipes](recipes.md). The table below is a quick reference.

## Options

| Option | Type | Default | Description |
| ------ | ---- | ------- | ----------- |
| `enabled` | bool | `true` | Turn link rewriting on or off. When `false`, page markdown is left untouched and no git lookup runs. |
| `pin` | string | `branch` | Pin forge URLs to a branch name (`branch`), the current commit SHA (`commit`), or an exact tag at `HEAD` (`tag`). When `commit` or `tag` lookup fails, falls back to the resolved branch and emits a build warning. |
| `branch` | string | resolved (see below) | Git branch used in forge URLs when `pin` is `branch`, or as fallback when `pin` is `commit` or `tag`. You may set a tag name explicitly (for example `branch: v1.2.3`), but that is **not forge-neutral** — Gitea/Forgejo/Codeberg and Azure DevOps use different URL shapes for branches and tags. Prefer [`pin: tag`](recipes.md#pin-tag) from a tag checkout on those forges, or a full forge blob URL for one-off historical links. |
| `forge` | string | autodetected | Forge type: `github`, `gitlab`, `bitbucket`, `gitea`, or `azure`. Overrides host autodetection. |
| `warn_on_missing` | bool | `true` | Emit a warning when a `../` link target does not exist in the repository (inline `[text](../path)` or `[ref]: ../path`). Counts toward `mkdocs build --strict`. |
| `log_rewrites` | `false` \| `summary` \| `verbose` | `false` | Opt-in INFO logging of successful `../` rewrites. Requires `repo_url`. Use YAML boolean `false`, not a quoted string. |

```yaml
plugins:
  - source-links:
      branch: develop
      pin: commit             # permalink to HEAD SHA instead of branch name
      # pin: tag              # use exact tag at HEAD (e.g. v1.2.3); else resolved branch
      forge: gitlab           # only needed when autodetection can't identify the host
      warn_on_missing: false  # silence warnings for intentionally absent targets
      log_rewrites: summary   # or verbose for per-page counts
```

### `log_rewrites`

When enabled, rewrite statistics appear at INFO level in normal `mkdocs build` output (no `-v`
required). `mkdocs build -q` suppresses INFO output, so rewrite statistics are hidden in quiet
mode. Counts include successful inline `[text](../…)` links and `[ref]: ../…` definitions only.

| Value | Output |
| ----- | ------ |
| `false` | No rewrite statistics (default). |
| `summary` | One build line, e.g. `Rewrote 42 links across 8 pages`. |
| `verbose` | Per-page lines for pages with rewrites, plus the summary line, e.g. `guide.md: rewrote 3 links`. Also logs when a reference definition is skipped because its label is shared with an image reference on the same page. |

Per-page paths in `verbose` mode are MkDocs `src_path` values (relative to the docs directory,
such as `guide.md` or `nested/page.md`), the same format used in `warn_on_missing` warnings — not
a `docs/` prefix.

If rewriting is active but no `../` links were rewritten, the summary reports zero links and zero
pages. When `repo_url` is unset, no statistics are logged.

### Disabling per environment

`enabled` accepts an environment variable so you can skip rewriting during local iteration
without editing config:

```yaml
plugins:
  - source-links:
      enabled: !ENV [SOURCE_LINKS, true]
```

Then run `SOURCE_LINKS=false mkdocs serve` to leave `../` links untouched.

See [Forges](forges.md) for the support matrix and when `forge` is needed.

## Branch resolution

When `branch` is not set explicitly, it is resolved in this order:

--8<-- "docs/snippets/branch_resolution.md"

```yaml
# Example: resolve branch from edit_uri
edit_uri: edit/trunk/docs/

plugins:
  - source-links
```
