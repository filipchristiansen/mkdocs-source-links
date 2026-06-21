"""Tests for branch resolution."""

from __future__ import annotations

from pathlib import Path

from conftest import REPO
from mkdocs_source_links.branch import resolve_branch
from mkdocs_source_links.ref import ViewRef
from mkdocs_source_links.rewrite import rewrite_repo_parent_links


def test_plugin_branch_wins() -> None:
    assert (
        resolve_branch(
            plugin_branch="develop",
            extra={"git_branch": "master"},
            edit_uri="edit/main/docs/",
        )
        == "develop"
    )


def test_extra_git_branch() -> None:
    assert (
        resolve_branch(
            plugin_branch=None,
            extra={"git_branch": "master"},
            edit_uri="edit/main/docs/",
        )
        == "master"
    )


def test_edit_uri_edit_prefix() -> None:
    assert (
        resolve_branch(
            plugin_branch=None,
            extra={},
            edit_uri="edit/master/docs/",
        )
        == "master"
    )


def test_edit_uri_blob_prefix() -> None:
    assert (
        resolve_branch(
            plugin_branch=None,
            extra={},
            edit_uri="blob/develop/docs/",
        )
        == "develop"
    )


def test_edit_uri_bitbucket_src_prefix() -> None:
    assert (
        resolve_branch(
            plugin_branch=None,
            extra={},
            edit_uri="src/develop/docs/",
        )
        == "develop"
    )


def test_edit_uri_gitlab_edit_prefix() -> None:
    assert (
        resolve_branch(
            plugin_branch=None,
            extra={},
            edit_uri="-/edit/main/docs/",
        )
        == "main"
    )


def test_edit_uri_gitlab_blob_prefix() -> None:
    assert (
        resolve_branch(
            plugin_branch=None,
            extra={},
            edit_uri="-/blob/develop/docs/",
        )
        == "develop"
    )


def test_edit_uri_unrecognized_falls_back_to_main() -> None:
    assert (
        resolve_branch(
            plugin_branch=None,
            extra={},
            edit_uri="custom/path/docs/",
        )
        == "main"
    )


def test_fallback_main() -> None:
    assert resolve_branch(plugin_branch=None, extra={}, edit_uri=None) == "main"


def test_built_url_uses_resolved_branch(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    page = docs / "index.md"
    page.write_text("# Index\n")
    (tmp_path / "README.md").write_text("# Readme\n")

    md = "[readme](../README.md)."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=tmp_path,
        repo_url=REPO,
        view_ref=ViewRef(
            resolve_branch(
                plugin_branch=None,
                extra={},
                edit_uri="blob/develop/docs/",
            ),
            "branch",
        ),
    )
    assert "blob/develop/README.md" in out
