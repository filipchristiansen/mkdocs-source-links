"""Resolve git ref and ref kind for forge view URLs."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Literal, NamedTuple

RefKind = Literal["branch", "commit"]


class ViewRef(NamedTuple):
    """Git ref and kind for forge view URLs."""

    ref: str
    kind: RefKind


def resolve_view_ref(
    *,
    pin: str,
    repo_root: Path,
    branch: str,
) -> tuple[str, RefKind]:
    """Resolve the git ref and kind used in forge view URLs.

    When ``pin`` is ``commit``, the current HEAD SHA is resolved via ``git rev-parse``. If git is
    unavailable or ``repo_root`` is not a repository, the resolved branch is used instead.

    Parameters
    ----------
    pin : str
        Pin mode: ``branch`` or ``commit``.
    repo_root : Path
        Repository root passed to ``git -C``.
    branch : str
        Resolved branch name used when ``pin`` is ``branch`` or as a fallback for ``commit``.

    Returns
    -------
    tuple[str, RefKind]
        Ref string and kind (``branch`` or ``commit``) for URL building.
    """
    if pin != "commit":
        return branch, "branch"
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return branch, "branch"
    sha = result.stdout.strip()
    if not sha:
        return branch, "branch"
    return sha, "commit"
