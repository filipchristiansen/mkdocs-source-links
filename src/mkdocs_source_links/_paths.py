"""Resolve ``../`` documentation links to repository-root-relative paths."""

from __future__ import annotations

import os
from pathlib import Path


def _is_within(*, target: Path, root: Path) -> bool:
    """Return whether ``target`` lies inside the already-resolved repository ``root``.

    Parameters
    ----------
    target : Path
        Absolute, resolved path to a file or directory.
    root : Path
        Resolved repository root the path should be checked against.

    Returns
    -------
    bool
        ``True`` when ``target`` is ``root`` or a descendant of it, ``False`` otherwise.
    """
    try:
        target.relative_to(root)
    except ValueError:
        return False
    return True


def resolve_parent_href(
    *,
    page_abs_path: Path,
    href: str,
    repo_root: Path,
) -> tuple[str, Path] | None:
    """Resolve a ``../`` href to a repo-relative POSIX path and absolute target path."""
    if not href.startswith("../"):
        return None
    # Resolve the repository root once; the same value drives both the inside-repo check and the
    # relative-path base below.
    root = repo_root.resolve()
    # Resolve the page's directory before the lexical join so the relative-path base shares a
    # real prefix with the resolved root (e.g. when the root is reached via a symlinked component
    # like macOS /tmp -> /private/tmp). The final href component stays lexical, so a symlinked
    # target keeps the name written in the link.
    lexical = page_abs_path.parent.resolve() / href
    resolved = lexical.resolve()
    if not _is_within(target=resolved, root=root):
        return None
    repo_rel = Path(
        os.path.relpath(
            os.path.normpath(str(lexical)),
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
    resolved = resolve_parent_href(page_abs_path=page_abs_path, href=href, repo_root=repo_root)
    return resolved[0] if resolved is not None else None
