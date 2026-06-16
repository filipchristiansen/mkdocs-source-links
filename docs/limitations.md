# Limitations

Known limitations of the current release. Several are tracked on the
[issue tracker](https://github.com/filipchristiansen/mkdocs-source-links/issues).

## Code blocks and inline code

Rewriting is text-level (a regex over the page markdown), so a literal `](../path)` shown inside a
fenced code block or inline code span is also rewritten. If you document link syntax verbatim, this
can be surprising. Tracked in
[issue #2](https://github.com/filipchristiansen/mkdocs-source-links/issues/2).

## Link syntax

Only inline links of the form `](../path)` are matched. Reference-style links (`[x][ref]`), links
with titles (`](../x "title")`), and angle-bracket links (`](<../x>)`) are not currently rewritten.

## Forge detection

URLs are built for GitHub, GitLab, Bitbucket, Gitea/Forgejo, and Azure DevOps. Public hosts and
common self-hosted patterns are autodetected; an instance on an unrelated custom domain needs an
explicit [`forge`](configuration.md#options) setting, otherwise its links are left unchanged. See
[Forges](forges.md).

## Existing targets only

A `../` link is only rewritten when its target resolves to a file or directory that exists on disk
inside the repository. Missing targets are left unchanged (no warning is emitted).
