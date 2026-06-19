"""Resolve git ref and ref kind for forge view URLs."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Literal, NamedTuple

RefKind = Literal["branch", "commit", "tag"]

_GIT = shutil.which("git")
_GIT_TIMEOUT = 10


class ViewRef(NamedTuple):
    """Git ref and kind for forge view URLs."""

    ref: str
    kind: RefKind


def _git_run(repo_root: Path, *args: str) -> str | None:
    """Run a git command in ``repo_root`` and return stripped stdout, or ``None`` on failure."""
    if _GIT is None:
        return None
    try:
        result = subprocess.run(  # noqa: S603 (subprocess-without-shell-equals-true)
            [_GIT, "-C", str(repo_root), *args],
            capture_output=True,
            text=True,
            check=True,
            timeout=_GIT_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    text = result.stdout.strip()
    return text or None


def _git_head_sha(repo_root: Path) -> str | None:
    """Return the current ``HEAD`` SHA, or ``None`` if git is unavailable or fails."""
    return _git_run(repo_root, "rev-parse", "HEAD")


def _git_exact_tag(repo_root: Path) -> str | None:
    """Return the tag name when ``HEAD`` is an exact tag, or ``None`` otherwise."""
    return _git_run(repo_root, "describe", "--tags", "--exact-match")


def resolve_view_ref(*, pin: str, repo_root: Path, branch: str) -> ViewRef:
    """Resolve the git ref and kind used in forge view URLs.

    When ``pin`` is ``commit``, the current HEAD SHA is resolved via ``git rev-parse``. When
    ``pin`` is ``tag``, an exact tag at ``HEAD`` is resolved via ``git describe --tags
    --exact-match``. If git is unavailable, times out, or lookup fails, the resolved branch is
    used instead (for ``commit`` and ``tag``).

    Parameters
    ----------
    pin : str
        Pin mode: ``branch``, ``commit``, or ``tag``.
    repo_root : Path
        Repository root passed to ``git -C``.
    branch : str
        Resolved branch name used when ``pin`` is ``branch`` or as a fallback for ``commit`` and
        ``tag``.

    Returns
    -------
    ViewRef
        Ref string and kind (``branch``, ``commit``, or ``tag``) for URL building.
    """
    if pin == "branch" or _GIT is None:
        return ViewRef(branch, "branch")
    if pin == "tag":
        tag = _git_exact_tag(repo_root)
        if tag is not None:
            return ViewRef(tag, "tag")
        return ViewRef(branch, "branch")
    sha = _git_head_sha(repo_root)
    if sha is not None:
        return ViewRef(sha, "commit")
    return ViewRef(branch, "branch")
