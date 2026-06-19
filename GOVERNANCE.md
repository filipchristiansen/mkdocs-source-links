# Governance

mkdocs-source-links uses a **maintainer-led** governance model appropriate for a
small open-source library.

## Decision-making

| Area | How decisions are made |
| ---- | ---------------------- |
| Day-to-day code changes | Pull requests reviewed by a maintainer; merged when CI passes and the change aligns with project scope |
| Releases | Listed maintainers cut semver releases per [CONTRIBUTING.md](CONTRIBUTING.md) |
| Security | Coordinated disclosure per [SECURITY.md](SECURITY.md); maintainers decide fix timing and advisory publication |
| Dependencies | Dependabot PRs reviewed by maintainers; Critical/High CVEs block merge per SECURITY.md |
| Escalated access | Documented vetting process in [MAINTAINERS.md](MAINTAINERS.md#escalated-permissions-policy); requires merged PR before grants |
| Scope and roadmap | [ROADMAP.md](ROADMAP.md) states 12-month intent; significant scope changes discussed in GitHub Issues before large PRs |

The project owner and listed maintainers make final decisions when consensus is
not reached. Disputes are resolved through good-faith discussion in the PR or
issue; unresolved technical disagreements defer to maintainer judgment.

## Roles

Roles, responsibilities, and who holds them are documented in
[MAINTAINERS.md](MAINTAINERS.md#roles-and-responsibilities).

## Contribution and conduct

Contributors follow [CONTRIBUTING.md](CONTRIBUTING.md). Community behavior is
governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Changes to governance

Updates to this file, [MAINTAINERS.md](MAINTAINERS.md), or [ROADMAP.md](ROADMAP.md)
require a pull request reviewed and merged by a maintainer, same as code changes.
