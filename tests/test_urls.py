"""Tests for forge detection and view-URL building."""

from __future__ import annotations

import pytest

from mkdocs_source_links.urls import SUPPORTED_FORGES, detect_forge, repo_view_url


@pytest.mark.parametrize(
    ("repo_url", "expected"),
    [
        ("https://github.com/org/repo", "github"),
        ("https://gitlab.com/org/repo", "gitlab"),
        ("https://bitbucket.org/org/repo", "bitbucket"),
        ("https://codeberg.org/org/repo", "gitea"),
        ("https://dev.azure.com/org/project/_git/repo", "azure"),
        ("https://myorg.visualstudio.com/project/_git/repo", "azure"),
        # Self-hosted instances detected via hostname hints:
        ("https://github.example.com/org/repo", "github"),
        ("https://gitlab.example.com/org/repo", "gitlab"),
        ("https://gitea.example.com/org/repo", "gitea"),
        ("https://forgejo.example.com/org/repo", "gitea"),
        ("https://bitbucket.example.com/org/repo", "bitbucket"),
        # Unknown / ambiguous hosts:
        ("https://example.com/org/repo", None),
        ("not-a-url", None),
    ],
)
def test_detect_forge(repo_url: str, expected: str | None) -> None:
    assert detect_forge(repo_url) == expected


@pytest.mark.parametrize(
    ("repo_url", "is_dir", "expected"),
    [
        ("https://github.com/o/r", False, "https://github.com/o/r/blob/main/a/b.py"),
        ("https://github.com/o/r", True, "https://github.com/o/r/tree/main/a/b.py"),
        ("https://gitlab.com/o/r", False, "https://gitlab.com/o/r/-/blob/main/a/b.py"),
        ("https://gitlab.com/o/r", True, "https://gitlab.com/o/r/-/tree/main/a/b.py"),
        ("https://bitbucket.org/o/r", False, "https://bitbucket.org/o/r/src/main/a/b.py"),
        ("https://codeberg.org/o/r", False, "https://codeberg.org/o/r/src/branch/main/a/b.py"),
        (
            "https://dev.azure.com/o/p/_git/r",
            False,
            "https://dev.azure.com/o/p/_git/r?path=/a/b.py&version=GBmain",
        ),
    ],
)
def test_repo_view_url_per_forge(
    repo_url: str,
    is_dir: bool,  # noqa: FBT001
    expected: str,
) -> None:
    assert (
        repo_view_url(repo_url=repo_url, branch="main", repo_path="a/b.py", is_dir=is_dir)
        == expected
    )


def test_repo_view_url_trailing_slash_normalized() -> None:
    assert (
        repo_view_url(
            repo_url="https://github.com/o/r/", branch="main", repo_path="x", is_dir=False
        )
        == "https://github.com/o/r/blob/main/x"
    )


def test_repo_view_url_explicit_forge_override() -> None:
    # Unknown host, but the forge is forced.
    assert (
        repo_view_url(
            repo_url="https://scm.internal/o/r",
            branch="dev",
            repo_path="x.py",
            is_dir=False,
            forge="gitlab",
        )
        == "https://scm.internal/o/r/-/blob/dev/x.py"
    )


def test_repo_view_url_unknown_host_returns_none() -> None:
    assert (
        repo_view_url(
            repo_url="https://example.com/o/r", branch="main", repo_path="x", is_dir=False
        )
        is None
    )


def test_supported_forges_contains_expected() -> None:
    assert set(SUPPORTED_FORGES) == {"github", "gitlab", "bitbucket", "gitea", "azure"}
