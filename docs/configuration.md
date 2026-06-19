# Configuration

For scenario-based setup (monorepos, release builds, self-hosted forges), see
[Configuration recipes](recipes.md). The table below is a quick reference.

## Options

| Option | Type | Default | Description |
| ------ | ---- | ------- | ----------- |
| `enabled` | bool | `true` | Turn link rewriting on or off. When `false`, page markdown is left untouched and no git lookup runs. |
| `pin` | string | `branch` | Pin forge URLs to a branch name (`branch`), the current commit SHA (`commit`), or an exact tag at `HEAD` (`tag`). When `commit` or `tag` lookup fails, falls back to the resolved branch. |
| `branch` | string | resolved (see below) | Git branch used in forge URLs when `pin` is `branch`, or as fallback when `pin` is `commit` or `tag`. Tag names are valid here when set explicitly (for example `branch: v1.2.3`). |
| `forge` | string | autodetected | Forge type: `github`, `gitlab`, `bitbucket`, `gitea`, or `azure`. Overrides host autodetection. |
| `warn_on_missing` | bool | `true` | Emit a warning when a `](../path)` link's target does not exist in the repository. Counts toward `mkdocs build --strict`. |

```yaml
plugins:
  - source-links:
      branch: develop
      pin: commit             # permalink to HEAD SHA instead of branch name
      # pin: tag              # use exact tag at HEAD (e.g. v1.2.3); else resolved branch
      forge: gitlab           # only needed when autodetection can't identify the host
      warn_on_missing: false  # silence warnings for intentionally absent targets
```

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
