# Forges

The plugin builds forge view URLs based on `repo_url`. Public forge hosts are detected
automatically. Hosts that cannot be identified are left unchanged (links are passed through
verbatim) unless you set [`forge`](configuration.md#options) explicitly.

## Support matrix

| Forge | Autodetected hosts | URL style |
| ----- | ------------------ | --------- |
| GitHub (incl. Enterprise) | `github.com`, `github.*` | `/blob/<branch>/<path>`, `/tree/...` |
| GitLab (incl. self-hosted) | `gitlab.com`, `gitlab.*` | `/-/blob/<branch>/<path>`, `/-/tree/...` |
| Bitbucket Cloud | `bitbucket.org`, `bitbucket.*` | `/src/<branch>/<path>` |
| Gitea / Forgejo / Codeberg | `codeberg.org`, `gitea.*`, `forgejo.*` | `/src/branch/<branch>/<path>` |
| Azure DevOps | `dev.azure.com`, `*.visualstudio.com` | `?path=/<path>&version=GB<branch>` |

## Self-hosted instances

Public hosts and common self-hosted patterns (for example GitHub Enterprise at
`github.example.com`) are detected automatically. For an instance on a domain that does not contain
the forge name, set the forge explicitly:

```yaml
plugins:
  - source-links:
      forge: gitlab   # github | gitlab | bitbucket | gitea | azure
```
