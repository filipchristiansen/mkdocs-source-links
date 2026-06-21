"""Error- and success-path tests for the CI helper shell scripts."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from git_utils import init_git_repo

_VERIFY_TAG_VERSION = Path(".github/scripts/verify-tag-version.sh").resolve()
_CHECK_DCO = Path(".github/scripts/check-dco.sh").resolve()
_BASH = shutil.which("bash") or "/bin/bash"

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="CI helper scripts run on the Linux/macOS runners only",
)


def _bash_available() -> bool:
    return shutil.which("bash") is not None


def _env_with(**overrides: str) -> dict[str, str]:
    env = os.environ.copy()
    env.update(overrides)
    return env


def _run_verify_tag_version(cwd: Path, tag: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [_BASH, str(_VERIFY_TAG_VERSION)],
        cwd=cwd,
        env=_env_with(TAG=tag),
        capture_output=True,
        text=True,
        check=False,
    )


def test_verify_tag_version_matches(tmp_path: Path) -> None:
    if not _bash_available():
        pytest.skip("bash not available")
    (tmp_path / "pyproject.toml").write_text('version = "1.2.3"\n')

    result = _run_verify_tag_version(tmp_path, "v1.2.3")

    assert result.returncode == 0, result.stderr
    assert "matches pyproject.toml version" in result.stdout


def test_verify_tag_version_mismatch_fails(tmp_path: Path) -> None:
    if not _bash_available():
        pytest.skip("bash not available")
    (tmp_path / "pyproject.toml").write_text('version = "1.2.3"\n')

    result = _run_verify_tag_version(tmp_path, "v9.9.9")

    assert result.returncode != 0
    assert "does not match pyproject.toml version" in result.stdout


def test_verify_tag_version_missing_version_fails(tmp_path: Path) -> None:
    if not _bash_available():
        pytest.skip("bash not available")
    (tmp_path / "pyproject.toml").write_text('name = "x"\n')

    result = _run_verify_tag_version(tmp_path, "v1.2.3")

    assert result.returncode != 0


def _commit(repo: Path, git_exe: str, message: str, *, signoff: bool) -> str:
    (repo / "f").write_text(f"{message}\n")
    subprocess.run([git_exe, "add", "-A"], cwd=repo, check=True)
    args = [git_exe, "commit"]
    if signoff:
        args.append("-s")
    args.extend(["-m", message])
    subprocess.run(args, cwd=repo, check=True)
    return subprocess.run(
        [git_exe, "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _run_check_dco(repo: Path, base: str, head: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [_BASH, str(_CHECK_DCO)],
        cwd=repo,
        env=_env_with(BASE_SHA=base, HEAD_SHA=head),
        capture_output=True,
        text=True,
        check=False,
    )


def test_check_dco_fails_on_missing_signoff(tmp_path: Path, git_exe: str) -> None:
    if not _bash_available():
        pytest.skip("bash not available")
    base = init_git_repo(tmp_path, git_exe)
    head = _commit(tmp_path, git_exe, "unsigned change", signoff=False)

    result = _run_check_dco(tmp_path, base, head)

    assert result.returncode != 0
    assert "Missing or mismatched Signed-off-by" in result.stdout


def test_check_dco_passes_when_signed_off(tmp_path: Path, git_exe: str) -> None:
    if not _bash_available():
        pytest.skip("bash not available")
    base = init_git_repo(tmp_path, git_exe)
    head = _commit(tmp_path, git_exe, "signed change", signoff=True)

    result = _run_check_dco(tmp_path, base, head)

    assert result.returncode == 0, result.stdout
    assert "All commits are signed off." in result.stdout
