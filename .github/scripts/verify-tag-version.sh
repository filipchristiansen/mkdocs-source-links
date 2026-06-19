#!/usr/bin/env bash
# Verify that TAG matches version in pyproject.toml at the checked-out commit.
#
# Required environment:
#   TAG — e.g. v0.4.0

set -euo pipefail

: "${TAG:?TAG is required (e.g. v0.4.0)}"

TAG_VERSION="${TAG#v}"
PYPROJECT_VERSION=$(
  grep -E '^version = ' pyproject.toml | head -1 | sed -E 's/^version = "([^"]+)".*/\1/'
)

if [ -z "$PYPROJECT_VERSION" ]; then
  echo "::error::Could not read version from pyproject.toml."
  exit 1
fi

if [ "$TAG_VERSION" != "$PYPROJECT_VERSION" ]; then
  echo "::error::Tag ${TAG} does not match pyproject.toml version (${PYPROJECT_VERSION})."
  exit 1
fi

echo "Tag ${TAG} matches pyproject.toml version."
