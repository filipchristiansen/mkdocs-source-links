"""Tests for ``.github/scripts/create-github-release.sh``."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(".github/scripts/create-github-release.sh")
_BASH = shutil.which("bash") or "/bin/bash"
_NOTES_FILE = "release-notes.txt"

CHANGELOG = """# Changelog

## [0.6.0] - 2026-06-20

### Added

- Example release note.

[0.6.0]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.5.2...v0.6.0
"""

_GH_STUB_SCRIPT = f"""\
#!/usr/bin/env bash
set -euo pipefail
if [[ "$1" == "release" && "$2" == "view" ]]; then
  exit 1
fi
if [[ "$1" == "release" && "$2" == "create" ]]; then
  while [[ $# -gt 0 ]]; do
    if [[ "$1" == "--notes" ]]; then
      printf '%s' "$2" > {_NOTES_FILE}
      exit 0
    fi
    shift
  done
fi
exit 1
"""


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="create-github-release.sh runs on Linux Publish workflow only",
)
def test_create_github_release_appends_compare_link(tmp_path: Path) -> None:
    if shutil.which("bash") is None:
        pytest.skip("bash not available")

    changelog_path = tmp_path / "CHANGELOG.md"
    changelog_path.write_text(CHANGELOG)
    provenance = tmp_path / "mkdocs-source-links.intoto.jsonl"
    provenance.write_text("{}\n")
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "mkdocs_source_links-0.6.0-py3-none-any.whl").write_bytes(b"whl")
    (dist / "mkdocs_source_links-0.6.0.tar.gz").write_bytes(b"tar")
    sbom = tmp_path / "sbom"
    sbom.mkdir()
    (sbom / "mkdocs-source-links-0.6.0.cdx.json").write_text("{}")

    notes_path = tmp_path / _NOTES_FILE
    gh_stub = tmp_path / "gh"
    gh_stub.write_text(_GH_STUB_SCRIPT)
    gh_stub.chmod(gh_stub.stat().st_mode | stat.S_IXUSR)

    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}{os.pathsep}{env['PATH']}"
    env["TAG"] = "v0.6.0"
    env["PROVENANCE"] = str(provenance)
    env["CHANGELOG"] = str(changelog_path)

    subprocess.run(
        [_BASH, str(SCRIPT.resolve())],
        cwd=tmp_path,
        env=env,
        check=True,
    )

    notes = notes_path.read_text()
    assert "### Added" in notes
    assert "**Full changelog:**" in notes
    assert notes.endswith(
        "https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.5.2...v0.6.0"
    )
