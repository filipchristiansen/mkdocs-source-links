# Maintainers

## Members with access to sensitive resources

| Member | GitHub | Sensitive access |
| ------ | ------ | ---------------- |
| Filip Christiansen | [@filipchristiansen](https://github.com/filipchristiansen) | Repository admin; `pypi` GitHub Environment (OIDC publish to PyPI); release signing key (GPG/SSH) |

This is a single-maintainer project. No other accounts have admin, environment, or signing access.

## Roles and responsibilities

### Maintainer

- Merge pull requests after review and passing CI
- Cut releases (`make release-prep`, signed `make release-tag`)
- Triage issues and security reports
- Respond to private vulnerability reports (see [SECURITY.md](SECURITY.md))
- Manage Dependabot and dependency update PRs

### Contributor

Anyone may open issues or pull requests. Contributors follow [CONTRIBUTING.md](CONTRIBUTING.md):
tests at 100% coverage, pre-commit/CI clean, conventional PR titles. Maintainers review and merge.

### Security contact

The maintainer listed above receives private vulnerability reports via GitHub Security Advisories
and coordinates fixes and disclosure per [SECURITY.md](SECURITY.md).

## Escalated permissions policy

Contributors do **not** receive escalated access to sensitive resources by default. Sensitive
resources include repository admin rights, the `pypi` GitHub Environment (OIDC publish to PyPI),
GitHub Actions secrets, and release signing keys.

To grant escalated permissions to a new maintainer:

1. **Vet** the candidate (established trust, review of prior contributions, alignment with project
   goals).
2. **Document** the grant by adding them to the maintainers table above with their sensitive access.
3. **Merge** a pull request updating this file; do not grant access before the PR is merged.

Until a contributor is listed in the maintainers table, only the current maintainer holds sensitive
access. Contributors may open pull requests and issues under the [CONTRIBUTING.md](CONTRIBUTING.md)
workflow without elevated permissions.
