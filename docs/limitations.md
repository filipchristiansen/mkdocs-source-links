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

## Forge detection

URLs are built for GitHub, GitLab, Bitbucket, Gitea/Forgejo, and Azure DevOps. Public hosts and
common self-hosted patterns are autodetected; an instance on an unrelated custom domain needs an
explicit [`forge`](configuration.md#options) setting, otherwise its links are left unchanged. See
[Forges](forges.md).

## Line anchors

Canonical line fragments in links (`#L10`, `#L10-L20`) are translated to each forge's syntax when
links are rewritten (GitHub/Gitea keep `#L` form, GitLab uses `#L10-20`, Bitbucket uses
`#lines-10:20`). Non-line fragments (`#section`) pass through unchanged. Azure DevOps view URLs do
not support hash-based line anchors; line fragments are omitted for that forge.

## Existing targets only

A `../` link is only rewritten when its target resolves to a file or directory that exists on disk
inside the repository. Missing targets are left unchanged; by default a warning is emitted (which
fails `mkdocs build --strict`). Set [`warn_on_missing: false`](configuration.md#options) to silence
it. Targets that resolve outside the repository are never reported.
