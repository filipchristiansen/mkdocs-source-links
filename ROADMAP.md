# Roadmap

Intent for the **next 12 months** (reviewed quarterly). For known gaps see
[limitations](https://filipchristiansen.github.io/mkdocs-source-links/limitations/);
for concrete work see the [issue tracker](https://github.com/filipchristiansen/mkdocs-source-links/issues).

## Next 12 months

- **Maintain compatibility** with MkDocs 1.x and Python 3.10+.
- **Fix bugs** and edge cases reported via GitHub Issues.
- **Keep docs and tests current** with each release.
- **Improve forge handling** on a best-effort basis when users report self-hosted or autodetection gaps.
- **Consider small features** only when there is clear demand (for example broader `../` link patterns in monorepos).

No major rewrite or version 1.0 feature push is planned unless adoption and feedback justify it.

## Non-goals (next 12 months)

- Running as a network service or HTTP proxy at build or runtime
- Internationalizing build-time log messages
- Rewriting links that are not parent-directory (`../`) paths (unless explicitly added via issue consensus)
- Supporting non-git version control systems
- Commercial support or paid SLAs
- Chasing OpenSSF Gold or Baseline Level 3 unless the project gains sustained adoption and contributors

## How to influence the roadmap

Open a [feature request](https://github.com/filipchristiansen/mkdocs-source-links/issues/new?template=feature_request.md)
or comment on an existing issue. Maintainers update this file when priorities shift.
