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
| Gitea / Forgejo / Codeberg | `codeberg.org`, `gitea.*`, `forgejo.*` | `/src/branch/<branch>/<path>`, `/src/commit/<sha>/<path>` |
| Azure DevOps | `dev.azure.com`, `*.visualstudio.com` | `?path=/<path>&version=GB<branch>` |

## Autodetection limits

Self-hosted detection matches forge names as **hostname labels** (for example `gitlab.example.com`
or `github-internal.corp`), not arbitrary substrings. A host like `notgitlab.com` is not treated
as GitLab. When autodetection cannot identify your forge, set [`forge`](configuration.md#options)
explicitly.

## Self-hosted instances

Public hosts and common self-hosted patterns (for example GitHub Enterprise at
`github.example.com`) are detected automatically via hostname labels. For an instance on a domain
that does not contain the forge name as a label, set the forge explicitly:

```yaml
plugins:
  - source-links:
      forge: gitlab   # github | gitlab | bitbucket | gitea | azure
```
