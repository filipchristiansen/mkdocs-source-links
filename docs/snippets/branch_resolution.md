<!-- markdownlint-disable-file MD041 -->

1. Plugin `branch:` config
2. `extra.git_branch` in `mkdocs.yml`
3. Parsed from `edit_uri` (`edit/<branch>/...` or `blob/<branch>/...`)
4. Fallback: `main`

If your default branch is not `main`, set `edit_uri`, `extra.git_branch`, or `source-links.branch`
so links point at the right ref.
