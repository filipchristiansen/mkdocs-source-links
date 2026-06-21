"""Forge view URL builders with host autodetection.

Supports GitHub, GitLab, Bitbucket Cloud, Gitea/Forgejo (incl. Codeberg), and Azure DevOps.
Public forge hosts are detected automatically; self-hosted instances on non-obvious domains can be
selected with an explicit forge name.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import NamedTuple
from urllib.parse import quote, urlsplit, urlunsplit

from .ref import RefKind


class _ForgeRequest(NamedTuple):
    base: str
    ref: str
    ref_kind: RefKind
    repo_path: str
    is_dir: bool


_GITEA_REF_SEGMENTS: dict[RefKind, str] = {
    "branch": "branch",
    "commit": "commit",
    "tag": "tag",
}

_AZURE_VERSION_PREFIXES: dict[RefKind, str] = {
    "branch": "GB",
    "commit": "GC",
    "tag": "GT",
}

# Exact public hosts mapped to their forge.
_KNOWN_HOSTS = {
    "github.com": "github",
    "gitlab.com": "gitlab",
    "bitbucket.org": "bitbucket",
    "codeberg.org": "gitea",
    "dev.azure.com": "azure",
}

# Substring hints for self-hosted instances (used only when the host is not a known public host).
# Bitbucket Cloud is only at bitbucket.org; self-hosted Bitbucket Server/DC is not supported.
_HOST_HINTS = (
    ("github", "github"),
    ("gitlab", "gitlab"),
    ("gitea", "gitea"),
    ("forgejo", "gitea"),
    ("codeberg", "gitea"),
)


def _normalize_repo_base(repo_url: str) -> str:
    """Normalize a repository URL for forge view URL building.

    Drops query and fragment first, then strips a trailing slash and ``.git`` suffix from the path
    (order matters — ``repo.git?foo=bar`` must not leave ``.git`` after query removal).
    """
    parsed = urlsplit(repo_url)
    if not parsed.scheme or not parsed.hostname:
        base = repo_url.rstrip("/")
        if base.endswith(".git"):
            return base[:-4]
        return base
    netloc = parsed.netloc
    path = parsed.path.rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    return urlunsplit((parsed.scheme, netloc, path, "", "")).rstrip("/")


def _quote_part(part: str) -> str:
    """Percent-encode a URL path part, preserving internal slashes."""
    return quote(part, safe="/")


def _github_url(req: _ForgeRequest) -> str:
    """Build a GitHub blob/tree URL."""
    kind = "tree" if req.is_dir else "blob"
    return f"{req.base}/{kind}/{_quote_part(req.ref)}/{_quote_part(req.repo_path)}"


def _gitlab_url(req: _ForgeRequest) -> str:
    """Build a GitLab blob/tree URL."""
    kind = "tree" if req.is_dir else "blob"
    return f"{req.base}/-/{kind}/{_quote_part(req.ref)}/{_quote_part(req.repo_path)}"


def _bitbucket_url(req: _ForgeRequest) -> str:
    """Build a Bitbucket Cloud src URL (files and directories share the same path)."""
    return f"{req.base}/src/{_quote_part(req.ref)}/{_quote_part(req.repo_path)}"


def _gitea_ref_segment(ref_kind: RefKind) -> str:
    """Return the Gitea/Forgejo ``src/`` path segment for a ref kind."""
    return _GITEA_REF_SEGMENTS[ref_kind]


def _gitea_url(req: _ForgeRequest) -> str:
    """Build a Gitea/Forgejo src URL (files and directories share the same path)."""
    kind = _gitea_ref_segment(req.ref_kind)
    return f"{req.base}/src/{kind}/{_quote_part(req.ref)}/{_quote_part(req.repo_path)}"


def _azure_version_prefix(ref_kind: RefKind) -> str:
    """Return the Azure DevOps version query prefix for a ref kind."""
    return _AZURE_VERSION_PREFIXES[ref_kind]


def _azure_url(req: _ForgeRequest) -> str:
    """Build an Azure DevOps view URL using the path/version query parameters."""
    path_param = quote(f"/{req.repo_path}", safe="/")
    version_param = quote(f"{_azure_version_prefix(req.ref_kind)}{req.ref}", safe="")
    return f"{req.base}?path={path_param}&version={version_param}"


_BUILDERS: dict[str, Callable[[_ForgeRequest], str]] = {
    "github": _github_url,
    "gitlab": _gitlab_url,
    "bitbucket": _bitbucket_url,
    "gitea": _gitea_url,
    "azure": _azure_url,
}

#: Forge names accepted by the plugin's ``forge`` option.
SUPPORTED_FORGES: tuple[str, ...] = tuple(_BUILDERS)


def _host_matches_hint(host: str, needle: str) -> bool:
    """Return whether ``needle`` is a complete dot-delimited label in ``host``.

    Matching whole labels only avoids false positives where the forge name is merely a substring of
    a label (for example ``my-github.com`` or ``notgitlab.com``); such ambiguous hosts return
    ``None`` from :func:`detect_forge` and need an explicit ``forge`` setting.
    """
    return needle in host.split(".")


def detect_forge(repo_url: str) -> str | None:
    """Identify the git forge that hosts a repository URL.

    Detection first matches well-known public hosts exactly, then falls back to hostname-label
    hints so self-hosted instances (for example GitHub Enterprise at ``github.example.com``) are
    recognized. Ambiguous custom domains return ``None`` and should be configured explicitly.

    Parameters
    ----------
    repo_url : str
        Repository URL from ``mkdocs.yml`` (``repo_url``).

    Returns
    -------
    str | None
        A forge name from :data:`SUPPORTED_FORGES`, or ``None`` if the host is unknown.
    """
    host = (urlsplit(repo_url).hostname or "").lower()
    if not host:
        return None
    if host in _KNOWN_HOSTS:
        return _KNOWN_HOSTS[host]
    if host.endswith(".visualstudio.com"):
        return "azure"
    for needle, forge in _HOST_HINTS:
        if _host_matches_hint(host, needle):
            return forge
    return None


def repo_view_url(
    *,
    repo_url: str,
    ref: str,
    ref_kind: RefKind,
    repo_path: str,
    is_dir: bool,
    forge: str | None = None,
) -> str | None:
    """Build a git-forge view URL for a path inside the repository.

    Parameters
    ----------
    repo_url : str
        Forge repository URL from ``mkdocs.yml``.
    ref : str
        Git branch name, tag name, or commit SHA to embed in the URL.
    ref_kind : RefKind
        Whether ``ref`` is a branch name, tag name, or commit SHA. Azure DevOps uses different
        version prefixes (``GB``, ``GT``, and ``GC``) depending on this value.
    repo_path : str
        Repo-root-relative POSIX path to the target file or directory.
    is_dir : bool
        Whether ``repo_path`` is a directory or a file. Forges that distinguish the two
        (GitHub, GitLab) use ``tree`` vs ``blob`` accordingly.
    forge : str | None
        Explicit forge name from :data:`SUPPORTED_FORGES`. When ``None``, the forge is
        autodetected from ``repo_url``.

    Returns
    -------
    str | None
        Forge view URL, or ``None`` if the forge could not be determined.

    Raises
    ------
    ValueError
        If ``forge`` is set to a name that is not in :data:`SUPPORTED_FORGES`.
    """
    forge_name = forge or detect_forge(repo_url)
    if forge_name is None:
        return None
    if forge_name not in _BUILDERS:
        msg = f"unsupported forge {forge_name!r}; expected one of {SUPPORTED_FORGES}"
        raise ValueError(msg)
    request = _ForgeRequest(
        base=_normalize_repo_base(repo_url),
        ref=ref,
        ref_kind=ref_kind,
        repo_path=repo_path,
        is_dir=is_dir,
    )
    return _BUILDERS[forge_name](request)
