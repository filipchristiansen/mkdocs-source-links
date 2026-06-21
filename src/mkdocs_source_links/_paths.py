"""Resolve ``../`` documentation links to repository-root-relative paths."""

from __future__ import annotations

import os
from pathlib import Path


def _repo_relative(*, target: Path, repo_root: Path) -> str | None:
    """Express a resolved absolute path relative to the repository root.

    Parameters
    ----------
    target : Path
        Absolute, resolved path to a file or directory.
    repo_root : Path
        Repository root the path should be made relative to.

    Returns
    -------
    str | None
        ``target`` as a repo-root-relative POSIX path, or ``None`` if it lies outside
        ``repo_root``.
    """
    try:
        return target.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return None


def _resolve_parent_href(
    *,
    page_abs_path: Path,
    href: str,
    repo_root: Path,
) -> tuple[str, Path] | None:
    """Resolve a ``../`` href to a repo-relative POSIX path and absolute target path."""
    if not href.startswith("../"):
        return None
    root = repo_root.resolve()
    resolved = (page_abs_path.parent / href).resolve()
    if _repo_relative(target=resolved, repo_root=repo_root) is None:
        return None
    repo_rel = Path(
        os.path.relpath(
            os.path.normpath(str(page_abs_path.parent / href)),
            str(root),
        )
    ).as_posix()
    return repo_rel, resolved


def repo_relative_path(*, page_abs_path: Path, href: str, repo_root: Path) -> str | None:
    """Resolve a ``../`` link from a doc page to a repo-root-relative POSIX path.

    The returned path reflects the link text (lexical path). Symlink targets are not followed
    when building the forge URL path segment, but ``resolve()`` is still used to verify the
    target lies inside ``repo_root``.

    Parameters
    ----------
    page_abs_path : Path
        Absolute path to the page's markdown file on disk.
    href : str
        Link target as written in the markdown; only ``../`` targets are resolved.
    repo_root : Path
        Repository root used to resolve the target and build the relative path.

    Returns
    -------
    str | None
        Repo-root-relative POSIX path, or ``None`` if ``href`` is not a ``../`` link or resolves
        outside ``repo_root``.
    """
    resolved = _resolve_parent_href(page_abs_path=page_abs_path, href=href, repo_root=repo_root)
    return resolved[0] if resolved is not None else None
