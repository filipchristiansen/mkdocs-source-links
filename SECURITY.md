# Security Policy

## Supported versions

Only the latest released version of mkdocs-source-links receives security fixes.

## Security contacts

See [MAINTAINERS.md](MAINTAINERS.md) for who handles security reports. Report vulnerabilities
privately via GitHub's
[private vulnerability reporting](https://github.com/filipchristiansen/mkdocs-source-links/security/advisories/new).
Do not open a public issue for security problems.

## Reporting a vulnerability

Include a description of the issue, affected versions, and steps to reproduce if possible.

You can expect an **initial response within 14 days**. Once the issue is confirmed, a fix or
mitigation will be released in a new version.

## Security assessment

mkdocs-source-links is a **build-time MkDocs plugin**. It rewrites markdown links in documentation
pages during `mkdocs build`; it does not serve HTTP, store secrets, or make network requests at
runtime.

### Scope and trust boundaries

| Actor | Trust | Interaction |
| ----- | ----- | ----------- |
| Documentation author | Trusted | Writes markdown and `mkdocs.yml` in the repo |
| MkDocs build | Trusted runner | Invokes the plugin on each page |
| Plugin | This software | Reads local repo paths and `mkdocs.yml`; emits rewritten markdown URLs |
| Git forge (GitHub, etc.) | External | Receives URLs in built HTML; not contacted during the build |

The plugin reads the local filesystem (to check link targets exist) and git metadata (branch/SHA).
It does not execute user-supplied code, deserialize untrusted formats, or write outside the build
output.

### Likely threats and mitigations

| Threat | Impact | Mitigation |
| ------ | ------ | ---------- |
| Path handling bugs (incorrect resolution of `../` links) | Broken or misleading forge URLs in docs | Strict path normalization; tests across OSes; missing targets left unchanged with warnings |
| Incorrect URL generation for a forge | Users follow wrong links | Forge-specific URL builders with integration tests; explicit `forge` override |
| Supply-chain compromise (dependency or PyPI package) | Malicious code in plugin | Minimal runtime deps; lockfile + `uv sync --frozen` in CI; Dependabot; SLSA provenance on releases; signed tags |
| Malicious contribution | Backdoor in plugin source | Required PR review, CI (incl. bandit via ruff), signed commits on `main` |

### Residual risks

- The plugin trusts the repository contents and MkDocs configuration it is built with; it cannot
  protect against a compromised docs source tree.
- Built HTML links point at third-party forges; their availability and content are outside this
  project.

## Secrets and credentials

- **Source code:** No secrets, API keys, or credentials are committed to the repository. Do not
  commit `.env` files, tokens, or private keys. Pre-commit hooks include `check-added-large-files`
  and all changes are reviewed before merge.
- **GitHub Actions secrets:** `CODECOV_TOKEN` and `SCORECARD_TOKEN` are stored as encrypted
  repository secrets. Only repository admins (see [MAINTAINERS.md](MAINTAINERS.md)) can read or
  rotate them via GitHub repository settings.
- **PyPI publishing:** Uses OIDC trusted publishing through the `pypi` GitHub Environment. No
  long-lived PyPI API tokens are stored in the repository or in workflow files.
- **Release signing keys:** GPG or SSH keys used for signed commits and annotated release tags are
  held locally by the maintainer. Public keys are registered on GitHub. To rotate, generate a new key,
  register it on GitHub, and retire the old key.
- **Access control:** Escalated access to secrets and environments is limited to listed maintainers
  per [MAINTAINERS.md](MAINTAINERS.md#escalated-permissions-policy).

## Dependency vulnerability policy

This project scans dependencies for known vulnerabilities and tracks updates via Dependabot. See
[CONTRIBUTING.md](CONTRIBUTING.md#dependencies) for how dependencies are declared and updated.

### Remediation threshold

- **Critical / High** known CVEs in the runtime or development lockfile block merge and release.
  Fix or upgrade the affected dependency before merging.
- **Medium / Low** findings are triaged in Dependabot update PRs and addressed on a best-effort
  basis.
- **Licenses:** Dependencies must use OSI-approved licenses compatible with this project's MIT
  license.

### Process

- Every pull request and push to `main` runs `pip-audit` in CI (required status check).
- Dependabot opens weekly PRs for `uv.lock` and GitHub Actions; maintainers review and merge after
  CI passes.
- Before any release, `make release-prep` runs `make ci` (lint, audit, tests, docs). A release tag
  is not cut if the audit step fails.

## CI/CD hardening

GitHub Actions workflows use least-privilege `permissions` (for example `contents: read` on CI).
Release publishing uses a dedicated environment with OIDC to PyPI; no long-lived PyPI tokens are
stored in the repository. The publish workflow accepts only GitHub-verified signed release tags,
uploads distribution archives to the matching GitHub release, and attaches SLSA provenance
(`.intoto.jsonl`) generated by the [SLSA GitHub generator](https://github.com/slsa-framework/slsa-github-generator).

Release verification instructions for consumers are published separately at
<https://filipchristiansen.github.io/mkdocs-source-links/security/> (not in the pipeline config).
