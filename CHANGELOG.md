# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] - 2026-06-20

### Added

- `log_rewrites` config option (`false`, `summary`, `verbose`) for opt-in rewrite statistics at INFO level.

### Documentation

- Sync stale release-verification examples; document `make ci` steps, commit/tag pin URL shapes per forge, indented-code limitation, and `on_page_markdown` rewrite stage wording.

## [0.5.2] - 2026-06-19

### Fixed

- CommonMark fenced code blocks now close when the closing fence uses **more** markers than the opener (for example ` ``` ` opened, ` ```` ` closed); reference definitions after such blocks are rewritten correctly.
- Symlink targets: forge URLs use the path written in the markdown (the symlink name), not the resolved target path.

### Changed

- `pin: commit` and `pin: tag` emit a build warning when git lookup fails and the resolved branch is used instead; git is no longer invoked when `repo_url` is unset.
- `repo_view_url()` raises `ValueError` for an unsupported explicit `forge` name instead of `KeyError`.

### Documentation

- Document slash-containing branch names from `edit_uri`, git pin fallback warnings, and symlink URL behavior in limitations and branch resolution docs.

## [0.5.1] - 2026-06-19

### Fixed

- Image links (`![alt](../path)` and image reference definitions) are no longer rewritten to forge blob URLs, which broke `<img>` rendering in built sites.
- Gitea/Codeberg tag URLs use `/src/tag/<tag>/…` when `pin: tag` resolves an exact tag (not `/src/branch/…`).
- Azure DevOps tag URLs use `version=GT…` when `pin: tag`; query parameters are encoded without double-encoding paths.
- Bitbucket Cloud autodetection is limited to `bitbucket.org`; self-hosted hostnames containing `bitbucket` are no longer misdetected as Cloud.

### Changed

- Plugin and rewrite docstrings describe multi-forge URLs and tag ref kind consistently with user docs.

## [0.5.0] - 2026-06-19

### Added

- `CODE_OF_CONDUCT.md` (Contributor Covenant v2.1), `GOVERNANCE.md`, and `ROADMAP.md`.
- Continuity-of-access plan and 2FA policy in `MAINTAINERS.md`.
- `DCO1.1.md` and `Signed-off-by` requirement in `CONTRIBUTING.md`.
- Regression test for unrecognized `edit_uri` branch fallback in `branch.py`.
- Documentation site pages for roadmap, support, governance, and code of conduct (snippet includes from root files).
- Cross-links in shared governance docs use docs-site URLs for published pages and GitHub blob URLs for root-only files.
- Reference-style link definitions (`[ref]: ../path`) rewrite to forge URLs; `[text][ref]` usages resolve at build time ([#28](https://github.com/filipchristiansen/mkdocs-source-links/issues/28)).
- `pin: tag` uses an exact tag at `HEAD` in forge URLs when building from a release tag checkout.
- Configuration recipes guide (`docs/recipes.md`) with prerequisites, link conventions, worked
  `mkdocs.yml` examples (monorepo, self-hosted, release builds), and a configuration decision tree.
- `make docs-serve` for local documentation preview (`strict` build, then `mkdocs serve`).

### Changed

- PyPI development status graduated from Beta to Production/Stable.
- Documentation site navigation grouped into Guide, Configuration, Reference, Project, and Community sections.
- README and root governance docs link to docs-site pages where published; root-only files (`MAINTAINERS.md`, `SECURITY.md`) link to GitHub blob URLs.
- `MAINTAINERS.md` documents branch protection expectations and private Code of Conduct reporting.
- `make test` and CI use branch coverage.
- Publish workflow verifies tag↔`pyproject.toml` version and runs `mkdocs build --strict` before PyPI upload.
- Removed duplicate `repo_view_url` tests from `test_rewrite.py` (`test_urls.py` remains the spec).

## [0.4.1] - 2026-06-19

### Added

- `MAINTAINERS.md` (maintainer roles, sensitive-resource access, escalated-permissions policy).
- `SUPPORT.md` (support scope and duration per release).
- Security assessment, secrets policy, and dependency vulnerability policy in `SECURITY.md`.
- Published [release verification docs](https://filipchristiansen.github.io/mkdocs-source-links/security/)
  (SLSA provenance, signed-tag checks, SBOM).
- `pip-audit` dependency scanning in CI and `make audit` (included in `make ci`).
- CycloneDX SBOM (`mkdocs-source-links-X.Y.Z.cdx.json`) on GitHub releases.
- Dependencies section in `CONTRIBUTING.md`.

### Changed

- Publish workflow steps moved to `.github/scripts/`; tag verification and release creation extracted.
- `CONTRIBUTING.md` documents `make audit` and the expanded `make ci` suite.
- README links to governance, support, and release verification docs.

## [0.4.0] - 2026-06-18

### Added

- SLSA Level 3 provenance (`mkdocs-source-links.intoto.jsonl`) on GitHub releases.
- Post-release `slsa-verifier` check in the publish workflow.

### Changed

- Publish workflow verifies maintainer signed tags before PyPI upload.
- GitHub releases created atomically with provenance and distribution archives (immutable-release compatible).
- Release notes sourced from CHANGELOG.

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

[Unreleased]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.5.2...v0.6.0
[0.5.2]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.4.1...v0.5.0
[0.4.1]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/filipchristiansen/mkdocs-source-links/releases/tag/v0.1.0
