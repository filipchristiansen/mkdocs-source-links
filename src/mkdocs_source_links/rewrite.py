"""Rewrite ../ markdown links to forge view URLs."""

from __future__ import annotations

import re
from pathlib import Path

from .urls import repo_view_url

# Single left-to-right scan matching, in order: a fenced code block, an inline code span, or a
# ``](../path)`` / ``](../path#fragment)`` link. Matching code regions first means links inside
# code are consumed (and left untouched) before the link branch can see them.
_SCAN = re.compile(
    r"""
    (?P<fence>                                  # fenced code block
        ^[ \t]*(?P<fence_marker>`{3,}|~{3,})    # opening fence (``` or ~~~, optionally indented)
        [^\n]*\n                                # info string + newline
        [\s\S]*?                                # body (lazy, spans lines)
        ^[ \t]*(?P=fence_marker)[ \t]*$         # closing fence (same marker)
    )
    | (?P<inline>(?P<backticks>`+)[\s\S]*?(?P=backticks))      # inline code span
    | \]\(\s*                                                  # the link: ](
        (?:
            <(?P<path_a>\.\./[^>\s\#]+)(?P<frag_a>\#[^>]*)?>   # angle-bracket destination
          | (?P<path>\.\./[^)\s\#]+)(?P<frag>\#[^)\s]*)?       # bare destination
        )
        (?:\s+(?P<title>"[^"]*"|'[^']*'|\([^)]*\)))?           # optional title
      \s*\)
    """,
    re.MULTILINE | re.VERBOSE,
)


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
    forge: str | None = None,
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
    forge : str | None
        Explicit forge name; when ``None`` the forge is autodetected from ``repo_url``.

    Returns
    -------
    str
        Markdown with matching parent-directory links rewritten to forge URLs.

    Notes
    -----
    Directory targets use ``tree`` URLs; file targets use ``blob`` URLs (on forges that
    distinguish them). URL fragments (``#anchor``) and link titles are preserved, and
    angle-bracket destinations (``](<../x>)``) are supported. Links inside fenced code blocks
    and inline code spans are left unchanged.
    """

    def repl(match: re.Match[str]) -> str:
        path_part = match.group("path") or match.group("path_a")
        if path_part is None:
            # Matched a fenced code block or inline code span: leave it untouched.
            return match.group(0)
        fragment = match.group("frag") or match.group("frag_a") or ""
        title = match.group("title")
        # path_part always starts with "../" (guaranteed by the link branch of _SCAN).
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

        url = repo_view_url(
            repo_url=repo_url,
            branch=branch,
            repo_path=repo_path,
            is_dir=is_dir,
            forge=forge,
        )
        if url is None:
            return match.group(0)
        title_suffix = f" {title}" if title else ""
        return f"]({url}{fragment}{title_suffix})"

    return _SCAN.sub(repl, markdown)
