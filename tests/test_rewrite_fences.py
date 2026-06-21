"""Tests for CommonMark fence closing and related rewrite edge cases."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import REPO, rewrite_on_docs_page
from mkdocs_source_links.ref import ViewRef


def test_rewrite_empty_markdown_unchanged(repo_tree: Path) -> None:
    assert rewrite_on_docs_page(repo_tree, "") == ""


def test_rewrite_skips_link_in_tilde_fence(repo_tree: Path) -> None:
    md = "~~~\n[env](../env.example)\n~~~\n\n[cfg](../backend/src/config.py).\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == (
        f"~~~\n[env](../env.example)\n~~~\n\n[cfg]({REPO}/blob/main/backend/src/config.py).\n"
    )


def test_rewrite_skips_link_in_tilde_fence_closed_with_longer_marker(repo_tree: Path) -> None:
    md = "~~~\n[env](../env.example)\n~~~~\n\n[cfg](../backend/src/config.py).\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == (
        f"~~~\n[env](../env.example)\n~~~~\n\n[cfg]({REPO}/blob/main/backend/src/config.py).\n"
    )


def test_indented_code_block_rewrites_parent_link(repo_tree: Path) -> None:
    md = "    [cfg](../env.example).\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == f"    [cfg]({REPO}/blob/main/env.example).\n"


def test_rewrite_skips_link_in_fence_closed_with_longer_marker(repo_tree: Path) -> None:
    md = "```\n[env](../env.example)\n````\n\n[cfg](../backend/src/config.py).\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == (
        f"```\n[env](../env.example)\n````\n\n[cfg]({REPO}/blob/main/backend/src/config.py).\n"
    )


def test_rewrite_reference_definition_after_fence_closed_with_longer_marker(
    repo_tree: Path,
) -> None:
    md = "```\n[skip]: ../env.example\n````\n\n[cfg]: ../backend/src/config.py\n"
    assert rewrite_on_docs_page(repo_tree, md) == (
        f"```\n[skip]: ../env.example\n````\n\n[cfg]: {REPO}/blob/main/backend/src/config.py\n"
    )


def test_rewrite_skips_link_in_long_opener_fence_with_shorter_marker_line(
    repo_tree: Path,
) -> None:
    md = "`````\n```\n[bad](../env.example)\n`````\n"
    assert rewrite_on_docs_page(repo_tree, md) == md


def test_rewrite_reference_definition_inside_unclosed_fence_skipped(repo_tree: Path) -> None:
    md = "```\n[skip]: ../backend/src/config.py\n\n[cfg]: ../env.example\n"
    assert rewrite_on_docs_page(repo_tree, md) == md


def test_rewrite_symlink_uses_lexical_path(repo_tree: Path) -> None:
    target = repo_tree / "backend" / "src" / "config.py"
    alias = repo_tree / "alias.py"
    try:
        alias.symlink_to(target)
    except OSError:
        pytest.skip("symlinks not supported in this environment")
    md = "[cfg](../alias.py)."
    out = rewrite_on_docs_page(repo_tree, md, view_ref=ViewRef("main", "branch"))
    assert out == f"[cfg]({REPO}/blob/main/alias.py)."
