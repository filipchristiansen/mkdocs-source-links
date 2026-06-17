"""Translate canonical line-number URL fragments to forge-specific syntax."""

from __future__ import annotations

import re

_LINE_FRAGMENT = re.compile(r"^#L(\d+)(?:-L(\d+))?$")


def translate_line_fragment(fragment: str, *, forge: str) -> str:
    """Translate a canonical ``#L`` line fragment to forge-specific syntax.

    Canonical input uses ``#L10`` for a single line and ``#L10-L20`` for a range. Non-line
    fragments (for example ``#section``) are returned unchanged. Azure DevOps does not support
    hash-based line anchors in view URLs, so line fragments are dropped for that forge.

    Parameters
    ----------
    fragment : str
        URL fragment from the markdown link, including the leading ``#``, or an empty string.
    forge : str
        Forge name from :data:`~mkdocs_source_links.urls.SUPPORTED_FORGES`.

    Returns
    -------
    str
        Forge-specific fragment, the original fragment when it is not a line anchor, or an empty
        string for Azure line anchors.
    """
    if not fragment:
        return fragment
    match = _LINE_FRAGMENT.match(fragment)
    if match is None:
        return fragment
    start = match.group(1)
    end = match.group(2)
    if forge == "azure":
        return ""
    if forge == "gitlab":
        return f"#L{start}-{end}" if end else f"#L{start}"
    if forge == "bitbucket":
        return f"#lines-{start}:{end}" if end else f"#lines-{start}"
    return f"#L{start}-L{end}" if end else f"#L{start}"
