# Limitations

Known limitations of the current release. Several are tracked on the
[issue tracker](https://github.com/filipchristiansen/mkdocs-source-links/issues).

## Link syntax

Inline links are matched, including titled links (`](../x "title")`) and angle-bracket
destinations (`](<../x>)`, which may contain spaces); the title and fragment are preserved, and
spaces are percent-encoded in the resulting URL. Reference-style definitions (`[ref]: ../path`,
optional title) are rewritten the same way; usages such as `[text][ref]` pick up the forge URL
when the markdown processor resolves the reference.

Rewriting is text-level (a regex over the page markdown), but fenced code blocks and inline code
spans are detected and skipped, so a literal `](../path)` or `[ref]: ../path` shown as an example
is left unchanged.

Raw HTML links (`<a href="../...">`) are not rewritten; only markdown inline and reference-style
`../` links are.

**Images** are intentionally not rewritten. Inline images (`![alt](../path)`) and image reference
definitions (`![alt][ref]` with `[ref]: ../path`) are left unchanged because forge blob/tree URLs
are HTML pages, not raw image assets — rewriting them would break `<img>` rendering in the built
site. If a reference label is used by both a normal link and an image, the definition is skipped
so the image keeps working (the normal link usage is left unrevised).

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
commit SHA when `pin: commit`, or an exact tag at `HEAD` when `pin: tag` (with branch fallback if
`HEAD` is not tagged). There is no per-link ref override.

To point at a **specific** commit or tag for one link — for example code as it existed in an older
release — use a full forge blob URL in the markdown. Absolute URLs are left unchanged by the plugin
and work in the built site as written.

## Existing targets only

A `../` link is only rewritten when its target resolves to a file or directory that **exists in
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
