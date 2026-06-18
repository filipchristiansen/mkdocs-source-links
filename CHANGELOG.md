# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Set `GH_TOKEN` in the publish workflow so signed-tag verification works in GitHub Actions.

## [0.3.3] - 2026-06-18

### Changed

- Attach SLSA provenance (`.intoto.jsonl`) and distribution archives to GitHub releases from the
  publish workflow.

## [0.3.2] - 2026-06-18

### Fixed

- Use Gitea `/src/commit/` URLs when `pin: commit` is enabled.
- Tighten forge hostname autodetection heuristics for self-hosted forges.
- Strip a trailing `.git` suffix from `repo_url` when building forge URLs.
- Always initialize `_view_ref` in `on_config` so partial config does not leave the plugin in a
  broken state.
- Parse GitLab-style `edit_uri` branch segments when resolving the documentation branch.

### Changed

- Add OpenSSF Best Practices (Metal Passing), Baseline Level 1, and Scorecard badges to the README
  and documentation site; run OpenSSF Scorecard analysis with SARIF upload to Code Scanning.
- Document a 14-day initial security response SLA and explicit security contacts in SECURITY.md.
- Create signed release tags (`git tag -s`); the publish workflow rejects unsigned or unverified tags
  before PyPI upload.
- Add MIT, CI, and Python badges to the docs home page; exclude MkDocs snippet files from standalone
  page builds.

## [0.3.1] - 2026-06-18

### Fixed

- Rewrite angle-bracket links whose destination contains spaces (`](<../my file.py>)`); the path is
  percent-encoded in the resulting forge URL.

### Changed

- Run the CI test suite on Windows and macOS (newest supported Python) in addition to the Linux
  Python matrix, to guard cross-platform path handling.
- Add a two-step release helper (`make release-prep` / `make release-tag`) that bumps the version,
  rolls the hand-written `[Unreleased]` changelog section into a dated release, and opens the
  release PR, tags, and publishes — without ever generating release notes.
- Lint and format TOML via pre-commit (`check-toml` plus the `taplo-format` formatter), keeping
  `pyproject.toml` consistently styled.

## [0.3.0] - 2026-06-17

### Added

- `pin` config option (`branch` or `commit`, default `branch`) to embed the current commit SHA in
  forge URLs instead of a branch name. Azure DevOps uses `version=GC<sha>` for commits.
- Line-anchor translation: canonical `#L10` / `#L10-L20` fragments in rewritten links are converted
  to each forge's line-reference syntax. Non-line fragments pass through; Azure line anchors are
  omitted.
- `enabled` config option (default `true`) to turn link rewriting off; supports `!ENV` for
  per-environment toggling (e.g. during `mkdocs serve`).
- `warn_on_missing` config option (default `true`) to warn when a `](../path)` link target does not
  exist in the repository. Warnings count toward `mkdocs build --strict`.

### Changed

- Add the `Framework :: MkDocs` trove classifier for PyPI discoverability.

## [0.2.0] - 2026-06-17

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

[Unreleased]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.3.3...HEAD
[0.3.3]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/filipchristiansen/mkdocs-source-links/releases/tag/v0.1.0
