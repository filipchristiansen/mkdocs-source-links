"""Tests for forge detection and view-URL building."""

from __future__ import annotations

import pytest

from mkdocs_source_links.ref import RefKind
from mkdocs_source_links.urls import (
    SUPPORTED_FORGES,
    _azure_version_prefix,
    _gitea_ref_segment,
    detect_forge,
    repo_view_url,
)


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
        ("https://bitbucket.example.com/org/repo", None),
        # Hostnames where the forge name is not a distinct label:
        ("https://notgitlab.com/org/repo", None),
        ("https://my-github.com/org/repo", None),
        ("https://github-mirror.example.com/org/repo", None),
        # Unknown / ambiguous hosts:
        ("https://example.com/org/repo", None),
        ("not-a-url", None),
    ],
)
def test_detect_forge(repo_url: str, expected: str | None) -> None:
    assert detect_forge(repo_url) == expected


@pytest.mark.parametrize(
    ("repo_url", "is_dir", "ref", "ref_kind", "expected"),
    [
        (
            "https://github.com/o/r",
            False,
            "main",
            "branch",
            "https://github.com/o/r/blob/main/a/b.py",
        ),
        (
            "https://github.com/o/r",
            True,
            "main",
            "branch",
            "https://github.com/o/r/tree/main/a/b.py",
        ),
        (
            "https://gitlab.com/o/r",
            False,
            "main",
            "branch",
            "https://gitlab.com/o/r/-/blob/main/a/b.py",
        ),
        (
            "https://gitlab.com/o/r",
            True,
            "main",
            "branch",
            "https://gitlab.com/o/r/-/tree/main/a/b.py",
        ),
        (
            "https://bitbucket.org/o/r",
            False,
            "main",
            "branch",
            "https://bitbucket.org/o/r/src/main/a/b.py",
        ),
        (
            "https://codeberg.org/o/r",
            False,
            "main",
            "branch",
            "https://codeberg.org/o/r/src/branch/main/a/b.py",
        ),
        (
            "https://dev.azure.com/o/p/_git/r",
            False,
            "main",
            "branch",
            "https://dev.azure.com/o/p/_git/r?path=/a/b.py&version=GBmain",
        ),
        (
            "https://github.com/o/r",
            False,
            "abc123def",
            "commit",
            "https://github.com/o/r/blob/abc123def/a/b.py",
        ),
        (
            "https://gitlab.com/o/r",
            False,
            "abc123def",
            "commit",
            "https://gitlab.com/o/r/-/blob/abc123def/a/b.py",
        ),
        (
            "https://bitbucket.org/o/r",
            False,
            "abc123def",
            "commit",
            "https://bitbucket.org/o/r/src/abc123def/a/b.py",
        ),
        (
            "https://codeberg.org/o/r",
            False,
            "abc123def",
            "commit",
            "https://codeberg.org/o/r/src/commit/abc123def/a/b.py",
        ),
        (
            "https://codeberg.org/o/r",
            False,
            "v1.2.3",
            "branch",
            "https://codeberg.org/o/r/src/branch/v1.2.3/a/b.py",
        ),
        (
            "https://codeberg.org/o/r",
            False,
            "v1.0.0",
            "tag",
            "https://codeberg.org/o/r/src/tag/v1.0.0/a/b.py",
        ),
        (
            "https://dev.azure.com/o/p/_git/r",
            False,
            "v1.2.3",
            "branch",
            "https://dev.azure.com/o/p/_git/r?path=/a/b.py&version=GBv1.2.3",
        ),
        (
            "https://dev.azure.com/o/p/_git/r",
            False,
            "v1.0.0",
            "tag",
            "https://dev.azure.com/o/p/_git/r?path=/a/b.py&version=GTv1.0.0",
        ),
        (
            "https://dev.azure.com/o/p/_git/r",
            False,
            "abc123def",
            "commit",
            "https://dev.azure.com/o/p/_git/r?path=/a/b.py&version=GCabc123def",
        ),
    ],
)
def test_repo_view_url_per_forge(
    repo_url: str,
    is_dir: bool,  # noqa: FBT001 (boolean-type-hint-positional-argument)
    ref: str,
    ref_kind: RefKind,
    expected: str,
) -> None:
    assert (
        repo_view_url(
            repo_url=repo_url,
            ref=ref,
            ref_kind=ref_kind,
            repo_path="a/b.py",
            is_dir=is_dir,
        )
        == expected
    )


def test_repo_view_url_trailing_slash_normalized() -> None:
    assert (
        repo_view_url(
            repo_url="https://github.com/o/r/",
            ref="main",
            ref_kind="branch",
            repo_path="x",
            is_dir=False,
        )
        == "https://github.com/o/r/blob/main/x"
    )


def test_repo_view_url_git_suffix_stripped() -> None:
    assert (
        repo_view_url(
            repo_url="https://github.com/o/r.git",
            ref="main",
            ref_kind="branch",
            repo_path="x",
            is_dir=False,
        )
        == "https://github.com/o/r/blob/main/x"
    )


@pytest.mark.parametrize(
    ("repo_url", "expected_base_blob"),
    [
        (
            "https://github.com/o/r?tab=readme",
            "https://github.com/o/r/blob/main/x",
        ),
        (
            "https://github.com/o/r#readme",
            "https://github.com/o/r/blob/main/x",
        ),
        (
            "https://github.com/o/r.git?foo=bar",
            "https://github.com/o/r/blob/main/x",
        ),
        (
            "https://dev.azure.com/o/p/_git/r?foo=bar",
            "https://dev.azure.com/o/p/_git/r?path=/x&version=GBmain",
        ),
    ],
)
def test_repo_view_url_normalizes_repo_url(repo_url: str, expected_base_blob: str) -> None:
    assert (
        repo_view_url(
            repo_url=repo_url,
            ref="main",
            ref_kind="branch",
            repo_path="x",
            is_dir=False,
        )
        == expected_base_blob
    )


def test_repo_view_url_non_url_base_with_explicit_forge() -> None:
    assert (
        repo_view_url(
            repo_url="scm.internal.example/o/r.git",
            ref="main",
            ref_kind="branch",
            repo_path="x",
            is_dir=False,
            forge="github",
        )
        == "scm.internal.example/o/r/blob/main/x"
    )


def test_repo_view_url_non_url_base_without_git_suffix() -> None:
    assert (
        repo_view_url(
            repo_url="scm.internal.example/o/r",
            ref="main",
            ref_kind="branch",
            repo_path="x",
            is_dir=False,
            forge="github",
        )
        == "scm.internal.example/o/r/blob/main/x"
    )


def test_repo_view_url_preserves_non_default_port() -> None:
    assert (
        repo_view_url(
            repo_url="https://github.example.com:8443/o/r",
            ref="main",
            ref_kind="branch",
            repo_path="x",
            is_dir=False,
        )
        == "https://github.example.com:8443/o/r/blob/main/x"
    )


def test_repo_view_url_explicit_forge_override() -> None:
    # Unknown host, but the forge is forced.
    assert (
        repo_view_url(
            repo_url="https://scm.internal/o/r",
            ref="dev",
            ref_kind="branch",
            repo_path="x.py",
            is_dir=False,
            forge="gitlab",
        )
        == "https://scm.internal/o/r/-/blob/dev/x.py"
    )


def test_repo_view_url_unknown_host_returns_none() -> None:
    assert (
        repo_view_url(
            repo_url="https://example.com/o/r",
            ref="main",
            ref_kind="branch",
            repo_path="x",
            is_dir=False,
        )
        is None
    )


def test_supported_forges_contains_expected() -> None:
    assert set(SUPPORTED_FORGES) == {"github", "gitlab", "bitbucket", "gitea", "azure"}


@pytest.mark.parametrize(
    ("ref_kind", "expected"),
    [
        ("branch", "branch"),
        ("commit", "commit"),
        ("tag", "tag"),
    ],
)
def test_gitea_ref_segment(ref_kind: RefKind, expected: str) -> None:
    assert _gitea_ref_segment(ref_kind) == expected


@pytest.mark.parametrize(
    ("ref_kind", "expected"),
    [
        ("branch", "GB"),
        ("commit", "GC"),
        ("tag", "GT"),
    ],
)
def test_azure_version_prefix(ref_kind: RefKind, expected: str) -> None:
    assert _azure_version_prefix(ref_kind) == expected


def test_repo_view_url_invalid_explicit_forge_raises() -> None:
    with pytest.raises(ValueError, match="unsupported forge 'unknown'"):
        repo_view_url(
            repo_url="https://github.com/o/r",
            ref="main",
            ref_kind="branch",
            repo_path="x",
            is_dir=False,
            forge="unknown",
        )


_REF_ENCODING_CASES: list[tuple[str, str]] = [
    ("feature/foo", "feature/foo"),
    ("release candidate", "release%20candidate"),
    ("bugfix/foo#123", "bugfix/foo%23123"),
    ("topic?draft", "topic%3Fdraft"),
    ("v1.0.0+build", "v1.0.0%2Bbuild"),
    ("références", "r%C3%A9f%C3%A9rences"),
]

_PATH_FORGE_URL_TEMPLATES: list[tuple[str, str, str]] = [
    ("github", "https://github.com/o/r", "https://github.com/o/r/blob/{ref}/a/b.py"),
    ("gitlab", "https://gitlab.com/o/r", "https://gitlab.com/o/r/-/blob/{ref}/a/b.py"),
    (
        "bitbucket",
        "https://bitbucket.org/o/r",
        "https://bitbucket.org/o/r/src/{ref}/a/b.py",
    ),
    (
        "gitea",
        "https://codeberg.org/o/r",
        "https://codeberg.org/o/r/src/branch/{ref}/a/b.py",
    ),
]


@pytest.mark.parametrize(("ref", "encoded_ref"), _REF_ENCODING_CASES)
@pytest.mark.parametrize(("forge", "repo_url", "url_template"), _PATH_FORGE_URL_TEMPLATES)
def test_repo_view_url_encodes_ref_per_forge(
    forge: str,
    repo_url: str,
    url_template: str,
    ref: str,
    encoded_ref: str,
) -> None:
    expected = url_template.format(ref=encoded_ref)
    assert (
        repo_view_url(
            repo_url=repo_url,
            ref=ref,
            ref_kind="branch",
            repo_path="a/b.py",
            is_dir=False,
            forge=forge,
        )
        == expected
    )


_AZURE_REF_ENCODING_CASES: list[tuple[str, str]] = [
    ("feature/foo", "GBfeature%2Ffoo"),
    ("release candidate", "GBrelease%20candidate"),
    ("bugfix/foo#123", "GBbugfix%2Ffoo%23123"),
    ("topic?draft", "GBtopic%3Fdraft"),
    ("v1.0.0+build", "GBv1.0.0%2Bbuild"),
    ("références", "GBr%C3%A9f%C3%A9rences"),
]


@pytest.mark.parametrize(("ref", "encoded_version"), _AZURE_REF_ENCODING_CASES)
def test_repo_view_url_azure_ref_encoding_unchanged(ref: str, encoded_version: str) -> None:
    """Azure already percent-encodes the version query parameter."""
    assert (
        repo_view_url(
            repo_url="https://dev.azure.com/o/p/_git/r",
            ref=ref,
            ref_kind="branch",
            repo_path="a/b.py",
            is_dir=False,
        )
        == f"https://dev.azure.com/o/p/_git/r?path=/a/b.py&version={encoded_version}"
    )
