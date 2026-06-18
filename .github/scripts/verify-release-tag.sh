#!/usr/bin/env bash
# Verify that TAG is a cryptographically verified signed annotated tag on GitHub.
#
# Required environment:
#   TAG                 — e.g. v0.4.0
#   GITHUB_REPOSITORY   — e.g. owner/repo
# Optional:
#   GH_TOKEN            — defaults to gh CLI login / GITHUB_TOKEN in Actions

set -euo pipefail

: "${TAG:?TAG is required (e.g. v0.4.0)}"
: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY is required (e.g. owner/repo)}"

TYPE=$(gh api "repos/${GITHUB_REPOSITORY}/git/ref/tags/${TAG}" --jq '.object.type')
if [ "$TYPE" != "tag" ]; then
  echo "::error::Release tag ${TAG} must be a signed annotated tag (git tag -s), not a lightweight tag."
  exit 1
fi

SHA=$(gh api "repos/${GITHUB_REPOSITORY}/git/ref/tags/${TAG}" --jq '.object.sha')
VERIFIED=$(gh api "repos/${GITHUB_REPOSITORY}/git/tags/${SHA}" --jq '.verification.verified')
REASON=$(gh api "repos/${GITHUB_REPOSITORY}/git/tags/${SHA}" --jq '.verification.reason')
if [ "$VERIFIED" != "true" ]; then
  echo "::error::Release tag ${TAG} is not cryptographically verified (reason: ${REASON}). Use git tag -s with a key registered on GitHub."
  exit 1
fi

echo "Tag ${TAG} is verified (${REASON})."
