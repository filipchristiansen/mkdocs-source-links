"""Rewrite ../ markdown links to forge view URLs."""

from __future__ import annotations

import os
import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

from .anchors import translate_line_fragment
from .ref import ViewRef
from .urls import detect_forge, repo_view_url

# Left-to-right scan on markdown outside fenced code blocks: an inline code span, an inline image
# with a ``../`` destination, or a ``](../path)`` / ``](../path#fragment)`` link. Fenced regions
# are skipped via :func:`_iter_fence_runs`; a regex scan (not line-based rewriting) is required
# here because inline links, images, and backtick spans can share a line. Reference definitions use
# a line pass instead because each ``[label]: ../path`` occupies its own line.
_SCAN = re.compile(
    r"""
    (?P<inline>(?P<backticks>`+)[\s\S]*?(?P=backticks))      # inline code span
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
class _RewriteContext:  # pylint: disable=too-many-instance-attributes
    page_abs_path: Path
    repo_root: Path
    repo_url: str
    view_ref: ViewRef
    forge: str | None
    report_missing: Callable[[str], None] | None
    report_rewrite: Callable[[], None] | None
    image_ref_labels: frozenset[str]


def _repo_relative(*, target: Path, repo_root: Path) -> str | None:
    """Express a resolved absolute path relative to the repository root.

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


def _resolve_parent_href(
    *, page_abs_path: Path, href: str, repo_root: Path
) -> tuple[str, Path] | None:
    """Resolve a ``../`` href to a repo-relative POSIX path and absolute target path."""
    if not href.startswith("../"):
        return None
    root = repo_root.resolve()
    resolved = (page_abs_path.parent / href).resolve()
    if _repo_relative(target=resolved, repo_root=repo_root) is None:
        return None
    rel = os.path.relpath(os.path.normpath(str(page_abs_path.parent / href)), str(root))
    if rel.startswith(".."):
        return None
    return Path(rel).as_posix(), resolved


def repo_relative_path(*, page_abs_path: Path, href: str, repo_root: Path) -> str | None:
    """Resolve a ``../`` link from a doc page to a repo-root-relative POSIX path.

    The returned path reflects the link text (lexical path). Symlink targets are not followed
    when building the forge URL path segment, but ``resolve()`` is still used to verify the
    target lies inside ``repo_root``.

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
    resolved = _resolve_parent_href(page_abs_path=page_abs_path, href=href, repo_root=repo_root)
    return resolved[0] if resolved is not None else None


def _parent_link_forge_url(path_part: str, fragment: str, ctx: _RewriteContext) -> str | None:
    """Build a forge view URL for a ``../`` path, or return ``None`` to leave the link unchanged."""
    resolved_pair = _resolve_parent_href(
        page_abs_path=ctx.page_abs_path,
        href=path_part,
        repo_root=ctx.repo_root,
    )
    if resolved_pair is None:
        return None
    repo_path, resolved = resolved_pair

    if resolved.is_dir():
        is_dir = True
    elif resolved.is_file():
        is_dir = False
    else:
        if ctx.report_missing is not None:
            ctx.report_missing(path_part)
        return None

    forge_name = ctx.forge or detect_forge(ctx.repo_url)
    if forge_name is None:
        return None
    url = repo_view_url(
        repo_url=ctx.repo_url,
        ref=ctx.view_ref.ref,
        ref_kind=ctx.view_ref.kind,
        repo_path=repo_path,
        is_dir=is_dir,
        forge=forge_name,
    )
    out_fragment = translate_line_fragment(fragment, forge=forge_name)
    return f"{url}{out_fragment}"


def _fence_closes_line(body: str, *, char: str, min_len: int) -> bool:
    """Return whether ``body`` closes a fence opened with ``char`` repeated ``min_len`` times."""
    return re.match(rf"^[ \t]*({re.escape(char)}{{{min_len},}})[ \t]*$", body) is not None


def _fence_closes_on_same_line(*, marker: str, rest: str) -> bool:
    """Return whether a fence opener and closer appear on the same line."""
    if not rest.strip():
        return False
    char = marker[0]
    min_len = len(marker)
    trailing = re.search(rf"({re.escape(char)}{{{min_len},}})\s*$", rest)
    return trailing is not None


@dataclass(frozen=True)
class _FencedLine:
    raw: str
    body: str
    in_fence: bool

    @property
    def suffix(self) -> str:
        """Return line-ending characters stripped from :attr:`body`."""
        return self.raw[len(self.body) :]


def _iter_fenced_lines(markdown: str) -> Iterator[_FencedLine]:
    """Yield each line with whether it lies inside a fenced code block."""
    in_fence = False
    fence_char = ""
    fence_min_len = 0

    for raw_line in markdown.splitlines(keepends=True):
        body = raw_line.rstrip("\r\n")

        if in_fence:
            yield _FencedLine(raw_line, body, in_fence=True)
            if _fence_closes_line(body, char=fence_char, min_len=fence_min_len):
                in_fence = False
                fence_char = ""
                fence_min_len = 0
            continue

        if open_m := _FENCE_OPEN.match(body):
            marker = open_m.group("marker")
            if not _fence_closes_on_same_line(marker=marker, rest=open_m.group("rest")):
                in_fence = True
                fence_char = marker[0]
                fence_min_len = len(marker)
                yield _FencedLine(raw_line, body, in_fence=True)
                continue

        yield _FencedLine(raw_line, body, in_fence=False)


def _iter_fence_runs(markdown: str) -> Iterator[tuple[str, bool]]:
    """Yield maximal contiguous markdown runs and whether each run is inside a fence."""
    run: list[str] = []
    run_in_fence = False
    have_run = False

    for line in _iter_fenced_lines(markdown):
        if have_run and line.in_fence != run_in_fence:
            yield "".join(run), run_in_fence
            run.clear()
        have_run = True
        run_in_fence = line.in_fence
        run.append(line.raw)

    if have_run:
        yield "".join(run), run_in_fence


def _rewrite_inline_links(markdown: str, replace: Callable[[re.Match[str]], str]) -> str:
    """Run ``_SCAN`` only on markdown outside fenced code blocks."""
    return "".join(
        text if in_fence else _SCAN.sub(replace, text)
        for text, in_fence in _iter_fence_runs(markdown)
    )


def _rewrite_link_match(match: re.Match[str], ctx: _RewriteContext) -> str:
    """Return a rewritten ``](../path)`` match, or the original text if unchanged."""
    if match.group("image") is not None:
        return match.group(0)
    path_part = match.group("path") or match.group("path_a")
    if path_part is None:
        # Matched an inline code span: leave it untouched.
        return match.group(0)
    fragment = match.group("frag") or match.group("frag_a") or ""
    title = match.group("title")
    url = _parent_link_forge_url(path_part, fragment, ctx)
    if url is None:
        return match.group(0)
    if ctx.report_rewrite is not None:
        ctx.report_rewrite()
    title_suffix = f" {title}" if title else ""
    return f"]({url}{title_suffix})"


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
    if ctx.report_rewrite is not None:
        ctx.report_rewrite()
    title_suffix = f" {title}" if title else ""
    return f"[{label}]: {url}{title_suffix}"


def _rewrite_reference_definitions(markdown: str, ctx: _RewriteContext) -> str:
    """Rewrite ``[label]: ../path`` reference definitions to forge URLs."""
    out: list[str] = []

    for line in _iter_fenced_lines(markdown):
        if line.in_fence:
            out.append(line.raw)
            continue

        rewritten = _rewrite_ref_def_line(line.body, ctx)
        if rewritten is not None:
            out.append(f"{rewritten}{line.suffix}")
            continue

        out.append(line.raw)

    return "".join(out)


def rewrite_repo_parent_links(  # pylint: disable=too-many-arguments
    markdown: str,
    *,
    page_abs_path: Path,
    repo_root: Path,
    repo_url: str,
    view_ref: ViewRef,
    forge: str | None = None,
    report_missing: Callable[[str], None] | None = None,
    report_rewrite: Callable[[], None] | None = None,
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
    report_rewrite : Callable[[], None] | None
        Optional callback invoked once for each successfully rewritten inline link or reference
        definition.

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
        report_rewrite=report_rewrite,
        image_ref_labels=image_ref_labels,
    )

    rewritten = _rewrite_inline_links(
        markdown,
        lambda match: _rewrite_link_match(match, ctx),
    )
    return _rewrite_reference_definitions(rewritten, ctx)
