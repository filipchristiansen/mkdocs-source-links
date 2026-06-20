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
- Respond to private vulnerability reports (see [Security policy](https://github.com/filipchristiansen/mkdocs-source-links/blob/main/SECURITY.md))
- Manage Dependabot and dependency update PRs

### Contributor

Anyone may open issues or pull requests. Contributors follow [Contributing](https://filipchristiansen.github.io/mkdocs-source-links/contributing/):
tests at 100% coverage, pre-commit/CI clean, conventional PR titles. Maintainers review and merge.

### Security contact

The maintainer listed above receives private vulnerability reports via GitHub Security Advisories
and coordinates fixes and disclosure per [Security policy](https://github.com/filipchristiansen/mkdocs-source-links/blob/main/SECURITY.md). The same maintainer receives
private [Code of conduct](https://filipchristiansen.github.io/mkdocs-source-links/code-of-conduct/) reports; do not use public issues for either.

## Escalated permissions policy

Contributors do **not** receive escalated access to sensitive resources by default. Sensitive
resources include repository admin rights, the `pypi` GitHub Environment (OIDC publish to PyPI),
GitHub Actions secrets, and release signing keys.

To grant escalated permissions to a new maintainer:

1. **Vet** the candidate (established trust, review of prior contributions, alignment with project
   goals).
2. **Require 2FA** — the candidate MUST enable GitHub two-factor authentication using TOTP
   (authenticator app) or a security key before receiving write or admin access. SMS-only 2FA
   is discouraged.
3. **Document** the grant by adding them to the maintainers table above with their sensitive access.
4. **Merge** a pull request updating this file; do not grant access before the PR is merged.

Until a contributor is listed in the maintainers table, only the current maintainer holds sensitive
access. Contributors may open pull requests and issues under the [Contributing](https://filipchristiansen.github.io/mkdocs-source-links/contributing/)
workflow without elevated permissions.

## Continuity of access

If the primary maintainer is unavailable, the project MUST continue within **one week** with
minimal interruption to issue triage, pull request review, and releases.

### Succession and backup

| Step | Action | Target time |
| ---- | ------ | ----------- |
| 1 | A trusted contributor opens a public issue or contacts the maintainer via GitHub | Day 0 |
| 2 | Follow [escalated permissions policy](#escalated-permissions-policy) to onboard a backup maintainer | Within 7 days |
| 3 | Backup maintainer receives repository admin and `pypi` environment access (OIDC; no long-lived PyPI tokens) | Within 7 days |
| 4 | New maintainer registers release signing key on GitHub; old keys rotated if compromised | Within 7 days |
| 5 | Resume issue triage, PR merges, and releases | Within 7 days |

### Account and key transfer

- **GitHub repository:** Grant admin to the backup maintainer via GitHub settings or transfer to
  a GitHub organization owned by multiple people.
- **PyPI publishing:** Add the backup maintainer as a trusted publisher admin on the `pypi`
  GitHub Environment; OIDC trusted publishing requires no token handoff.
- **Release signing keys:** Generate a new GPG or SSH signing key for the incoming maintainer;
  register the public key on GitHub. Retire lost keys per [Security policy](https://github.com/filipchristiansen/mkdocs-source-links/blob/main/SECURITY.md#secrets-and-credentials).
- **GitHub Actions secrets:** Repository admins rotate `CODECOV_TOKEN` and `SCORECARD_TOKEN` if
  the outgoing maintainer had access.

### Interim operation (no maintainer available)

The MIT-licensed source remains public on GitHub. Community members may fork, open pull requests,
and install from PyPI releases already published. Security reports should use
[private vulnerability reporting](https://github.com/filipchristiansen/mkdocs-source-links/security/advisories/new)
until a maintainer responds.

## Branch protection expectations

Maintainers configure `main` with:

- Required signed commits
- Required status checks (lint, test, audit, docs)
- At least one approving pull request review
- Code owner review (see [`.github/CODEOWNERS`](../.github/CODEOWNERS))
- **Require approval from someone other than the author** when a co-maintainer is listed

See [Contributing](https://filipchristiansen.github.io/mkdocs-source-links/contributing/) and [Governance](https://filipchristiansen.github.io/mkdocs-source-links/governance/).
