# Limitations

Known limitations of the current release. Several are tracked on the
[issue tracker](https://github.com/filipchristiansen/mkdocs-source-links/issues).

## Link syntax

Complete inline `[text](../path)` links are matched, including titled links (`[text](../x "title")`) and angle-bracket
destinations (`[text](<../x>)`, which may contain spaces); the title and fragment are preserved, and
spaces are percent-encoded in the resulting URL. A bare (non-angle-bracket) destination ends at the
first space, so a link to a path that contains spaces such as `[text](../wide img.png)` is **not**
matched; wrap the destination in angle brackets — `[text](<../wide img.png>)` — for it to be rewritten. Reference-style definitions (`[ref]: ../path`,
optional title) are rewritten the same way; usages such as `[text][ref]` pick up the forge URL
when the markdown processor resolves the reference. Inline and reference labels may contain nested
(`[a [b]]`) or backslash-escaped (`[a\]b]`) `]` characters.

Reference definitions must fit on a **single line**. Multi-line definitions (for example a title
wrapped to the next line) are not matched and are left unchanged.

Rewriting is text-level over the page markdown, but fenced code blocks (backtick or
tilde fences) and inline code spans are detected and skipped, so a literal `](../path)` or
`[ref]: ../path` shown as an example is left unchanged.

**Indented code blocks** (four-space or tab-indented paragraphs) are **not** skipped. A complete
inline `[text](../path)` link inside an indented block **will be rewritten**; lonely `](../path)`
suffixes in prose are not matched. Use fenced code blocks for examples that must stay literal.

Raw HTML links (`<a href="../...">`) are not rewritten; only markdown inline and reference-style
`../` links are.

**HTML comments are not treated as code.** A complete `[text](../path)` link or `[ref]: ../path`
definition inside `<!-- ... -->` is rewritten like any other link. Use a fenced or inline code
span to keep an example literal.

**Images** are intentionally not rewritten. Inline images (`![alt](../path)`), including alt text
with nested or escaped `]` characters, and image reference definitions (`![alt][ref]` with
`[ref]: ../path`) are left unchanged because forge blob/tree URLs are HTML pages, not raw image
assets — rewriting them would break `<img>` rendering in the built site. If a reference label is
used by both a normal link and an image, the definition is skipped so the image keeps working (the
normal link usage is left unrevised).

MkDocs **virtual pages** (generated content with no markdown file on disk) are left unchanged —
the plugin needs `page.file.abs_src_path` to resolve `../` paths from the page location.

## Forge detection

URLs are built for GitHub, GitLab, Bitbucket, Gitea/Forgejo, and Azure DevOps. Public hosts and
common self-hosted patterns are autodetected; an instance on an unrelated custom domain needs an
explicit [`forge`](configuration.md#options) setting, otherwise its links are left unchanged. See
[Forges](forges.md) (including [unsupported forges](forges.md#unsupported-forges)).

## Line anchors

Canonical line fragments in links (`#L10`, `#L10-L20`) are translated to each forge's syntax when
links are rewritten (GitHub/Gitea keep `#L` form, GitLab uses `#L10-20`, Bitbucket uses
`#lines-10:20`). Non-line fragments (`#section`) pass through unchanged. Azure DevOps view URLs do
not support hash-based line anchors; line fragments are omitted for that forge.

## Git ref and historical links

Every rewritten `../` link uses the same git ref for the build, from [`pin`](configuration.md#options)
and [`branch`](configuration.md#options): a branch or tag name when `pin: branch`, the current
commit SHA when `pin: commit`, or an exact tag at `HEAD` when `pin: tag`. When `pin: commit` or
`pin: tag` cannot be resolved (git unavailable, not a repository, or `HEAD` not on an exact tag),
the plugin falls back to the resolved branch and emits a **warning** at build time. There is no
per-link ref override.

### Hardcoded tag names

You can set an explicit tag name with `pin: branch` and `branch: v1.2.3` when you are not building
from that tag checkout. That always treats the value as a **branch** ref in URL building — the
plugin does not infer tag kind from the string.

On **GitHub, GitLab, and Bitbucket Cloud**, branch and tag names often share the same URL path
shape, so this recipe may still work. On **Gitea/Forgejo/Codeberg** and **Azure DevOps**, branch
and tag URLs differ (`/src/branch/…` vs `/src/tag/…`, or `version=GB…` vs `version=GT…`), so
hardcoded tag names via `branch:` produce **wrong links** on those forges.

For release docs on Gitea or Azure, check out the release tag and use [`pin: tag`](recipes.md#pin-tag).
For a single historical link, use a full forge blob URL in markdown (it passes through unchanged).
See [Pin modes and URL shape](forges.md#pin-modes-and-url-shape).

## Branch names from edit_uri

When plugin `branch` and `extra.git_branch` are unset, the branch name is parsed from `edit_uri`
by taking the **first path segment** after `edit/` or `blob/`. Branch names that contain `/`
(for example `feature/my-branch` in `edit/feature/my-branch/docs/`) are truncated to the first
segment only. This truncation is **silent** — no build-time warning is emitted, because a
multi-segment `edit_uri` is indistinguishable from a nested docs directory (for example
`edit/main/packages/app/docs/`) without knowing the repository layout. Set
[`branch`](configuration.md#options) or `extra.git_branch` explicitly for slash-containing branch
names so forge URLs use the full branch.

## Symlinks

Forge URLs use the **lexical** path written in the markdown (the symlink name), not the symlink
target path, while still validating that the resolved target exists inside the repository.

To point at a **specific** commit or tag for one link — for example code as it existed in an older
release — use a full forge blob URL in the markdown. Absolute URLs are left unchanged by the plugin
and work in the built site as written.

## Existing targets only

A complete inline `[text](../path)` link or `[ref]: ../path` definition is only rewritten when its target resolves to a file or directory that **exists in
the working tree at build time** inside the repository. The plugin does not run `git` to check
whether a path existed at the commit, tag, or branch embedded in the forge URL;
[`pin: commit`](configuration.md#options) and [`pin: tag`](configuration.md#options) only set that
ref in the link (Gitea/Codeberg use `/src/tag/…` for tags; Azure DevOps uses `version=GT…`).
Build from the checkout you want reflected (for example a release tag) so on-disk paths match the
URLs you publish. Directory targets rewrite to forge tree URLs with or without a trailing slash
in the markdown (`../scripts` and `../scripts/` are equivalent when `scripts` is a directory). Missing
targets are left unchanged; by default a warning is emitted (which
fails `mkdocs build --strict`). Set [`warn_on_missing: false`](configuration.md#options) to silence
it. Targets that resolve outside the repository are never reported.
