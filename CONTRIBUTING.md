# Contributing

Thanks for your interest in improving mkdocs-source-links!

## Development setup

This project uses [uv](https://docs.astral.sh/uv), [pre-commit](https://pre-commit.com), and a `Makefile`.

```bash
make install   # install Python 3.10, sync all groups, set up pre-commit hooks
```

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

## Releases

Releases are cut by maintainers. First, curate the `## [Unreleased]` section of `CHANGELOG.md` by
hand (the tooling never generates release notes). Then:

1. `make release-prep VERSION=X.Y.Z` — bumps `version` in `pyproject.toml`, rolls `[Unreleased]`
   into a dated `## [X.Y.Z]` section with updated compare links, runs `make ci`, and opens the
   release PR.
2. After the PR is merged, `make release-tag VERSION=X.Y.Z` — tags `vX.Y.Z` and creates the GitHub
   release. Pushing the tag triggers the publish workflow, which builds and uploads to PyPI.
