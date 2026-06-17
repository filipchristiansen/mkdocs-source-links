# Limitations

Known limitations of the current release. Several are tracked on the
[issue tracker](https://github.com/filipchristiansen/mkdocs-source-links/issues).

## Link syntax

Inline links are matched, including titled links (`](../x "title")`) and angle-bracket
destinations (`](<../x>)`); the title and fragment are preserved. Reference-style links
(`[x][ref]` with a separate `[ref]: ../path` definition) are not yet rewritten.

Rewriting is text-level (a regex over the page markdown), but fenced code blocks and inline code
spans are detected and skipped, so a literal `](../path)` shown as an example is left unchanged.

## Forge detection

URLs are built for GitHub, GitLab, Bitbucket, Gitea/Forgejo, and Azure DevOps. Public hosts and
common self-hosted patterns are autodetected; an instance on an unrelated custom domain needs an
explicit [`forge`](configuration.md#options) setting, otherwise its links are left unchanged. See
[Forges](forges.md).

## Existing targets only

A `../` link is only rewritten when its target resolves to a file or directory that exists on disk
inside the repository. Missing targets are left unchanged (no warning is emitted).
