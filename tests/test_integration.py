"""Integration test: plugin rewrites links in a real mkdocs build."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_mkdocs_build_rewrites_parent_links(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text(
        "See [config](../backend/config.py) and [scripts](../scripts/).\n"
    )
    backend = tmp_path / "backend"
    backend.mkdir()
    (backend / "config.py").write_text("X = 1\n")
    (tmp_path / "scripts").mkdir()

    (tmp_path / "mkdocs.yml").write_text(
        """
site_name: test
repo_url: https://github.com/example/test-repo
edit_uri: edit/main/docs/
plugins:
  - source-links
""".strip()
        + "\n"
    )

    site = tmp_path / "site"
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "-d", str(site)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    html = (site / "index.html").read_text()
    assert "github.com/example/test-repo/blob/main/backend/config.py" in html
    assert "github.com/example/test-repo/tree/main/scripts" in html
