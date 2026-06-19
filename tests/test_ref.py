"""Tests for git ref resolution (branch, commit, and tag pin)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from mkdocs_source_links.ref import _git_run, resolve_view_ref

_GIT = shutil.which("git")


def test_resolve_view_ref_branch_pin() -> None:
    ref, kind = resolve_view_ref(pin="branch", repo_root=Path("/repo"), branch="main")
    assert ref == "main"
    assert kind == "branch"


def test_resolve_view_ref_commit_pin(tmp_path: Path) -> None:
    if _GIT is None:
        return
    subprocess.run([_GIT, "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run([_GIT, "config", "user.email", "t@e.com"], cwd=tmp_path, check=True)
    subprocess.run([_GIT, "config", "user.name", "T"], cwd=tmp_path, check=True)
    (tmp_path / "f").write_text("x\n")
    subprocess.run([_GIT, "add", "f"], cwd=tmp_path, check=True)
    subprocess.run([_GIT, "commit", "-m", "init"], cwd=tmp_path, check=True)
    sha = subprocess.run(
        [_GIT, "rev-parse", "HEAD"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    ref, kind = resolve_view_ref(pin="commit", repo_root=tmp_path, branch="main")
    assert ref == sha
    assert kind == "commit"


def test_resolve_view_ref_commit_fallback_when_not_a_repo(tmp_path: Path) -> None:
    ref, kind = resolve_view_ref(pin="commit", repo_root=tmp_path, branch="develop")
    assert ref == "develop"
    assert kind == "branch"


def test_resolve_view_ref_commit_fallback_when_git_fails(tmp_path: Path) -> None:
    with patch("mkdocs_source_links.ref.subprocess.run", side_effect=OSError("no git")):
        ref, kind = resolve_view_ref(pin="commit", repo_root=tmp_path, branch="main")
    assert ref == "main"
    assert kind == "branch"


def test_resolve_view_ref_commit_fallback_on_empty_sha(tmp_path: Path) -> None:
    with patch(
        "mkdocs_source_links.ref.subprocess.run",
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="  \n"),
    ):
        ref, kind = resolve_view_ref(pin="commit", repo_root=tmp_path, branch="main")
    assert ref == "main"
    assert kind == "branch"


def test_resolve_view_ref_commit_fallback_on_called_process_error(tmp_path: Path) -> None:
    with patch(
        "mkdocs_source_links.ref.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "git"),
    ):
        ref, kind = resolve_view_ref(pin="commit", repo_root=tmp_path, branch="main")
    assert ref == "main"
    assert kind == "branch"


def _init_git_repo(tmp_path: Path) -> None:
    if _GIT is None:
        pytest.skip("git not available")
    subprocess.run([_GIT, "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run([_GIT, "config", "user.email", "t@e.com"], cwd=tmp_path, check=True)
    subprocess.run([_GIT, "config", "user.name", "T"], cwd=tmp_path, check=True)
    (tmp_path / "f").write_text("x\n")
    subprocess.run([_GIT, "add", "f"], cwd=tmp_path, check=True)
    subprocess.run([_GIT, "commit", "-m", "init"], cwd=tmp_path, check=True)


def test_resolve_view_ref_tag_pin_at_exact_tag(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    assert _GIT is not None
    subprocess.run([_GIT, "tag", "v1.0.0"], cwd=tmp_path, check=True)

    ref, kind = resolve_view_ref(pin="tag", repo_root=tmp_path, branch="main")
    assert ref == "v1.0.0"
    assert kind == "branch"


def test_resolve_view_ref_tag_pin_fallback_when_not_on_tag(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    assert _GIT is not None
    subprocess.run([_GIT, "tag", "v1.0.0"], cwd=tmp_path, check=True)
    (tmp_path / "f").write_text("y\n")
    subprocess.run([_GIT, "add", "f"], cwd=tmp_path, check=True)
    subprocess.run([_GIT, "commit", "-m", "second"], cwd=tmp_path, check=True)

    ref, kind = resolve_view_ref(pin="tag", repo_root=tmp_path, branch="main")
    assert ref == "main"
    assert kind == "branch"


def test_resolve_view_ref_tag_pin_fallback_when_not_a_repo(tmp_path: Path) -> None:
    ref, kind = resolve_view_ref(pin="tag", repo_root=tmp_path, branch="develop")
    assert ref == "develop"
    assert kind == "branch"


def test_resolve_view_ref_tag_pin_fallback_when_git_fails(tmp_path: Path) -> None:
    with patch("mkdocs_source_links.ref.subprocess.run", side_effect=OSError("no git")):
        ref, kind = resolve_view_ref(pin="tag", repo_root=tmp_path, branch="main")
    assert ref == "main"
    assert kind == "branch"


def test_git_run_returns_none_when_git_unavailable(tmp_path: Path) -> None:
    with patch("mkdocs_source_links.ref._GIT", None):
        assert _git_run(tmp_path, "rev-parse", "HEAD") is None
        assert resolve_view_ref(pin="commit", repo_root=tmp_path, branch="main") == (
            "main",
            "branch",
        )
        assert resolve_view_ref(pin="tag", repo_root=tmp_path, branch="main") == ("main", "branch")
