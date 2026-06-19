# Configuration recipes

Scenario-based setup for **mkdocs-source-links**: MkDocs prerequisites, link conventions, plugin options,
worked `mkdocs.yml` examples, and fixed behavior. For the compact options table see
[Configuration](configuration.md); for forge autodetection see [Forges](forges.md); for caveats see
[Limitations](limitations.md).

## Prerequisites

The plugin rewrites `](../path)` links during `mkdocs build` using three layers of MkDocs configuration
plus its own options.

### MkDocs settings

| Setting | Role |
| ------- | ---- |
| `repo_url` | **Required** for rewriting. Without it, all `../` links are left unchanged. |
| `edit_uri` | When plugin `branch` and `extra.git_branch` are unset, the branch name is parsed from `edit/` or `blob/` in this path (GitLab `-/edit/<branch>/…` is supported). |
| `extra.git_branch` | Overrides `edit_uri` for branch resolution when plugin `branch` is unset. |

`repo_url` also supplies the forge host for URL building. Autodetection uses hostname labels such as
`github.com`, `gitlab.example.com`, or `github-internal.corp`. When the host cannot be identified, set
[`forge`](configuration.md#options) explicitly — see [Self-hosted GitLab on a neutral hostname](#self-hosted-gitlab-on-a-neutral-hostname)
and [Forges](forges.md).

### Branch resolution order

When plugin `branch` is not set explicitly, the branch name embedded in forge URLs is resolved in this
order:

--8<-- "docs/snippets/branch_resolution.md"

`pin` controls whether that resolved name (or an override) is used in URLs, or whether `HEAD` is resolved
to a commit SHA or exact tag — see [`pin` and ref modes](#pin-and-ref-modes).

### Repository root for path resolution

The plugin resolves `../` links relative to each page file on disk, but only within the directory that
contains `mkdocs.yml` (MkDocs `config_file_path` parent). That directory is the **plugin repository
root** — it is not always the git repository root.

- `mkdocs.yml` at the monorepo root with `docs_dir: packages/foo/docs` → root is the monorepo.
- `mkdocs.yml` inside `packages/foo/` → root is `packages/foo/`; paths outside that directory are not
  rewritten.

The shell working directory for `mkdocs build` does not change this; only the config file path matters.
Use `mkdocs build -f path/to/mkdocs.yml` when the config is not in the current directory.

## Choosing link styles

### Supported targets

--8<-- "docs/snippets/link_conventions_table.md"

### Do

| Pattern | Example | Notes |
| ------- | ------- | ----- |
| Inline parent-directory link | `[config](../backend/config.py)` | File → forge blob URL |
| Inline directory link | `[scripts](../scripts/)` | Directory → forge tree URL |
| Reference definition | `[cfg]: ../backend/config.py` | Usages `[text][cfg]` pick up the forge URL |
| Titled link | `[x](../path "title")` | Title preserved |
| Angle-bracket destination | `[x](<../path with spaces>)` | Spaces percent-encoded in output |
| Line fragment | `[x](../src/foo.py#L10-L20)` | Translated per forge — see [Limitations](limitations.md#line-anchors) |
| In-`docs/` page link | `[other](other.md)` | Unchanged; MkDocs resolves it |

### Don't (left unchanged)

| Pattern | Example | Why |
| ------- | ------- | --- |
| No `../` prefix | `[x](src/foo.py)`, `[x](./foo.py)` | Only parent-directory links match |
| HTML link | `<a href="../foo">` | Markdown-only rewrite |
| Absolute / hard-coded blob URL | `https://github.com/.../blob/old/src/foo.py` | Pass through — use for one-off historical refs |
| Missing on-disk target | `[x](../not-there.py)` | Not rewritten; warning by default |
| Outside plugin root | `[x](../../outside)` when root is a subdirectory | Path outside `mkdocs.yml` directory |
| Virtual page | Generated page with no source file | No `abs_src_path` to resolve from |

### Shared root files (GitHub, IDE, and built site)

Documentation often lives in `docs/` while governance files (`README.md`, `CONTRIBUTING.md`,
`ROADMAP.md`) sit at the repository root. Relative `../` links work on GitHub and in the IDE; on the
built site you can include root markdown with **pymdownx snippets** instead of duplicating content:

```yaml
exclude_docs: snippets/*

markdown_extensions:
  - pymdownx.snippets:
      base_path: ["."]
      check_paths: true
```

In a doc page:

```markdown
--8<-- "CONTRIBUTING.md"
```

Root files stay editable in one place; the built page renders the included content. Snippet setup is
MkDocs configuration, not a plugin option. See [Contributing](contributing.md) for this project's
workflow.

## Plugin options reference

| Option | Type | Default | When to use |
| ------ | ---- | ------- | ----------- |
| `enabled` | bool | `true` | Turn rewriting off for local preview, or gate with an environment variable. |
| `pin` | string | `branch` | `branch` — normal docs; `commit` — permalink to `HEAD` SHA; `tag` — exact tag at `HEAD` (release builds). |
| `branch` | string | resolved | Override branch resolution; set an explicit tag name (`branch: v1.2.3`) when not building from that tag. |
| `forge` | string | autodetected | Host without a forge hostname label (e.g. `git.mycompany.com` running GitLab). |
| `warn_on_missing` | bool | `true` | `false` to silence missing-target warnings; `true` with `mkdocs build --strict` for CI. |

Valid `forge` values: `github`, `gitlab`, `bitbucket`, `gitea`, `azure`. See [Forges](forges.md) for the
support matrix, autodetection limits, and **unsupported** hosts (Bitbucket Server, SourceHut, etc.).

### `enabled`

Skip rewriting without editing config on each serve:

```yaml
plugins:
  - source-links:
      enabled: !ENV [SOURCE_LINKS, true]
```

```bash
SOURCE_LINKS=false mkdocs serve
```

When `enabled: false`, markdown is untouched and no `git` lookup runs.

### `pin`

```yaml
plugins:
  - source-links:
      pin: branch   # default — resolved branch name in URLs
      # pin: commit # HEAD SHA (permalink)
      # pin: tag    # exact tag at HEAD (release CI)
```

### `branch`

```yaml
plugins:
  - source-links:
      branch: develop
```

Also use for a hardcoded tag when you are not on that tag checkout: `pin: branch` with `branch: v1.2.3`.

### `forge`

```yaml
plugins:
  - source-links:
      forge: gitlab
```

Only when autodetection cannot identify the host. Do not set `forge: bitbucket` on Bitbucket
Server/Data Center — see [Forges](forges.md#unsupported-forges).

### `warn_on_missing`

```yaml
plugins:
  - source-links:
      warn_on_missing: false
```

## `pin` and ref modes

Every rewritten link uses the **same** git ref for the whole build. There is no per-link override; for a
single historical link use a full forge blob URL in markdown ([Limitations](limitations.md#git-ref-and-historical-links)).

| `pin` | Forge URL ref | `git` required? | Fallback |
| ----- | ------------- | --------------- | -------- |
| `branch` | Resolved branch (or `branch:` override) | No | — |
| `commit` | `git rev-parse HEAD` | Yes | Resolved branch |
| `tag` | `git describe --tags --exact-match` | Yes | Resolved branch |

### `pin: branch`

Default. Forge URLs use the resolved branch name (`main`, `develop`, etc.). Works in environments
without `git`.

### `pin: commit`

Embeds the current `HEAD` commit SHA in blob/tree URLs (permalink). If `git` is unavailable or fails,
falls back to the resolved branch.

### `pin: tag`

For **release documentation builds**: check out the release tag in CI, then:

```yaml
plugins:
  - source-links:
      pin: tag
```

If `HEAD` is exactly tagged (e.g. `v1.2.3`), URLs use that tag name. If `HEAD` is not exactly tagged,
falls back to the resolved branch.

**Hardcoded tag without tag checkout:** use `pin: branch` with an explicit branch override:

```yaml
plugins:
  - source-links:
      pin: branch
      branch: v1.2.3
```

### Example CI pattern (release from tag)

```yaml
# .github/workflows/docs.yml (illustrative)
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.ref }}  # tag ref for release workflow
      - run: pip install mkdocs mkdocs-material mkdocs-source-links
      - run: mkdocs build --strict
```

With `pin: tag` in `mkdocs.yml`, published links point at `vX.Y.Z` on the forge.

## Common recipes

Each recipe assumes a layout like the integration test fixtures: `docs/`, `backend/config.py`,
`scripts/`, and `mkdocs.yml` at the plugin repository root unless noted.

### Default GitHub / `main`

```yaml
site_name: My project
repo_url: https://github.com/you/your-repo
edit_uri: edit/main/docs/

plugins:
  - source-links
```

**Before** (source markdown in `docs/index.md`):

```markdown
[config](../backend/config.py)
```

**After** (built HTML href):

```text
https://github.com/you/your-repo/blob/main/backend/config.py
```

### `develop` branch

Option A — derive branch from `edit_uri`:

```yaml
edit_uri: edit/develop/docs/
```

Option B — explicit plugin override (wins over `edit_uri`):

```yaml
plugins:
  - source-links:
      branch: develop
```

### Local serve without rewriting

```yaml
plugins:
  - source-links:
      enabled: !ENV [SOURCE_LINKS, true]
```

```bash
SOURCE_LINKS=false mkdocs serve
```

Built HTML during serve still rewrites by default; use `enabled: false` or the env var when you want
`../` links untouched.

### Release from tag

Check out the release tag, then:

```yaml
plugins:
  - source-links:
      pin: tag
```

### Strict CI (catch broken links)

Default `warn_on_missing: true` plus:

```bash
mkdocs build --strict
```

Warnings for missing `../` targets fail the build.

### Silent missing links

```yaml
plugins:
  - source-links:
      warn_on_missing: false
```

Use when some `../` links intentionally point at paths not present in every checkout.

### Self-hosted GitLab on a neutral hostname

Autodetection matches forge names as **hostname labels** (`gitlab.example.com`), not arbitrary domains.
`https://git.mycompany.com/org/repo` is left unchanged unless `forge` is set.

```yaml
site_name: Internal docs
repo_url: https://scm.internal.example/org/repo
edit_uri: -/edit/main/docs/

plugins:
  - source-links:
      forge: gitlab
```

**Before:**

```markdown
[config](../backend/config.py)
```

**After:**

```text
https://scm.internal.example/org/repo/-/blob/main/backend/config.py
```

See [Forges](forges.md#self-hosted-instances) for autodetection vs explicit `forge`.

### GitHub Enterprise

Hosts such as `github-internal.corp` autodetect as GitHub (hostname label `github`). No `forge` needed:

```yaml
repo_url: https://github-internal.corp/org/repo
edit_uri: edit/main/docs/

plugins:
  - source-links
```

### Monorepo with `docs_dir` at repo root

```text
my-monorepo/
  mkdocs.yml
  README.md
  packages/foo/
    docs/
      index.md
    src/
      foo.py
```

```yaml
site_name: Foo package
repo_url: https://github.com/you/my-monorepo
edit_uri: edit/main/docs/
docs_dir: packages/foo/docs

plugins:
  - source-links
```

From `packages/foo/docs/index.md`:

| Source markdown | Resolves to repo path | Built link path segment |
| --------------- | --------------------- | ----------------------- |
| `[src](../src/foo.py)` | `packages/foo/src/foo.py` | `.../blob/main/packages/foo/src/foo.py` |
| `[readme](../../README.md)` | `README.md` | `.../blob/main/README.md` |

`repo_url` is always the **git** repository URL (monorepo root), not a package subdirectory.

### Nested `mkdocs.yml` (subdirectory config)

```text
my-monorepo/
  README.md
  packages/foo/
    mkdocs.yml
    docs/
      index.md
    src/
      foo.py
```

Build with:

```bash
mkdocs build -f packages/foo/mkdocs.yml
```

Plugin repository root is `packages/foo/`. A link `[readme](../../README.md)` resolves outside that
root and is **not** rewritten. Prefer `mkdocs.yml` at the monorepo root with `docs_dir`, or accept that
only paths under `packages/foo/` are linkable via `../`.

## Fixed behavior

Summary of behavior that does not change with configuration. Details in [Limitations](limitations.md).

| Topic | Behavior |
| ----- | -------- |
| Rewrite stage | `on_page_markdown` — markdown only, not HTML (`on_page_content` is not used). |
| Code blocks | Fenced blocks (`` ``` `` or `~~~`) and inline code spans are skipped; **indented** (4-space) code blocks are not — use fences for literal examples. |
| Virtual pages | Pages without a backing markdown file are unchanged. |
| Line anchors | `#L10`, `#L10-L20` translated per forge; Azure DevOps omits line fragments. |
| Targets | Only existing files/directories under the plugin root at build time; directory targets treat trailing slash as optional. |
| Global ref | One ref per build from `pin` / `branch`; no per-link ref override. |

## Full example

Commented `mkdocs.yml` combining common settings (generic placeholders):

```yaml
site_name: My project
site_url: https://you.github.io/your-repo/   # optional; site URL for MkDocs

# Required for source-links rewriting
repo_url: https://github.com/you/your-repo
repo_name: you/your-repo

# Branch for forge URLs when plugin branch / extra.git_branch unset
edit_uri: edit/main/docs/

# Alternative branch override (second priority after plugin branch:)
# extra:
#   git_branch: develop

# Monorepo: point docs_dir at package docs while mkdocs.yml stays at repo root
# docs_dir: packages/foo/docs

exclude_docs: snippets/*   # if using pymdownx snippets for root markdown

theme:
  name: material

plugins:
  - search
  - source-links:
      enabled: !ENV [SOURCE_LINKS, true]   # SOURCE_LINKS=false mkdocs serve
      pin: branch                            # branch | commit | tag
      # branch: develop                       # override resolved branch
      # forge: gitlab                         # neutral hostname only
      warn_on_missing: true                  # false to silence; true + --strict for CI

markdown_extensions:
  - admonition
  - toc:
      permalink: true
  - pymdownx.highlight
  - pymdownx.superfences
  - pymdownx.snippets:          # optional: include root markdown in docs
      base_path: ["."]
      check_paths: true
```

## Decision tree

Use this flow for `pin` and `forge`; adjust the other options as needed:

- **`enabled: false`** or `SOURCE_LINKS=false` — skip rewriting for local iteration.
- **`branch:`** — override resolved branch, or hardcode a tag name with `pin: branch`.
- **`warn_on_missing: false`** — allow missing `../` targets without warnings.

1. **`repo_url` set?** If no → links unchanged. If yes → continue.
2. **Release build at an exact tag checkout?** If yes → `pin: tag`. If no → continue.
3. **Need permalink to `HEAD` SHA?** If yes → `pin: commit`. If no → `pin: branch` (default).
4. **Host autodetects forge?** If no → set `forge` explicitly (see [Forges](forges.md)). If yes → build.

Further reading: [Configuration](configuration.md) · [Usage](usage.md) · [Forges](forges.md) ·
[Limitations](limitations.md)
