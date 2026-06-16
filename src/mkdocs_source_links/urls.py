"""Forge view URL builder (host-agnostic API, GitHub v1)."""

from __future__ import annotations


def repo_view_url(
    *,
    repo_url: str,
    branch: str,
    repo_path: str,
    is_dir: bool,
) -> str | None:
    """Build a git-forge view URL for a path inside the repository.

    Parameters
    ----------
    repo_url : str
        Forge repository URL from ``mkdocs.yml`` (for example a GitHub URL).
    branch : str
        Git branch name to embed in the URL.
    repo_path : str
        Repo-root-relative POSIX path to the target file or directory.
    is_dir : bool
        Whether ``repo_path`` is a directory (``tree`` URL) or a file (``blob`` URL).

    Returns
    -------
    str | None
        Forge view URL, or ``None`` if the host is unsupported (v1 supports GitHub only).
    """
    kind = "tree" if is_dir else "blob"
    if "github.com" in repo_url:
        return f"{repo_url.rstrip('/')}/{kind}/{branch}/{repo_path}"
    return None
