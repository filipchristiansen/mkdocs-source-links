# Contributing

Thanks for your interest in improving mkdocs-source-links!

## Development setup

This project uses [uv](https://docs.astral.sh/uv), [pre-commit](https://pre-commit.com), and a `Makefile`.

```bash
make install   # install Python 3.10, sync all groups, set up pre-commit hooks
```

When editing [`.github/scripts/`](.github/scripts/): install [ShellCheck](https://www.shellcheck.net) locally — `brew install shellcheck` (macOS) or `sudo apt install shellcheck` (Linux). CI installs it automatically.

## Workflow

1. Create a branch with a conventional prefix (`feat/`, `fix/`, `chore/`, `docs/`, `refactor/`, `test/`).
2. Make your change and add tests. The suite must stay at 100% coverage.
3. Run the full pre-PR suite locally:

   ```bash
   make ci      # lint (pre-commit) + tests with coverage
   ```

   Individual targets are also available:

   ```bash
   make lint    # pre-commit hooks (ruff, mypy, pydoclint, pylint, markdownlint, ...)
   make test    # pytest with coverage
   ```

4. Open a pull request targeting `main` with a conventional title (for example `fix: ...`).
   CI runs the same lint and test suite across Python 3.10-3.13.

## Coding standards

- Code is linted and formatted with [ruff](https://docs.astral.sh/ruff), type-checked with
  [mypy](https://mypy-lang.org), and checked with [pylint](https://www.pylint.org) and pydoclint.
- Public functions use NumPy-style docstrings.
- These are all enforced by pre-commit and CI; running `make lint` before pushing avoids surprises.

## Static analysis

Before merge, CI runs pre-commit hooks including ruff (with bandit security rules), mypy, pylint,
and pydoclint. See `Makefile`, `.pre-commit-config.yaml`, and `.github/workflows/ci.yml` in the
repository.

## Releases

Releases are cut by maintainers. First, curate the `## [Unreleased]` section of `CHANGELOG.md` by
hand (the tooling never generates release notes). Then:

1. `make release-prep VERSION=X.Y.Z` — bumps `version` in `pyproject.toml`, rolls `[Unreleased]`
   into a dated `## [X.Y.Z]` section with updated compare links, runs `make ci`, and opens the
   release PR.
2. After the PR is merged, `make release-tag VERSION=X.Y.Z` — creates a **signed** annotated tag
   `vX.Y.Z` and pushes it. Optionally run `make verify-tag TAG=vX.Y.Z` first to confirm the tag
   is verified on GitHub. The publish workflow verifies the tag signature, builds and uploads to
   PyPI, and creates the GitHub release with SLSA provenance (`.intoto.jsonl`) and distribution
   archives in a single `gh release create` (required for **immutable releases** — do not enable
   SLSA `upload-assets`, which pre-creates an empty release and breaks asset upload). Release notes
   on GitHub are taken from the matching `CHANGELOG.md` section; a post-release job verifies
   provenance with `slsa-verifier`.

### Signed tags and commits

`main` requires signed commits; release tags are created with `git tag -s`. The publish workflow
rejects unsigned or unverified tags before PyPI upload. Configure commit/tag signing locally (GPG
or SSH) and add the public key to your GitHub account so tags and merges show as **Verified**. See
GitHub’s
[commit signature verification](https://docs.github.com/en/authentication/managing-commit-signature-verification)
guide.
