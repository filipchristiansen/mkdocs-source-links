"""Tests for skipping image links during ../ rewrite."""

from __future__ import annotations

from pathlib import Path

from conftest import REPO, rewrite_on_docs_page
from mkdocs_source_links._scan import collect_image_reference_labels


def test_rewrite_skips_inline_image(repo_tree: Path) -> None:
    md = "![alt](../img.png)\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == md
    assert "github.com" not in out


def test_rewrite_skips_titled_inline_image(repo_tree: Path) -> None:
    md = '![alt text](../img.png "title")\n'
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == md


def test_rewrite_skips_angle_bracket_inline_image(repo_tree: Path) -> None:
    md = "![alt](<../wide img.png>)\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == md


def test_rewrite_still_rewrites_normal_link_beside_image(repo_tree: Path) -> None:
    md = "![alt](../img.png) and [code](../img.png)\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == f"![alt](../img.png) and [code]({REPO}/blob/main/img.png)\n"


def test_rewrite_skips_image_reference_definition_full(repo_tree: Path) -> None:
    md = "![logo][img]\n\n[img]: ../img.png\n"
    assert rewrite_on_docs_page(repo_tree, md) == md


def test_rewrite_skips_image_reference_definition_collapsed(repo_tree: Path) -> None:
    md = "![img][]\n\n[img]: ../img.png\n"
    assert rewrite_on_docs_page(repo_tree, md) == md


def test_rewrite_skips_image_reference_definition_shortcut(repo_tree: Path) -> None:
    md = "![img]\n\n[img]: ../img.png\n"
    assert rewrite_on_docs_page(repo_tree, md) == md


def test_rewrite_skips_image_ref_def_with_normalized_label(repo_tree: Path) -> None:
    md = "![x][my   image]\n\n[My Image]: ../img.png\n"
    assert rewrite_on_docs_page(repo_tree, md) == md


def test_rewrite_skips_image_ref_def_when_label_shared_with_image_usage(repo_tree: Path) -> None:
    md = "[docs][ref]\n![docs]\n\n[docs]: ../img.png\n"
    assert rewrite_on_docs_page(repo_tree, md) == md


def test_rewrite_skips_image_ref_with_nested_brackets_in_alt(repo_tree: Path) -> None:
    md = "![icon [beta]][img-ref]\n\n[img-ref]: ../img.png\n"
    assert rewrite_on_docs_page(repo_tree, md) == md


def test_rewrite_skips_image_ref_with_escaped_bracket_in_alt(repo_tree: Path) -> None:
    md = "![a \\] b][img]\n\n[img]: ../img.png\n"
    assert rewrite_on_docs_page(repo_tree, md) == md


def test_rewrite_still_rewrites_link_reference_definition(repo_tree: Path) -> None:
    md = "[cfg][ref]\n\n[ref]: ../img.png\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == f"[cfg][ref]\n\n[ref]: {REPO}/blob/main/img.png\n"


def test_rewrite_rewrites_link_ref_when_full_image_ref_shares_alt_label(repo_tree: Path) -> None:
    md = "![logo][cfg]\n\n[logo]: ../src.py\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == f"![logo][cfg]\n\n[logo]: {REPO}/blob/main/src.py\n"


def test_collect_image_reference_labels_shortcut_at_eof() -> None:
    assert "solo" in collect_image_reference_labels("![solo]")


def test_collect_image_reference_labels_ignores_unbalanced_alt() -> None:
    assert collect_image_reference_labels("![unclosed") == frozenset()


def test_collect_image_reference_labels_ignores_unbalanced_ref_label() -> None:
    assert collect_image_reference_labels("![alt][unclosed") == frozenset()
