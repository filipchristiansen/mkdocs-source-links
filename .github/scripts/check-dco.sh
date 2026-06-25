#!/usr/bin/env bash
# Require a Developer Certificate of Origin sign-off on every non-merge commit in a pull request
# (OpenSSF Security Baseline OSPS-LE-01.01). The Signed-off-by trailer must match the commit author.
#
# Required environment:
#   BASE_SHA — pull request base commit (e.g. github.event.pull_request.base.sha)
#   HEAD_SHA — pull request head commit (e.g. github.event.pull_request.head.sha)

set -euo pipefail

: "${BASE_SHA:?BASE_SHA is required (pull request base commit)}"
: "${HEAD_SHA:?HEAD_SHA is required (pull request head commit)}"

missing=0
while IFS= read -r sha; do
  [ -n "$sha" ] || continue
  author="$(git show -s --format='%an <%ae>' "$sha")"
  # Bots (e.g. dependabot[bot]) cannot satisfy DCO: their sign-off email
  # (support@github.com) never matches their author noreply address. Skip them.
  case "$author" in
    *"[bot]@users.noreply.github.com>") continue ;;
  esac
  if git show -s --format='%(trailers:key=Signed-off-by,valueonly)' "$sha" | grep -qixF "$author"; then
    continue
  fi
  missing=1
  echo "::error::Missing or mismatched Signed-off-by (expected '${author}') on commit: $(git show -s --format='%h %s' "$sha")"
done < <(git rev-list --no-merges "${BASE_SHA}..${HEAD_SHA}")

if [ "$missing" -ne 0 ]; then
  echo "All commits must carry a Developer Certificate of Origin sign-off."
  echo "Add one with 'git commit -s', or fix existing commits with 'git rebase --signoff ${BASE_SHA}'."
  exit 1
fi

echo "All commits are signed off."
