"""Resolve git branch for forge URLs from MkDocs config."""

from __future__ import annotations


def resolve_branch(
    *,
    plugin_branch: str | None,
    extra: dict,
    edit_uri: str | None,
) -> str:
    """Return branch name using plugin config, extra.git_branch, edit_uri, or main."""
    if plugin_branch:
        return plugin_branch
    if branch := extra.get("git_branch"):
        return str(branch)
    if edit_uri:
        parts = edit_uri.strip("/").split("/")
        if len(parts) >= 2 and parts[0] in ("edit", "blob"):
            return parts[1]
    return "main"
