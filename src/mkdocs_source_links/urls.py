"""Forge view URL builder (host-agnostic API, GitHub v1)."""

from __future__ import annotations


def repo_view_url(
    *,
    repo_url: str,
    branch: str,
    repo_path: str,
    is_dir: bool,
) -> str | None:
    """Build a forge view URL, or None if the host is unsupported (v1: GitHub only)."""
    kind = "tree" if is_dir else "blob"
    if "github.com" in repo_url:
        return f"{repo_url.rstrip('/')}/{kind}/{branch}/{repo_path}"
    return None
