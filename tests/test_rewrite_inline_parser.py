"""Tests for bracket-aware inline link and image scanning."""

from __future__ import annotations

from pathlib import Path

from conftest import REPO, rewrite_on_docs_page


def test_rewrite_leaves_lonely_parent_link_suffix_in_prose(repo_tree: Path) -> None:
    md = "This is not a link: ](../src.py)\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == md
    assert "github.com" not in out


def test_rewrite_still_rewrites_link_with_nested_brackets_in_label(repo_tree: Path) -> None:
    md = "[a [nested]](../src.py)\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert f"[a [nested]]({REPO}/blob/main/src.py)" in out


def test_rewrite_skips_image_with_nested_brackets_in_alt(repo_tree: Path) -> None:
    md = "![a [nested]](../img.png)\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == md
    assert "github.com" not in out


def test_rewrite_skips_image_with_escaped_bracket_in_alt(repo_tree: Path) -> None:
    md = r"![a \] bracket](../img.png)" + "\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == md
    assert "github.com" not in out


def test_rewrite_skips_image_when_alt_contains_link_like_parent_path(repo_tree: Path) -> None:
    md = "![see [link](../src.py)](../img.png)\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == md
    assert "github.com" not in out


def test_rewrite_leaves_unbalanced_bracket_text_unchanged(repo_tree: Path) -> None:
    md = "See [unclosed text\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == md


def test_rewrite_leaves_reference_style_usage_without_inline_dest(repo_tree: Path) -> None:
    md = "Use [text][ref] for more.\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == md


def test_rewrite_leaves_inline_link_with_non_parent_dest_unchanged(repo_tree: Path) -> None:
    md = "[other](src.py)\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == md
