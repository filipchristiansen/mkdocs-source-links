"""Tests for reference-style ../ link rewriting."""

from __future__ import annotations

from pathlib import Path

from conftest import REPO, rewrite_on_docs_page
from mkdocs_source_links.ref import ViewRef


def test_rewrite_reference_definition_file(repo_tree: Path) -> None:
    assert (
        rewrite_on_docs_page(repo_tree, "[cfg]: ../backend/src/config.py\n")
        == f"[cfg]: {REPO}/blob/main/backend/src/config.py\n"
    )


def test_rewrite_reference_definition_with_fragment(repo_tree: Path) -> None:
    assert (
        rewrite_on_docs_page(repo_tree, "[env]: ../env.example#section\n")
        == f"[env]: {REPO}/blob/main/env.example#section\n"
    )


def test_rewrite_reference_definition_with_title(repo_tree: Path) -> None:
    assert (
        rewrite_on_docs_page(repo_tree, '[env]: ../env.example "The env file"\n')
        == f'[env]: {REPO}/blob/main/env.example "The env file"\n'
    )


def test_rewrite_reference_definition_directory(repo_tree: Path) -> None:
    assert (
        rewrite_on_docs_page(
            repo_tree,
            "[scripts]: ../scripts/\n",
            view_ref=ViewRef("develop", "branch"),
        )
        == f"[scripts]: {REPO}/tree/develop/scripts\n"
    )


def test_rewrite_reference_definition_directory_without_trailing_slash(
    repo_tree: Path,
) -> None:
    assert (
        rewrite_on_docs_page(
            repo_tree,
            "[scripts]: ../scripts\n",
            view_ref=ViewRef("develop", "branch"),
        )
        == f"[scripts]: {REPO}/tree/develop/scripts\n"
    )


def test_rewrite_reference_definition_angle_bracket(repo_tree: Path) -> None:
    assert (
        rewrite_on_docs_page(repo_tree, "[env]: <../env.example#section>\n")
        == f"[env]: {REPO}/blob/main/env.example#section\n"
    )


def test_rewrite_reference_usage_with_definition(repo_tree: Path) -> None:
    md = "See [config][cfg].\n\n[cfg]: ../backend/src/config.py\n"
    assert rewrite_on_docs_page(repo_tree, md) == (
        f"See [config][cfg].\n\n[cfg]: {REPO}/blob/main/backend/src/config.py\n"
    )


def test_rewrite_reference_definition_skips_fenced_code_block(repo_tree: Path) -> None:
    md = "```markdown\n[cfg]: ../backend/src/config.py\n```\n"
    assert rewrite_on_docs_page(repo_tree, md) == md


def test_fenced_image_ref_does_not_suppress_link_reference_definition(repo_tree: Path) -> None:
    md = "```\n![x][cfg]\n```\n\n[cfg]: ../src.py\n"
    assert rewrite_on_docs_page(repo_tree, md) == (
        f"```\n![x][cfg]\n```\n\n[cfg]: {REPO}/blob/main/src.py\n"
    )


def test_rewrite_reference_definition_after_single_line_fence(repo_tree: Path) -> None:
    md = "```f()```\n\n[cfg]: ../backend/src/config.py\n"
    assert rewrite_on_docs_page(repo_tree, md) == (
        f"```f()```\n\n[cfg]: {REPO}/blob/main/backend/src/config.py\n"
    )


def test_rewrite_reference_definition_missing_reports(repo_tree: Path) -> None:
    missing: list[str] = []
    md = "[gone]: ../does_not_exist.py\n"
    assert rewrite_on_docs_page(repo_tree, md, report_missing=missing.append) == md
    assert missing == ["../does_not_exist.py"]


def test_rewrite_reference_definition_non_parent_unchanged(repo_tree: Path) -> None:
    assert rewrite_on_docs_page(repo_tree, "[other]: other.md\n") == "[other]: other.md\n"


def test_rewrite_reference_definition_preserves_leading_spaces(repo_tree: Path) -> None:
    assert (
        rewrite_on_docs_page(repo_tree, "  [cfg]: ../backend/src/config.py\n")
        == f"  [cfg]: {REPO}/blob/main/backend/src/config.py\n"
    )


def test_rewrite_reference_definition_preserves_max_indent(repo_tree: Path) -> None:
    assert (
        rewrite_on_docs_page(repo_tree, "   [env]: ../env.example\n")
        == f"   [env]: {REPO}/blob/main/env.example\n"
    )


def test_rewrite_reference_definition_preserves_indent_with_title(repo_tree: Path) -> None:
    assert (
        rewrite_on_docs_page(repo_tree, '  [env]: ../env.example "The env file"\n')
        == f'  [env]: {REPO}/blob/main/env.example "The env file"\n'
    )


def test_rewrite_reference_definition_over_indent_unchanged(repo_tree: Path) -> None:
    md = "    [cfg]: ../backend/src/config.py\n"
    assert rewrite_on_docs_page(repo_tree, md) == md
