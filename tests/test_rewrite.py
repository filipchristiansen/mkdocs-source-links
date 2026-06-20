"""Tests for ../ link rewriting."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import REPO
from mkdocs_source_links.ref import ViewRef
from mkdocs_source_links.rewrite import repo_relative_path, rewrite_repo_parent_links


def test_repo_relative_path_from_docs(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    assert (
        repo_relative_path(page_abs_path=page, href="../env.example", repo_root=repo_tree)
        == "env.example"
    )


def test_repo_relative_path_to_nested_file(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    assert (
        repo_relative_path(
            page_abs_path=page,
            href="../backend/src/config.py",
            repo_root=repo_tree,
        )
        == "backend/src/config.py"
    )


def test_repo_relative_path_outside_repo(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    assert (
        repo_relative_path(
            page_abs_path=page,
            href="../../etc/passwd",
            repo_root=repo_tree,
        )
        is None
    )


def test_repo_relative_path_non_parent_href(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    assert repo_relative_path(page_abs_path=page, href="other.md", repo_root=repo_tree) is None


def test_repo_relative_path_filename_starting_with_dot_dot(repo_tree: Path) -> None:
    weird = repo_tree / "..weird"
    weird.mkdir()
    (weird / "file.txt").write_text("x\n")
    page = repo_tree / "docs" / "page.md"
    assert (
        repo_relative_path(
            page_abs_path=page,
            href="../..weird/file.txt",
            repo_root=repo_tree,
        )
        == "..weird/file.txt"
    )


def test_rewrite_link_to_filename_starting_with_dot_dot(repo_tree: Path) -> None:
    weird = repo_tree / "..weird"
    weird.mkdir()
    (weird / "file.txt").write_text("x\n")
    md = "[f](../..weird/file.txt)\n"
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=repo_tree / "docs" / "page.md",
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    assert f"]({REPO}/blob/main/..weird/file.txt)" in out


def test_rewrite_outside_repo_unchanged(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[etc](../../etc/passwd)."
    assert (
        rewrite_repo_parent_links(
            md,
            page_abs_path=page,
            repo_root=repo_tree,
            repo_url=REPO,
            view_ref=ViewRef("main", "branch"),
        )
        == md
    )


def test_report_missing_called_for_missing_target(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[gone](../does_not_exist.py)."
    missing: list[str] = []
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
        report_missing=missing.append,
    )
    assert out == md
    assert missing == ["../does_not_exist.py"]


def test_report_missing_not_called_outside_repo(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[etc](../../etc/does_not_exist)."
    missing: list[str] = []
    rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
        report_missing=missing.append,
    )
    assert not missing


def test_report_rewrite_called_for_inline_link(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[cfg](../env.example)."
    rewrites: list[None] = []
    rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
        report_rewrite=lambda: rewrites.append(None),
    )
    assert len(rewrites) == 1


def test_report_rewrite_called_for_reference_definition(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[cfg]: ../env.example\n"
    rewrites: list[None] = []
    rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
        report_rewrite=lambda: rewrites.append(None),
    )
    assert len(rewrites) == 1


def test_report_rewrite_not_called_for_missing_target(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[gone](../does_not_exist.py)."
    rewrites: list[None] = []
    rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
        report_rewrite=lambda: rewrites.append(None),
    )
    assert not rewrites


def test_report_rewrite_not_called_outside_repo(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[etc](../../etc/passwd)."
    rewrites: list[None] = []
    rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
        report_rewrite=lambda: rewrites.append(None),
    )
    assert not rewrites


def test_report_rewrite_not_called_for_inline_image(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "![alt](../img.png)\n"
    rewrites: list[None] = []
    rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
        report_rewrite=lambda: rewrites.append(None),
    )
    assert not rewrites


def test_report_rewrite_counts_mixed_links(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[a](../env.example) and [b](../src.py)\n\n[c]: ../backend/src/config.py\n"
    rewrites: list[None] = []
    rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
        report_rewrite=lambda: rewrites.append(None),
    )
    assert len(rewrites) == 3


@pytest.mark.parametrize(
    ("md", "kwargs"),
    [
        ("```markdown\n[env](../env.example)\n```\n", {}),
        ("Write `[env](../env.example)` to link a repo file.", {}),
        (
            "[cfg](../backend/src/config.py).",
            {"repo_url": "https://example.com/example/example-repo"},
        ),
        ("![logo][img]\n\n[img]: ../img.png\n", {}),
    ],
    ids=["fenced_code", "inline_code", "unsupported_host", "image_reference_definition"],
)
def test_report_rewrite_not_called_for_skipped_links(
    repo_tree: Path,
    md: str,
    kwargs: dict[str, str],
) -> None:
    page = repo_tree / "docs" / "page.md"
    rewrites: list[None] = []
    rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=kwargs.get("repo_url", REPO),
        view_ref=ViewRef("main", "branch"),
        report_rewrite=lambda: rewrites.append(None),
    )
    assert not rewrites


def test_rewrite_leaves_in_doc_links(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "See [other](other.md#anchor)."
    assert (
        rewrite_repo_parent_links(
            md,
            page_abs_path=page,
            repo_root=repo_tree,
            repo_url=REPO,
            view_ref=ViewRef("main", "branch"),
        )
        == md
    )


def test_rewrite_file_link_to_blob(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[`config.py`](../backend/src/config.py)."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    assert out == (f"[`config.py`]({REPO}/blob/main/backend/src/config.py).")


def test_rewrite_directory_link_to_tree(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[scripts](../scripts/)."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("develop", "branch"),
    )
    assert out == f"[scripts]({REPO}/tree/develop/scripts)."


def test_rewrite_directory_link_without_trailing_slash(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[scripts](../scripts)."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("develop", "branch"),
    )
    assert out == f"[scripts]({REPO}/tree/develop/scripts)."


def test_rewrite_link_with_fragment(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[env](../env.example#section)."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    assert out == f"[env]({REPO}/blob/main/env.example#section)."


def test_rewrite_missing_path_unchanged(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[missing](../no/such/file.py)."
    assert (
        rewrite_repo_parent_links(
            md,
            page_abs_path=page,
            repo_root=repo_tree,
            repo_url=REPO,
            view_ref=ViewRef("main", "branch"),
        )
        == md
    )


def test_rewrite_unsupported_host_unchanged(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[cfg](../backend/src/config.py)."
    unknown = "https://example.com/example/example-repo"
    assert (
        rewrite_repo_parent_links(
            md,
            page_abs_path=page,
            repo_root=repo_tree,
            repo_url=unknown,
            view_ref=ViewRef("main", "branch"),
        )
        == md
    )


def test_rewrite_forge_override(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[cfg](../backend/src/config.py)."
    self_hosted = "https://scm.internal.example/example/example-repo"
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=self_hosted,
        view_ref=ViewRef("main", "branch"),
        forge="gitlab",
    )
    assert out == f"[cfg]({self_hosted}/-/blob/main/backend/src/config.py)."


def test_rewrite_skips_fenced_code_block(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "```markdown\n[env](../env.example)\n```\n"
    assert (
        rewrite_repo_parent_links(
            md,
            page_abs_path=page,
            repo_root=repo_tree,
            repo_url=REPO,
            view_ref=ViewRef("main", "branch"),
        )
        == md
    )


def test_rewrite_skips_inline_code_span(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "Write `[env](../env.example)` to link a repo file."
    assert (
        rewrite_repo_parent_links(
            md,
            page_abs_path=page,
            repo_root=repo_tree,
            repo_url=REPO,
            view_ref=ViewRef("main", "branch"),
        )
        == md
    )


def test_rewrite_real_link_with_adjacent_code(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = (
        "Example `](../x)` then real [env](../env.example) and:\n\n"
        "```\n[env](../env.example)\n```\n"
    )
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    # The inline span and the fenced block are untouched; only the real link is rewritten.
    assert "`](../x)`" in out
    assert "```\n[env](../env.example)\n```" in out
    assert f"[env]({REPO}/blob/main/env.example)" in out


def test_rewrite_titled_link_preserves_title(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = '[env](../env.example "The env file").'
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    assert out == f'[env]({REPO}/blob/main/env.example "The env file").'


def test_rewrite_titled_link_single_quotes(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[env](../env.example 'title')."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    assert out == f"[env]({REPO}/blob/main/env.example 'title')."


def test_rewrite_angle_bracket_link(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[env](<../env.example>)."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    assert out == f"[env]({REPO}/blob/main/env.example)."


def test_rewrite_angle_bracket_link_with_fragment(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[env](<../env.example#section>)."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    assert out == f"[env]({REPO}/blob/main/env.example#section)."


def test_rewrite_angle_bracket_link_with_space(repo_tree: Path) -> None:
    (repo_tree / "my file.py").write_text("X = 1\n")
    page = repo_tree / "docs" / "page.md"
    md = "[f](<../my file.py>)."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    assert out == f"[f]({REPO}/blob/main/my%20file.py)."


def test_rewrite_angle_bracket_link_with_space_and_fragment(repo_tree: Path) -> None:
    (repo_tree / "my file.py").write_text("X = 1\n")
    page = repo_tree / "docs" / "page.md"
    md = "[f](<../my file.py#L2>)."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    assert out == f"[f]({REPO}/blob/main/my%20file.py#L2)."


def test_rewrite_uses_branch(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[env](../env.example)."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("master", "branch"),
    )
    assert "blob/master/env.example" in out
