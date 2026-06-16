"""Rewrite ../ markdown links to forge view URLs."""

from __future__ import annotations

import re
from pathlib import Path

from .urls import repo_view_url

# ](../path) or ](../path#fragment) — repo files outside docs/
_REPO_PARENT_LINK = re.compile(r"\]\((\.\./[^)#]+)(#[^)]*)?\)")


def repo_relative_path(*, page_abs_path: Path, href: str, repo_root: Path) -> str | None:
    """Resolve a ../ link from a doc page to a repo-root-relative POSIX path."""
    if not href.startswith("../"):
        return None
    target = (page_abs_path.parent / href).resolve()
    try:
        return target.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return None


def rewrite_repo_parent_links(
    markdown: str,
    *,
    page_abs_path: Path,
    repo_root: Path,
    repo_url: str,
    branch: str,
) -> str:
    """Replace ](../…) markdown links with forge view URLs (source unchanged on disk)."""

    def repl(match: re.Match[str]) -> str:
        path_part = match.group(1)
        fragment = match.group(2) or ""
        repo_path = repo_relative_path(
            page_abs_path=page_abs_path,
            href=path_part,
            repo_root=repo_root,
        )
        if repo_path is None:
            return match.group(0)

        target = (page_abs_path.parent / path_part).resolve()
        if target.is_dir():
            is_dir = True
        elif target.is_file():
            is_dir = False
        else:
            return match.group(0)

        url = repo_view_url(
            repo_url=repo_url,
            branch=branch,
            repo_path=repo_path,
            is_dir=is_dir,
        )
        if url is None:
            return match.group(0)
        return f"]({url}{fragment})"

    return _REPO_PARENT_LINK.sub(repl, markdown)
