# Forges

The plugin builds forge view URLs based on `repo_url`. Use an **HTTPS** repository URL (the same
shape MkDocs expects for theme repo/edit links). Query strings and URL fragments in `repo_url` are
stripped when building forge links.

Public forge hosts are detected automatically. When autodetection fails and no [`forge`](configuration.md#options)
override is set, the plugin emits a **once-per-build warning** and leaves matching `../` links
unchanged.

A trailing `.git` suffix on `repo_url` is stripped when building view URLs.

## Support matrix

| Forge | Autodetected hosts | URL style |
| ----- | ------------------ | --------- |
| GitHub (incl. Enterprise) | `github.com`, `github.*` | `/blob/<ref>/<path>`, `/tree/…` |
| GitLab (incl. self-hosted) | `gitlab.com`, `gitlab.*` | `/-/blob/<ref>/<path>`, `/-/tree/…` |
| Bitbucket Cloud | `bitbucket.org` only | `/src/<ref>/<path>` |
| Gitea / Forgejo / Codeberg | `codeberg.org`, `gitea.*`, `forgejo.*` | `/src/branch/<ref>/…`, `/src/tag/<ref>/…`, `/src/commit/<ref>/…` |
| Azure DevOps | `dev.azure.com`, `*.visualstudio.com` | `?path=/<path>&version=GB{branch}` (`GT{tag}`, `GC{sha}`) |

`<ref>` is the branch name, commit SHA, or tag name from [`pin`](configuration.md#options) and
[`branch`](configuration.md#options) resolution.

## Pin modes and URL shape

Every rewritten link uses the same ref for the build. With [`pin: branch`](configuration.md#options)
(default), URLs embed the resolved branch name. With `pin: commit`, the current `HEAD` SHA is
embedded. With `pin: tag`, an exact tag at `HEAD` is embedded (otherwise the resolved branch is
used and a warning is emitted).

| Forge | Branch (`pin: branch`) | Commit (`pin: commit`) | Tag (`pin: tag`) |
| ----- | ---------------------- | ---------------------- | ---------------- |
| GitHub | `/blob/<branch>/…` or `/tree/…` | `/blob/<sha>/…` | `/blob/<tag>/…` |
| GitLab | `/-/blob/<branch>/…` | `/-/blob/<sha>/…` | `/-/blob/<tag>/…` |
| Bitbucket Cloud | `/src/<branch>/…` | `/src/<sha>/…` | `/src/<tag>/…` |
| Gitea / Forgejo | `/src/branch/<branch>/…` | `/src/commit/<sha>/…` | `/src/tag/<tag>/…` |
| Azure DevOps | `version=GB{branch}` | `version=GC{sha}` | `version=GT{tag}` |

Azure uses the same `?path=/<path>` query for all pin modes; only the `version=` prefix changes.
Bitbucket and GitHub/GitLab use the same path pattern for branch names, tags, and commit SHAs.

**Hardcoded tag via `branch:`:** Setting `pin: branch` with `branch: v1.2.3` (without a tag
checkout) always emits a **branch** ref in URLs. On GitHub, GitLab, and Bitbucket Cloud that often
still works because branch and tag names share the same path shape. On **Gitea/Forgejo/Codeberg**
and **Azure DevOps** it produces the wrong URL kind (`/src/branch/v1.2.3/…` instead of
`/src/tag/v1.2.3/…`, or `version=GBv1.2.3` instead of `version=GTv1.2.3`). Use [`pin: tag`](recipes.md#pin-tag)
from an exact tag checkout, or paste a full forge URL for one-off links. See
[Limitations — Hardcoded tag names](limitations.md#hardcoded-tag-names).

## Autodetection limits

Self-hosted detection matches forge names as **whole hostname labels** (for example
`gitlab.example.com` or `github.example.com`), not arbitrary substrings. Hosts like `notgitlab.com`
or `github-internal.corp` — where the forge name is only **part** of a label — are not matched and
need an explicit [`forge`](configuration.md#options) setting. **Bitbucket Cloud** is only autodetected at `bitbucket.org`; self-hosted Bitbucket
Server/Data Center hostnames are not matched (see [unsupported forges](#unsupported-forges)). When
autodetection cannot identify your forge, set [`forge`](configuration.md#options) explicitly.

## Self-hosted instances

For a full `mkdocs.yml` example on a neutral hostname (e.g. GitLab at `scm.internal.example`), see
[Configuration recipes](recipes.md#self-hosted-gitlab-on-a-neutral-hostname).

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
| **Bitbucket Server / Data Center** | Different URL scheme from Bitbucket Cloud (`/projects/.../browse/...?at=...`). Self-hosted hostnames (for example `bitbucket.corp.com`) are **not autodetected** — `../` links are left unchanged unless you set `forge` explicitly. Do **not** set `forge: bitbucket` on Server/DC; that uses Bitbucket Cloud URL shape and will be wrong. Use full Server/DC browse URLs in markdown instead. |
| **SourceHut** (`git.sr.ht`) | Not autodetected or supported. |
| **AWS CodeCommit** | Console browse URLs differ from the git clone host; not supported. |
| **Google Gitiles** (`*.googlesource.com`) | Distinct `/+ref/path` URL scheme; not supported. |
| **Other forges** | e.g. Pagure, Savannah, cloud vendor git UIs — not autodetected; use full blob URLs. |
