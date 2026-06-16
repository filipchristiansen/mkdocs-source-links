"""Tests for ../ link rewriting."""

from __future__ import annotations

from pathlib import Path

import pytest

from mkdocs_source_links.rewrite import repo_relative_path, rewrite_repo_parent_links
from mkdocs_source_links.urls import repo_view_url

REPO = "https://github.com/example/example-repo"


@pytest.fixture(name="repo_tree")
def _repo_tree(tmp_path: Path) -> Path:
    """Minimal repo: docs/page.md, env.example, backend/, scripts/."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "page.md").write_text("# Page\n")
    (tmp_path / "env.example").write_text("FOO=bar\n")
    backend = tmp_path / "backend" / "src"
    backend.mkdir(parents=True)
    (backend / "config.py").write_text("X = 1\n")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    return tmp_path


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


def test_rewrite_outside_repo_unchanged(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[etc](../../etc/passwd)."
    assert (
        rewrite_repo_parent_links(
            md,
            page_abs_path=page,
            repo_root=repo_tree,
            repo_url=REPO,
            branch="main",
        )
        == md
    )


def test_rewrite_leaves_in_doc_links(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "See [other](other.md#anchor)."
    assert (
        rewrite_repo_parent_links(
            md,
            page_abs_path=page,
            repo_root=repo_tree,
            repo_url=REPO,
            branch="main",
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
        branch="main",
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
        branch="develop",
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
        branch="main",
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
            branch="main",
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
            branch="main",
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
        branch="main",
        forge="gitlab",
    )
    assert out == f"[cfg]({self_hosted}/-/blob/main/backend/src/config.py)."


def test_rewrite_uses_branch(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[env](../env.example)."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        branch="master",
    )
    assert "blob/master/env.example" in out


def test_repo_view_url_file() -> None:
    assert (
        repo_view_url(
            repo_url=REPO,
            branch="main",
            repo_path="env.example",
            is_dir=False,
        )
        == f"{REPO}/blob/main/env.example"
    )


def test_repo_view_url_directory() -> None:
    assert (
        repo_view_url(
            repo_url=REPO,
            branch="main",
            repo_path="scripts",
            is_dir=True,
        )
        == f"{REPO}/tree/main/scripts"
    )


def test_repo_view_url_unsupported_host() -> None:
    assert (
        repo_view_url(
            repo_url="https://example.com/org/repo",
            branch="main",
            repo_path="foo.py",
            is_dir=False,
        )
        is None
    )
