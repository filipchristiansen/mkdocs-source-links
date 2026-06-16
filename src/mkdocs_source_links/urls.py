"""Forge view URL builders with host autodetection.

Supports GitHub, GitLab, Bitbucket Cloud, Gitea/Forgejo (incl. Codeberg), and Azure DevOps.
Public forge hosts are detected automatically; self-hosted instances on non-obvious domains can be
selected with an explicit forge name.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import NamedTuple
from urllib.parse import urlsplit


class _ForgeRequest(NamedTuple):
    base: str
    branch: str
    repo_path: str
    is_dir: bool


def _github_url(req: _ForgeRequest) -> str:
    """Build a GitHub blob/tree URL."""
    kind = "tree" if req.is_dir else "blob"
    return f"{req.base}/{kind}/{req.branch}/{req.repo_path}"


def _gitlab_url(req: _ForgeRequest) -> str:
    """Build a GitLab blob/tree URL."""
    kind = "tree" if req.is_dir else "blob"
    return f"{req.base}/-/{kind}/{req.branch}/{req.repo_path}"


def _bitbucket_url(req: _ForgeRequest) -> str:
    """Build a Bitbucket Cloud src URL (files and directories share the same path)."""
    return f"{req.base}/src/{req.branch}/{req.repo_path}"


def _gitea_url(req: _ForgeRequest) -> str:
    """Build a Gitea/Forgejo src/branch URL (files and directories share the same path)."""
    return f"{req.base}/src/branch/{req.branch}/{req.repo_path}"


def _azure_url(req: _ForgeRequest) -> str:
    """Build an Azure DevOps view URL using the path/version query parameters."""
    return f"{req.base}?path=/{req.repo_path}&version=GB{req.branch}"


_BUILDERS: dict[str, Callable[[_ForgeRequest], str]] = {
    "github": _github_url,
    "gitlab": _gitlab_url,
    "bitbucket": _bitbucket_url,
    "gitea": _gitea_url,
    "azure": _azure_url,
}

#: Forge names accepted by the plugin's ``forge`` option.
SUPPORTED_FORGES: tuple[str, ...] = tuple(_BUILDERS)

# Exact public hosts mapped to their forge.
_KNOWN_HOSTS = {
    "github.com": "github",
    "gitlab.com": "gitlab",
    "bitbucket.org": "bitbucket",
    "codeberg.org": "gitea",
    "dev.azure.com": "azure",
}

# Substring hints for self-hosted instances (used only when the host is not a known public host).
_HOST_HINTS = (
    ("github", "github"),
    ("gitlab", "gitlab"),
    ("gitea", "gitea"),
    ("forgejo", "gitea"),
    ("codeberg", "gitea"),
    ("bitbucket", "bitbucket"),
)


def detect_forge(repo_url: str) -> str | None:
    """Identify the git forge that hosts a repository URL.

    Detection first matches well-known public hosts exactly, then falls back to substring hints on
    the hostname so self-hosted instances (for example GitHub Enterprise at ``github.example.com``)
    are recognized. Ambiguous custom domains return ``None`` and should be configured explicitly.

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
        if needle in host:
            return forge
    return None


def repo_view_url(
    *,
    repo_url: str,
    branch: str,
    repo_path: str,
    is_dir: bool,
    forge: str | None = None,
) -> str | None:
    """Build a git-forge view URL for a path inside the repository.

    Parameters
    ----------
    repo_url : str
        Forge repository URL from ``mkdocs.yml``.
    branch : str
        Git branch name to embed in the URL.
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
    """
    forge_name = forge or detect_forge(repo_url)
    if forge_name is None:
        return None
    request = _ForgeRequest(
        base=repo_url.rstrip("/"),
        branch=branch,
        repo_path=repo_path,
        is_dir=is_dir,
    )
    return _BUILDERS[forge_name](request)
