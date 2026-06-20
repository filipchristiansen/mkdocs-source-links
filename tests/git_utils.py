"""Git helpers for tests that need real repositories."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def find_git() -> str | None:
    """Return the path to the git executable, or ``None`` if it is not installed."""
    return shutil.which("git")


def init_git_repo(root: Path, git: str) -> str:
    """Initialize a git repository under ``root`` with one commit.

    Parameters
    ----------
    root : Path
        Directory that becomes the repository root.
    git : str
        Path to the git executable.

    Returns
    -------
    str
        The HEAD commit SHA.
    """
    subprocess.run([git, "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run([git, "config", "user.email", "t@e.com"], cwd=root, check=True)
    subprocess.run([git, "config", "user.name", "T"], cwd=root, check=True)
    if not any(p.is_file() for p in root.rglob("*") if ".git" not in p.parts):
        (root / "f").write_text("x\n")
    subprocess.run([git, "add", "-A"], cwd=root, check=True)
    subprocess.run([git, "commit", "-m", "init"], cwd=root, check=True)
    return subprocess.run(
        [git, "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
