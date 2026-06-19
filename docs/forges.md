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

## Unsupported forges

The plugin does **not** build view URLs for these hosts. Use full forge blob URLs in markdown
(they pass through unchanged) or open a [feature request](https://github.com/filipchristiansen/mkdocs-source-links/issues/new?template=feature_request.md).

| Host | Notes |
| ---- | ----- |
| **Bitbucket Server / Data Center** | Different URL scheme from Bitbucket Cloud (`/projects/.../browse/...?at=...`). A self-hosted hostname containing `bitbucket` (for example `bitbucket.corp.com`) is autodetected as **Cloud** and rewritten links will be **wrong** — do not set `forge: bitbucket` on Server/DC. |
| **SourceHut** (`git.sr.ht`) | Not autodetected or supported. |
| **AWS CodeCommit** | Console browse URLs differ from the git clone host; not supported. |
| **Google Gitiles** (`*.googlesource.com`) | Distinct `/+ref/path` URL scheme; not supported. |
| **Other forges** | e.g. Pagure, Savannah, cloud vendor git UIs — not autodetected; use full blob URLs. |
