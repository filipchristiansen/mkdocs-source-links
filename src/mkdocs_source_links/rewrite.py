"""Rewrite ../ markdown links to forge view URLs."""

from __future__ import annotations

import re
from pathlib import Path

from .urls import repo_view_url

# `](../path)` or `](../path#fragment)` — repo files outside docs/
_REPO_PARENT_LINK = re.compile(r"\]\((\.\./[^)#]+)(#[^)]*)?\)")


def _repo_relative(*, target: Path, repo_root: Path) -> str | None:
    """Express an absolute path relative to the repository root.

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


def repo_relative_path(*, page_abs_path: Path, href: str, repo_root: Path) -> str | None:
    """Resolve a ``../`` link from a doc page to a repo-root-relative POSIX path.

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
    if not href.startswith("../"):
        return None
    target = (page_abs_path.parent / href).resolve()
    return _repo_relative(target=target, repo_root=repo_root)


def rewrite_repo_parent_links(
    markdown: str,
    *,
    page_abs_path: Path,
    repo_root: Path,
    repo_url: str,
    branch: str,
) -> str:
    """Replace ``](../…)`` markdown links with git-forge view URLs.

    Only links whose target resolves to an existing file or directory inside ``repo_root`` are
    rewritten. Unsupported hosts, paths outside the repo, and missing targets are left unchanged.

    Parameters
    ----------
    markdown : str
        Markdown source text for a single documentation page.
    page_abs_path : Path
        Absolute path to the page's markdown file on disk.
    repo_root : Path
        Repository root used to resolve ``../`` targets and to build
        repo-relative paths for the forge URL.
    repo_url : str
        Forge repository URL from ``mkdocs.yml`` (for example a GitHub URL).
    branch : str
        Git branch name to embed in blob/tree URLs.

    Returns
    -------
    str
        Markdown with matching parent-directory links rewritten to forge URLs.

    Notes
    -----
    Directory targets use ``tree`` URLs; file targets use ``blob`` URLs.
    URL fragments (``#anchor``) are preserved. v1 supports GitHub only.
    """

    def repl(match: re.Match[str]) -> str:
        path_part = match.group(1)
        fragment = match.group(2) or ""
        # path_part always starts with "../" (guaranteed by _REPO_PARENT_LINK).
        target = (page_abs_path.parent / path_part).resolve()
        repo_path = _repo_relative(target=target, repo_root=repo_root)
        if repo_path is None:
            return match.group(0)

        if target.is_dir():
            is_dir = True
        elif target.is_file():
            is_dir = False
        else:
            return match.group(0)

        url = repo_view_url(repo_url=repo_url, branch=branch, repo_path=repo_path, is_dir=is_dir)
        if url is None:
            return match.group(0)
        return f"]({url}{fragment})"

    return _REPO_PARENT_LINK.sub(repl, markdown)
