"""Shared pytest fixtures for rewrite tests."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from mkdocs_source_links.ref import ViewRef
from mkdocs_source_links.rewrite import rewrite_repo_parent_links

REPO = "https://github.com/example/example-repo"


@pytest.fixture(name="repo_tree")
def _repo_tree(tmp_path: Path) -> Path:
    """Minimal repo layout shared by rewrite tests."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "page.md").write_text("# Page\n")
    (tmp_path / "env.example").write_text("FOO=bar\n")
    (tmp_path / "src.py").write_text("line1\nline2\n")
    (tmp_path / "img.png").write_bytes(b"\x89PNG\r\n")
    (tmp_path / "wide img.png").write_bytes(b"\x89PNG\r\n")
    backend = tmp_path / "backend" / "src"
    backend.mkdir(parents=True)
    (backend / "config.py").write_text("X = 1\n")
    (tmp_path / "scripts").mkdir()
    return tmp_path


def rewrite_on_docs_page(
    repo_tree: Path,
    md: str,
    *,
    repo_url: str = REPO,
    view_ref: ViewRef | None = None,
    forge: str | None = None,
    report_missing: Callable[[str], None] | None = None,
) -> str:
    """Run ``rewrite_repo_parent_links`` for ``docs/page.md`` in ``repo_tree``."""
    return rewrite_repo_parent_links(
        md,
        page_abs_path=repo_tree / "docs" / "page.md",
        repo_root=repo_tree,
        repo_url=repo_url,
        view_ref=view_ref or ViewRef("main", "branch"),
        forge=forge,
        report_missing=report_missing,
    )
