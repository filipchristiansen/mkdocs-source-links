"""Tests for line-anchor translation in link rewriting."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import REPO
from mkdocs_source_links.ref import ViewRef
from mkdocs_source_links.rewrite import rewrite_repo_parent_links


@pytest.mark.parametrize(
    ("repo_url", "forge", "fragment", "expected_suffix"),
    [
        (REPO, None, "#L10", "#L10"),
        (REPO, None, "#L10-L20", "#L10-L20"),
        (REPO, None, "#section", "#section"),
        ("https://gitlab.com/o/r", None, "#L10", "#L10"),
        ("https://gitlab.com/o/r", None, "#L10-L20", "#L10-20"),
        ("https://gitlab.com/o/r", None, "#intro", "#intro"),
        ("https://bitbucket.org/o/r", None, "#L5", "#lines-5"),
        ("https://bitbucket.org/o/r", None, "#L5-L15", "#lines-5:15"),
        ("https://codeberg.org/o/r", None, "#L3", "#L3"),
        ("https://codeberg.org/o/r", None, "#L3-L7", "#L3-L7"),
        (
            "https://dev.azure.com/o/p/_git/r",
            None,
            "#L10",
            "",
        ),
        (
            "https://dev.azure.com/o/p/_git/r",
            None,
            "#L10-L20",
            "",
        ),
        (
            "https://dev.azure.com/o/p/_git/r",
            None,
            "#readme",
            "#readme",
        ),
    ],
)
def test_rewrite_translates_line_fragments(
    repo_tree: Path,
    repo_url: str,
    forge: str | None,
    fragment: str,
    expected_suffix: str,
) -> None:
    page = repo_tree / "docs" / "page.md"
    md = f"[src](../src.py{fragment})."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=repo_url,
        view_ref=ViewRef("main", "branch"),
        forge=forge,
    )
    assert out.endswith(f"{expected_suffix}).")
    assert "../src.py" not in out
