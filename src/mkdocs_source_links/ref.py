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


class ResolvedViewRef(NamedTuple):
    """Result of resolving ``pin`` to a :class:`ViewRef`, with fallback diagnostics."""

    view_ref: ViewRef
    used_fallback: bool
    requested_pin: str


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


def resolve_view_ref(*, pin: str, repo_root: Path, branch: str) -> ResolvedViewRef:
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
    ResolvedViewRef
        Resolved ref and kind for URL building, plus whether a ``commit``/``tag`` pin fell back to
        the branch.
    """
    if pin == "branch":
        return ResolvedViewRef(ViewRef(branch, "branch"), used_fallback=False, requested_pin=pin)
    if _GIT is None:
        return ResolvedViewRef(
            ViewRef(branch, "branch"),
            used_fallback=True,
            requested_pin=pin,
        )
    if pin == "tag":
        tag = _git_exact_tag(repo_root)
        if tag is not None:
            return ResolvedViewRef(ViewRef(tag, "tag"), used_fallback=False, requested_pin=pin)
        return ResolvedViewRef(
            ViewRef(branch, "branch"),
            used_fallback=True,
            requested_pin=pin,
        )
    sha = _git_head_sha(repo_root)
    if sha is not None:
        return ResolvedViewRef(ViewRef(sha, "commit"), used_fallback=False, requested_pin=pin)
    return ResolvedViewRef(
        ViewRef(branch, "branch"),
        used_fallback=True,
        requested_pin=pin,
    )
