# Configuration

## Options

| Option | Type | Default | Description |
| ------ | ---- | ------- | ----------- |
| `pin` | string | `branch` | Pin forge URLs to a branch name (`branch`) or the current commit SHA (`commit`). When `commit`, falls back to the resolved branch if git is unavailable. |
| `branch` | string | resolved (see below) | Git branch used in forge URLs when `pin` is `branch`, or as fallback when `pin` is `commit`. |
| `forge` | string | autodetected | Forge type: `github`, `gitlab`, `bitbucket`, `gitea`, or `azure`. Overrides host autodetection. |

```yaml
plugins:
  - source-links:
      branch: develop
      pin: commit     # permalink to HEAD SHA instead of branch name
      forge: gitlab   # only needed when autodetection can't identify the host
```

See [Forges](forges.md) for the support matrix and when `forge` is needed.

## Branch resolution

When `branch` is not set explicitly, it is resolved in this order:

1. Plugin `branch:` config
2. `extra.git_branch` in `mkdocs.yml`
3. Parsed from `edit_uri` (`edit/<branch>/...` or `blob/<branch>/...`)
4. Fallback: `main`

If your default branch is not `main`, set `edit_uri`, `extra.git_branch`, or `source-links.branch`
so links point at the right ref.

```yaml
# Example: resolve branch from edit_uri
edit_uri: edit/trunk/docs/

plugins:
  - source-links
```
