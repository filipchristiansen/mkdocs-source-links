# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Multi-forge support: GitLab, Bitbucket Cloud, Gitea/Forgejo (incl. Codeberg), and Azure DevOps,
  in addition to GitHub. Public hosts and common self-hosted patterns (e.g. GitHub Enterprise) are
  autodetected.
- `forge` config option to select the forge explicitly for self-hosted instances on custom domains.
- Support titled links (`](../x "title")`) and angle-bracket destinations (`](<../x>)`), preserving
  the title and fragment.
- Documentation site (MkDocs Material) published to GitHub Pages, with an mkdocstrings API reference.
- `py.typed` marker so downstream type checkers consume the bundled type hints (PEP 561).
- `CHANGELOG.md`, `CONTRIBUTING.md`, and `SECURITY.md`.
- GitHub issue and pull request templates.
- Dependabot configuration for GitHub Actions and uv dependencies.

### Fixed

- Do not rewrite `](../path)` links inside fenced code blocks or inline code spans
  ([#2](https://github.com/filipchristiansen/mkdocs-source-links/issues/2)).

### Changed

- Trim the source distribution to the package, tests, and metadata (exclude CI, tooling, and editor/agent configs).
- CI lint now runs the shared pre-commit hooks (single source of truth with local `make lint`).
- Install dependencies from the committed `uv.lock` (`uv sync --frozen`) for reproducible CI.
- Align the publish workflow with the action and Python versions used by CI.

## [0.1.1] - 2026-06-16

### Fixed

- Leave page markdown unchanged when a page has no backing file (`abs_src_path is None`).

### Changed

- Derive `__version__` from installed package metadata instead of hardcoding it.

## [0.1.0] - 2026-06-16

### Added

- Initial release: rewrite `](../path)` markdown links to GitHub `blob`/`tree` URLs in built HTML, leaving source files unchanged.
- Optional `branch` config and branch resolution from `extra.git_branch` / `edit_uri`.

[Unreleased]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/filipchristiansen/mkdocs-source-links/releases/tag/v0.1.0
