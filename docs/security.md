# Security

How to verify release integrity, author identity, and obtain the software bill of materials (SBOM).

For vulnerability reporting and supported versions, see
[SECURITY.md](../SECURITY.md).

## Release assets

Each GitHub Release (for example [v0.4.0](https://github.com/filipchristiansen/mkdocs-source-links/releases/tag/v0.4.0))
includes:

| Asset | Purpose |
| ----- | ------- |
| `mkdocs_source_links-X.Y.Z-py3-none-any.whl` | Python wheel |
| `mkdocs_source_links-X.Y.Z.tar.gz` | Source distribution |
| `mkdocs-source-links.intoto.jsonl` | SLSA Level 3 provenance |
| `mkdocs-source-links-X.Y.Z.cdx.json` | CycloneDX SBOM (from the matching release onward) |

Download assets from the release page or with:

```bash
gh release download v0.4.0 -R filipchristiansen/mkdocs-source-links
```

## Verify integrity and authenticity

Install [slsa-verifier](https://github.com/slsa-framework/slsa-verifier#installation) (v2.7+).

From the directory containing the downloaded files:

```bash
slsa-verifier verify-artifact \
  --provenance-path mkdocs-source-links.intoto.jsonl \
  --source-uri github.com/filipchristiansen/mkdocs-source-links \
  --source-tag v0.4.0 \
  mkdocs_source_links-0.4.0-py3-none-any.whl mkdocs_source_links-0.4.0.tar.gz
```

**Expected output:** verification succeeds (for example `PASSED: Verified signature on` followed by
artifact confirmation). Any failure indicates the artifacts do not match the signed provenance for
that tag.

## Verify release author identity

Release tags must be **signed annotated tags** verified by GitHub before publish.

```bash
# Expect "tag" (not "commit")
gh api repos/filipchristiansen/mkdocs-source-links/git/ref/tags/v0.4.0 --jq '.object.type'

# Expect verified == true
SHA=$(gh api repos/filipchristiansen/mkdocs-source-links/git/ref/tags/v0.4.0 --jq '.object.sha')
gh api "repos/filipchristiansen/mkdocs-source-links/git/tags/${SHA}" \
  --jq '{verified: .verification.verified, reason: .verification.reason}'
```

**Expected output:** `"verified": true` with a reason such as `valid` or `valid_but_inaccessible`.

SLSA provenance additionally records:

- **Builder:** GitHub Actions workflow via `slsa-framework/slsa-github-generator`
- **Source:** `github.com/filipchristiansen/mkdocs-source-links` at the matching `vX.Y.Z` tag

Inspect the provenance file:

```bash
head -c 2000 mkdocs-source-links.intoto.jsonl | python3 -m json.tool
```

Look for `builder.id` pointing at the GitHub Actions builder and `materials` referencing the
repository and tag.

## Software bill of materials

Each release attaches a CycloneDX JSON SBOM (`mkdocs-source-links-X.Y.Z.cdx.json`) listing **runtime**
dependencies from `uv.lock` at build time. Use it to inspect pinned packages shipped with the
released wheel/sdist.

```bash
python3 -m json.tool mkdocs-source-links-0.4.0.cdx.json | head
```

The SBOM is also listed as a release asset on GitHub alongside the wheel, sdist, and provenance.
