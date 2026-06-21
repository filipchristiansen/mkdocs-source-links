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
    assert out == f"[a [nested]]({REPO}/blob/main/src.py)\n"


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


def test_rewrite_inline_link_with_escaped_parens(repo_tree: Path) -> None:
    (repo_tree / "file(draft).md").write_text("draft\n")
    md = r"[draft](../file\(draft\).md)" + "\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == f"[draft]({REPO}/blob/main/file%28draft%29.md)\n"


def test_rewrite_inline_link_with_balanced_parens(repo_tree: Path) -> None:
    (repo_tree / "file(draft).md").write_text("draft\n")
    md = "[draft](../file(draft).md)\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == f"[draft]({REPO}/blob/main/file%28draft%29.md)\n"


def test_rewrite_inline_link_with_escaped_parens_and_fragment(repo_tree: Path) -> None:
    (repo_tree / "file(draft).md").write_text("a\nb\n")
    md = r"[draft](../file\(draft\).md#L2)" + "\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == f"[draft]({REPO}/blob/main/file%28draft%29.md#L2)\n"


def test_rewrite_inline_link_with_escaped_parens_and_title(repo_tree: Path) -> None:
    (repo_tree / "file(draft).md").write_text("draft\n")
    md = r'[draft](../file\(draft\).md "Draft notes")' + "\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == f'[draft]({REPO}/blob/main/file%28draft%29.md "Draft notes")\n'


def test_rewrite_inline_link_angle_bracket_with_literal_parens(repo_tree: Path) -> None:
    (repo_tree / "file(draft).md").write_text("draft\n")
    md = "[draft](<../file(draft).md>)\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == f"[draft]({REPO}/blob/main/file%28draft%29.md)\n"


def test_rewrite_inline_link_with_unbalanced_parens_left_unchanged(repo_tree: Path) -> None:
    md = "[x](../file(draft.md)\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == md
    assert "github.com" not in out


def test_rewrite_inline_link_angle_bracket_with_escaped_char(repo_tree: Path) -> None:
    md = r"[env](<../env\.example>)" + "\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == f"[env]({REPO}/blob/main/env.example)\n"


def test_rewrite_inline_link_angle_bracket_with_inner_angle_unchanged(repo_tree: Path) -> None:
    md = "[x](<../a<b>).\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == md
    assert "github.com" not in out


def test_rewrite_inline_link_unterminated_angle_bracket_unchanged(repo_tree: Path) -> None:
    md = "[env](<../env.example).\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == md
    assert "github.com" not in out


def test_rewrite_inline_link_empty_destination_unchanged(repo_tree: Path) -> None:
    md = "[x]().\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == md
    assert "github.com" not in out


def test_rewrite_inline_link_unbalanced_open_paren_unchanged(repo_tree: Path) -> None:
    md = "[x](../a( ).\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == md
    assert "github.com" not in out


def test_rewrite_inline_link_title_with_escaped_quote(repo_tree: Path) -> None:
    md = r'[env](../env.example "a \" b").' + "\n"
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == f'[env]({REPO}/blob/main/env.example "a \\" b").\n'


def test_rewrite_inline_link_unterminated_title_unchanged(repo_tree: Path) -> None:
    md = '[env](../env.example "unterminated).\n'
    out = rewrite_on_docs_page(repo_tree, md)
    assert out == md
    assert "github.com" not in out
