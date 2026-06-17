"""Resolve git ref and ref kind for forge view URLs."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Literal, NamedTuple

RefKind = Literal["branch", "commit"]

_GIT = shutil.which("git")


class ViewRef(NamedTuple):
    """Git ref and kind for forge view URLs."""

    ref: str
    kind: RefKind


def resolve_view_ref(
    *,
    pin: str,
    repo_root: Path,
    branch: str,
) -> ViewRef:
    """Resolve the git ref and kind used in forge view URLs.

    When ``pin`` is ``commit``, the current HEAD SHA is resolved via ``git rev-parse``. If git is
    unavailable, times out, or ``repo_root`` is not a repository, the resolved branch is used
    instead.

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
    ViewRef
        Ref string and kind (``branch`` or ``commit``) for URL building.
    """
    if pin != "commit" or _GIT is None:
        return ViewRef(branch, "branch")
    try:
        result = subprocess.run(  # noqa: S603 (subprocess-without-shell-equals-true)
            [_GIT, "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return ViewRef(branch, "branch")
    sha = result.stdout.strip()
    if not sha:
        return ViewRef(branch, "branch")
    return ViewRef(sha, "commit")
