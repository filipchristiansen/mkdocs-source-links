# Forges

The plugin builds forge view URLs based on `repo_url`. Hosts that are not yet supported are left
unchanged (links are passed through verbatim).

## Support matrix

| Forge | Status |
| ----- | ------ |
| GitHub (github.com) | Supported |
| GitHub Enterprise / self-hosted | Planned |
| GitLab | Planned |
| Bitbucket Cloud | Planned |
| Gitea / Forgejo / Codeberg | Planned |
| Azure DevOps | Planned |

!!! info "v1 scope"
    The current release supports GitHub only. Multi-forge support is on the roadmap; see the
    project [issues](https://github.com/filipchristiansen/mkdocs-source-links/issues) for progress.
