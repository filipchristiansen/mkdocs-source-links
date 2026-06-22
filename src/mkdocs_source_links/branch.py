"""Resolve git branch for forge URLs from MkDocs config."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from mkdocs.plugins import get_plugin_logger

log = get_plugin_logger(__name__)


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
        Value of the plugin's ``branch`` config option, if set. An empty or whitespace-only value
        is ignored with a warning, falling back to ``extra.git_branch``, ``edit_uri``, or ``main``.
    extra : Mapping[str, Any]
        MkDocs ``extra`` mapping; ``git_branch`` is consulted when set (not ``None``). A non-string
        ``git_branch`` is coerced with ``str()`` and logs a build warning. An empty or
        whitespace-only ``git_branch`` is ignored with a warning, falling back to ``edit_uri`` or
        ``main``.
    edit_uri : str | None
        MkDocs ``edit_uri``; the segment after ``edit/``, ``blob/``, or Bitbucket ``src/`` is used
        as the branch name when present. GitLab-style ``-/edit/<branch>/…`` paths are supported.

    Returns
    -------
    str
        Branch name for forge URLs.
    """
    if plugin_branch is not None:
        if plugin_branch.strip():
            return plugin_branch
        log.warning(
            "plugin 'branch' is set but empty; ignoring it and falling back "
            "to extra.git_branch, edit_uri, or 'main'.",
        )
    if (branch := extra.get("git_branch")) is not None:
        if not isinstance(branch, str):
            log.warning(
                "extra.git_branch should be a string; got %r (%s). Coercing with str().",
                branch,
                type(branch).__name__,
            )
            return str(branch)
        if branch.strip():
            return branch
        log.warning(
            "extra.git_branch is set but empty; ignoring it and falling back "
            "to edit_uri or 'main'.",
        )
    if edit_uri:
        parts = edit_uri.strip("/").split("/")
        if len(parts) >= 3 and parts[0] == "-" and parts[1] in ("edit", "blob"):
            return parts[2]
        if len(parts) >= 2 and parts[0] in ("edit", "blob", "src"):
            return parts[1]
    return "main"
