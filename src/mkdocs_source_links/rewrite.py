"""Rewrite ../ markdown links to forge view URLs."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .anchors import translate_line_fragment
from .ref import ViewRef
from .urls import detect_forge, repo_view_url

# Single left-to-right scan matching, in order: a fenced code block, an inline code span, an
# inline image with a ``../`` destination, or a ``](../path)`` / ``](../path#fragment)`` link.
# Matching code regions and images first means links inside them are left untouched.
_SCAN = re.compile(
    r"""
    (?P<fence>                                  # fenced code block
        ^[ \t]*(?P<fence_marker>`{3,}|~{3,})    # opening fence (``` or ~~~, optionally indented)
        [^\n]*\n                                # info string + newline
        [\s\S]*?                                # body (lazy, spans lines)
        ^[ \t]*(?P=fence_marker)[ \t]*$         # closing fence (same marker)
    )
    | (?P<inline>(?P<backticks>`+)[\s\S]*?(?P=backticks))      # inline code span
    | (?P<image>!\[[^\]]*\]\(\s*                               # inline image with ../ dest
        (?:
            <(?P<img_path_a>\.\./[^>\#\n]+)(?P<img_frag_a>\#[^>\n]*)?>
          | (?P<img_path>\.\./[^)\s\#]+)(?P<img_frag>\#[^)\s]*)?
        )
        (?:\s+(?P<img_title>"[^"]*"|'[^']*'|\([^)]*\)))?
      \s*\))
    | \]\(\s*                                                  # the link: ](
        (?:
            <(?P<path_a>\.\./[^>\#\n]+)(?P<frag_a>\#[^>\n]*)?> # angle-bracket dest (allows spaces)
          | (?P<path>\.\./[^)\s\#]+)(?P<frag>\#[^)\s]*)?       # bare destination
        )
        (?:\s+(?P<title>"[^"]*"|'[^']*'|\([^)]*\)))?           # optional title
      \s*\)
    """,
    re.MULTILINE | re.VERBOSE,
)

# Reference-style link definitions: ``[label]: ../path`` (up to 3 spaces indent, optional title).
_REF_DEF = re.compile(
    r"""
    ^[ \t]{0,3}
    \[(?P<label>[^\]]+)\]:[ \t]+
    (?:
        <(?P<path_a>\.\./[^>\#\n]+)(?P<frag_a>\#[^>\n]*)?>
      | (?P<path>\.\./[^\s\#]+)(?P<frag>\#[^\s]*)?
    )
    (?:[ \t]+(?P<title>"[^"]*"|'[^']*'|\([^)]*\)))?
    [ \t]*$
    """,
    re.MULTILINE | re.VERBOSE,
)

_FENCE_OPEN = re.compile(r"^[ \t]*(?P<marker>`{3,}|~{3,})(?P<rest>.*)$")

# Image reference usages (definitions are ``[label]: ../path`` without a leading ``!``).
_IMAGE_REF_FULL = re.compile(r"!\[[^\]]*\]\[([^\]]+)\]")
_IMAGE_REF_COLLAPSED = re.compile(r"!\[([^\]]+)\]\[\]")
_IMAGE_REF_SHORTCUT = re.compile(r"!\[([^\]]+)\](?!\()")


def _normalize_ref_label(label: str) -> str:
    """Normalize a reference label (case-fold, collapse whitespace)."""
    return re.sub(r"\s+", " ", label.strip()).casefold()


def _collect_image_reference_labels(markdown: str) -> frozenset[str]:
    """Return normalized labels used by image reference usages in ``markdown``."""
    labels: set[str] = set()
    for pattern in (_IMAGE_REF_FULL, _IMAGE_REF_COLLAPSED, _IMAGE_REF_SHORTCUT):
        for match in pattern.finditer(markdown):
            labels.add(_normalize_ref_label(match.group(1)))
    return frozenset(labels)


@dataclass(frozen=True)
class _RewriteContext:
    page_abs_path: Path
    repo_root: Path
    repo_url: str
    view_ref: ViewRef
    forge: str | None
    report_missing: Callable[[str], None] | None
    image_ref_labels: frozenset[str]


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


def _parent_link_forge_url(
    path_part: str,
    fragment: str,
    ctx: _RewriteContext,
) -> str | None:
    """Build a forge view URL for a ``../`` path, or return ``None`` to leave the link unchanged."""
    target = (ctx.page_abs_path.parent / path_part).resolve()
    repo_path = _repo_relative(target=target, repo_root=ctx.repo_root)
    if repo_path is None:
        return None

    if target.is_dir():
        is_dir = True
    elif target.is_file():
        is_dir = False
    else:
        if ctx.report_missing is not None:
            ctx.report_missing(path_part)
        return None

    forge_name = ctx.forge or detect_forge(ctx.repo_url)
    url = repo_view_url(
        repo_url=ctx.repo_url,
        ref=ctx.view_ref.ref,
        ref_kind=ctx.view_ref.kind,
        repo_path=repo_path,
        is_dir=is_dir,
        forge=forge_name,
    )
    if url is None:
        return None
    out_fragment = translate_line_fragment(fragment, forge=forge_name) if forge_name else fragment
    return f"{url}{out_fragment}"


def _fence_closes_on_same_line(*, marker: str, rest: str) -> bool:
    """Return whether a fence opener and closer appear on the same line."""
    if not rest.strip():
        return False
    char = marker[0]
    min_len = len(marker)
    trailing = re.search(rf"({re.escape(char)}{{{min_len},}})\s*$", rest)
    return trailing is not None


def _rewrite_ref_def_line(body: str, ctx: _RewriteContext) -> str | None:
    """Return a rewritten reference-definition line, or ``None`` if unchanged."""
    ref_m = _REF_DEF.match(body)
    if ref_m is None:
        return None
    label = ref_m.group("label")
    if _normalize_ref_label(label) in ctx.image_ref_labels:
        return None
    path_part = ref_m.group("path") or ref_m.group("path_a")
    fragment = ref_m.group("frag") or ref_m.group("frag_a") or ""
    title = ref_m.group("title")
    url = _parent_link_forge_url(path_part, fragment, ctx)
    if url is None:
        return None
    title_suffix = f" {title}" if title else ""
    return f"[{label}]: {url}{title_suffix}"


def _rewrite_reference_definitions(markdown: str, ctx: _RewriteContext) -> str:
    """Rewrite ``[label]: ../path`` reference definitions to forge URLs."""
    out: list[str] = []
    in_fence = False
    fence_marker = ""

    for raw_line in markdown.splitlines(keepends=True):
        body = raw_line.rstrip("\r\n")
        suffix = raw_line[len(body) :]

        if in_fence:
            if re.match(rf"^[ \t]*{re.escape(fence_marker)}[ \t]*$", body):
                in_fence = False
                fence_marker = ""
            out.append(raw_line)
            continue

        open_m = _FENCE_OPEN.match(body)
        if open_m:
            marker = open_m.group("marker")
            if not _fence_closes_on_same_line(marker=marker, rest=open_m.group("rest")):
                in_fence = True
                fence_marker = marker
            out.append(raw_line)
            continue

        rewritten = _rewrite_ref_def_line(body, ctx)
        if rewritten is not None:
            out.append(f"{rewritten}{suffix}")
            continue

        out.append(raw_line)

    return "".join(out)


def rewrite_repo_parent_links(
    markdown: str,
    *,
    page_abs_path: Path,
    repo_root: Path,
    repo_url: str,
    view_ref: ViewRef,
    forge: str | None = None,
    report_missing: Callable[[str], None] | None = None,
) -> str:
    """Replace ``](../…)`` and ``[ref]: ../…`` markdown links with git-forge view URLs.

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
    view_ref : ViewRef
        Git branch name, tag name, or commit SHA and its kind (``branch``, ``commit``, or
        ``tag``) for forge view URLs.
    forge : str | None
        Explicit forge name; when ``None`` the forge is autodetected from ``repo_url``.
    report_missing : Callable[[str], None] | None
        Optional callback invoked with the link target (as written in the markdown) for each
        ``../`` link that resolves inside ``repo_root`` but points at a path that does not exist
        on disk. Links outside the repo are not reported.

    Returns
    -------
    str
        Markdown with matching parent-directory links rewritten to forge URLs.

    Notes
    -----
    Directory targets use ``tree`` URLs; file targets use ``blob`` URLs (on forges that
    distinguish them). URL fragments (``#anchor``) and link titles are preserved, and
    angle-bracket destinations (``](<../x>)``) are supported. Inline images (``![alt](../path)``)
    and image reference definitions are left unchanged because forge blob URLs are HTML pages, not
    raw image assets. Links inside fenced code blocks and inline code spans are left unchanged.
    Reference-style definitions (``[ref]: ../path``) are rewritten when not inside a fenced code
    block and not used as an image reference label.
    """

    image_ref_labels = _collect_image_reference_labels(markdown)
    ctx = _RewriteContext(
        page_abs_path=page_abs_path,
        repo_root=repo_root,
        repo_url=repo_url,
        view_ref=view_ref,
        forge=forge,
        report_missing=report_missing,
        image_ref_labels=image_ref_labels,
    )

    def repl(match: re.Match[str]) -> str:
        if match.group("image") is not None:
            return match.group(0)
        path_part = match.group("path") or match.group("path_a")
        if path_part is None:
            # Matched a fenced code block or inline code span: leave it untouched.
            return match.group(0)
        fragment = match.group("frag") or match.group("frag_a") or ""
        title = match.group("title")
        url = _parent_link_forge_url(path_part, fragment, ctx)
        if url is None:
            return match.group(0)
        title_suffix = f" {title}" if title else ""
        return f"]({url}{title_suffix})"

    rewritten = _SCAN.sub(repl, markdown)
    return _rewrite_reference_definitions(rewritten, ctx)
