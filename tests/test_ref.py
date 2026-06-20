"""Tests for git ref resolution (branch, commit, and tag pin)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

from mkdocs_source_links.ref import ResolvedViewRef, ViewRef, _git_run, resolve_view_ref


def test_resolve_view_ref_branch_pin() -> None:
    resolved = resolve_view_ref(pin="branch", repo_root=Path("/repo"), branch="main")
    assert resolved == ResolvedViewRef(
        ViewRef("main", "branch"), used_fallback=False, requested_pin="branch"
    )


def test_resolve_view_ref_commit_pin(git_repo: tuple[Path, str]) -> None:
    root, sha = git_repo

    resolved = resolve_view_ref(pin="commit", repo_root=root, branch="main")
    assert resolved.view_ref == ViewRef(sha, "commit")
    assert resolved.used_fallback is False


def test_resolve_view_ref_commit_fallback_when_not_a_repo(tmp_path: Path) -> None:
    resolved = resolve_view_ref(pin="commit", repo_root=tmp_path, branch="develop")
    assert resolved.view_ref == ViewRef("develop", "branch")
    assert resolved.used_fallback is True


def test_resolve_view_ref_commit_fallback_when_git_fails(tmp_path: Path) -> None:
    with patch("mkdocs_source_links.ref.subprocess.run", side_effect=OSError("no git")):
        resolved = resolve_view_ref(pin="commit", repo_root=tmp_path, branch="main")
    assert resolved.view_ref == ViewRef("main", "branch")
    assert resolved.used_fallback is True


def test_resolve_view_ref_commit_fallback_on_empty_sha(tmp_path: Path) -> None:
    with patch(
        "mkdocs_source_links.ref.subprocess.run",
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="  \n"),
    ):
        resolved = resolve_view_ref(pin="commit", repo_root=tmp_path, branch="main")
    assert resolved.view_ref == ViewRef("main", "branch")
    assert resolved.used_fallback is True


def test_resolve_view_ref_commit_fallback_on_called_process_error(tmp_path: Path) -> None:
    with patch(
        "mkdocs_source_links.ref.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "git"),
    ):
        resolved = resolve_view_ref(pin="commit", repo_root=tmp_path, branch="main")
    assert resolved.view_ref == ViewRef("main", "branch")
    assert resolved.used_fallback is True


def test_resolve_view_ref_tag_pin_at_exact_tag(
    git_repo: tuple[Path, str],
    git_exe: str,
) -> None:
    root, _sha = git_repo
    subprocess.run([git_exe, "tag", "v1.0.0"], cwd=root, check=True)

    resolved = resolve_view_ref(pin="tag", repo_root=root, branch="main")
    assert resolved.view_ref == ViewRef("v1.0.0", "tag")
    assert resolved.used_fallback is False


def test_resolve_view_ref_tag_pin_fallback_when_not_on_tag(
    git_repo: tuple[Path, str],
    git_exe: str,
) -> None:
    root, _sha = git_repo
    subprocess.run([git_exe, "tag", "v1.0.0"], cwd=root, check=True)
    (root / "f").write_text("y\n")
    subprocess.run([git_exe, "add", "f"], cwd=root, check=True)
    subprocess.run([git_exe, "commit", "-m", "second"], cwd=root, check=True)

    resolved = resolve_view_ref(pin="tag", repo_root=root, branch="main")
    assert resolved.view_ref == ViewRef("main", "branch")
    assert resolved.used_fallback is True


def test_resolve_view_ref_tag_pin_fallback_when_not_a_repo(tmp_path: Path) -> None:
    resolved = resolve_view_ref(pin="tag", repo_root=tmp_path, branch="develop")
    assert resolved.view_ref == ViewRef("develop", "branch")
    assert resolved.used_fallback is True


def test_resolve_view_ref_tag_pin_fallback_when_git_fails(tmp_path: Path) -> None:
    with patch("mkdocs_source_links.ref.subprocess.run", side_effect=OSError("no git")):
        resolved = resolve_view_ref(pin="tag", repo_root=tmp_path, branch="main")
    assert resolved.view_ref == ViewRef("main", "branch")
    assert resolved.used_fallback is True


def test_git_run_returns_none_on_timeout(tmp_path: Path) -> None:
    with patch(
        "mkdocs_source_links.ref.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="git", timeout=10),
    ):
        assert _git_run(tmp_path, "rev-parse", "HEAD") is None


def test_resolve_view_ref_commit_fallback_on_git_timeout(tmp_path: Path) -> None:
    with patch(
        "mkdocs_source_links.ref.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="git", timeout=10),
    ):
        resolved = resolve_view_ref(pin="commit", repo_root=tmp_path, branch="main")
    assert resolved.view_ref == ViewRef("main", "branch")
    assert resolved.used_fallback is True


def test_git_run_returns_none_when_git_unavailable(tmp_path: Path) -> None:
    with patch("mkdocs_source_links.ref._GIT", None):
        assert _git_run(tmp_path, "rev-parse", "HEAD") is None
        commit = resolve_view_ref(pin="commit", repo_root=tmp_path, branch="main")
        assert commit.view_ref == ViewRef("main", "branch")
        assert commit.used_fallback is True
        tag = resolve_view_ref(pin="tag", repo_root=tmp_path, branch="main")
        assert tag.view_ref == ViewRef("main", "branch")
        assert tag.used_fallback is True
