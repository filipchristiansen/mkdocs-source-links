#!/usr/bin/env bash
# Create an immutable GitHub release with provenance and distribution archives.
#
# Run from the repository root after checkout, with dist/ and the provenance file present.
#
# Required environment:
#   TAG         — e.g. v0.4.0
#   PROVENANCE  — provenance filename (e.g. mkdocs-source-links.intoto.jsonl)
# Optional:
#   GH_TOKEN    — defaults to gh CLI login / GITHUB_TOKEN in Actions
#   CHANGELOG   — path to changelog (default: CHANGELOG.md)

set -euo pipefail

: "${TAG:?TAG is required (e.g. v0.4.0)}"
: "${PROVENANCE:?PROVENANCE is required (e.g. mkdocs-source-links.intoto.jsonl)}"

CHANGELOG="${CHANGELOG:-CHANGELOG.md}"

if gh release view "$TAG" >/dev/null 2>&1; then
  echo "::error::Release ${TAG} already exists; delete it before re-publishing."
  exit 1
fi

if [ ! -f "$CHANGELOG" ]; then
  echo "::error::Changelog not found at ${CHANGELOG}."
  exit 1
fi

if [ ! -f "$PROVENANCE" ]; then
  echo "::error::Provenance file not found at ${PROVENANCE}."
  exit 1
fi

VERSION="${TAG#v}"
NOTES=$(
  awk -v ver="$VERSION" '
    $0 ~ "^## \\[" ver "\\]" { found=1; next }
    found && /^## \[/ { exit }
    found { print }
  ' "$CHANGELOG"
)
if [ -z "$(echo "$NOTES" | tr -d '[:space:]')" ]; then
  echo "::error::No CHANGELOG section found for ${VERSION}."
  exit 1
fi

COMPARE_LINK=$(
  awk -v ver="$VERSION" '
    $0 ~ "^\\[" ver "\\]: " { print $NF; exit }
  ' "$CHANGELOG"
)
if [ -z "$COMPARE_LINK" ]; then
  echo "::error::No compare link found for ${VERSION} in CHANGELOG.md."
  exit 1
fi

NOTES="${NOTES}

**Full changelog:** ${COMPARE_LINK}"

gh release create "$TAG" \
  "$PROVENANCE" \
  sbom/*.cdx.json \
  dist/*.tar.gz \
  dist/*.whl \
  --title "$TAG" \
  --notes "$NOTES"
