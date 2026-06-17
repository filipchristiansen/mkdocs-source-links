"""Tests for git ref resolution (branch vs commit pin)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

from mkdocs_source_links.ref import resolve_view_ref


def test_resolve_view_ref_branch_pin() -> None:
    ref, kind = resolve_view_ref(pin="branch", repo_root=Path("/repo"), branch="main")
    assert ref == "main"
    assert kind == "branch"


def test_resolve_view_ref_commit_pin(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_path, check=True)
    (tmp_path / "f").write_text("x\n")
    subprocess.run(["git", "add", "f"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True)
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
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
