"""Resolve git branch for forge URLs from MkDocs config."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def resolve_branch(
    *,
    plugin_branch: str | None,
    extra: Mapping[str, Any],
    edit_uri: str | None,
) -> str:
    """Resolve the git branch name used in forge view URLs.

    Branch resolution follows MkDocs and plugin configuration in priority order: explicit plugin
    ``branch``, then ``extra.git_branch``, then the branch parsed from ``edit_uri``, then ``main``.

    Parameters
    ----------
    plugin_branch : str | None
        Value of the plugin's ``branch`` config option, if set.
    extra : Mapping[str, Any]
        MkDocs ``extra`` mapping; ``git_branch`` is consulted when present.
    edit_uri : str | None
        MkDocs ``edit_uri``; the segment after ``edit/`` or ``blob/`` is used as the branch name
        when present. GitLab-style ``-/edit/<branch>/…`` paths are supported.

    Returns
    -------
    str
        Branch name for forge URLs.
    """
    if plugin_branch:
        return plugin_branch
    if branch := extra.get("git_branch"):
        return str(branch)
    if edit_uri:
        parts = edit_uri.strip("/").split("/")
        if len(parts) >= 3 and parts[0] == "-" and parts[1] in ("edit", "blob"):
            return parts[2]
        if len(parts) >= 2 and parts[0] in ("edit", "blob"):
            return parts[1]
    return "main"
