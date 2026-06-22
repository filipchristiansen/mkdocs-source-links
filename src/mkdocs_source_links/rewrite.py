"""Rewrite ``[text](../path)`` inline links and ``[ref]: ../path`` definitions to forge view URLs.

:func:`rewrite_repo_parent_links` collects image-reference labels, rewrites inline links, then
reference definitions. The markdown parsing primitives live in the internal ``_scan`` and
``_fences`` modules, and ``../`` path resolution lives in the internal ``_paths`` module.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ._fences import iter_fence_runs, iter_fenced_lines
from ._paths import repo_relative_path, resolve_parent_href
from ._scan import (
    INLINE_CODE,
    LinkTarget,
    collect_image_reference_labels,
    normalize_ref_label,
    parse_ref_def,
    read_balanced_brackets,
    read_inline_destination,
)
from .anchors import translate_line_fragment
from .ref import ViewRef
from .urls import detect_forge, repo_view_url

__all__ = ["repo_relative_path", "rewrite_repo_parent_links"]


@dataclass(frozen=True)
class _RewriteContext:  # pylint: disable=too-many-instance-attributes
    page_abs_path: Path
    repo_root: Path
    repo_url: str
    view_ref: ViewRef
    resolved_forge: str | None
    report_missing: Callable[[str], None] | None
    report_rewrite: Callable[[], None] | None
    report_unknown_forge: Callable[[], None] | None
    report_skipped_shared_label: Callable[[str], None] | None
    image_ref_labels: frozenset[str]


def _parent_link_forge_url(path_part: str, fragment: str, ctx: _RewriteContext) -> str | None:
    """Build a forge view URL for a ``../`` path, or return ``None`` to leave the link unchanged."""
    resolved_pair = resolve_parent_href(
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

    forge_name = ctx.resolved_forge
    if forge_name is None:
        if ctx.report_unknown_forge is not None:
            ctx.report_unknown_forge()
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


def _rewritten_inline_dest(dest: LinkTarget, ctx: _RewriteContext) -> str | None:
    """Return a rewritten ``(../path)`` destination for a parsed inline link, or ``None``."""
    url = _parent_link_forge_url(dest.path, dest.fragment, ctx)
    if url is None:
        return None
    if ctx.report_rewrite is not None:
        ctx.report_rewrite()
    title_suffix = f" {dest.title}" if dest.title else ""
    return f"({url}{title_suffix})"


def _rewrite_inline_links_text(text: str, ctx: _RewriteContext) -> str:
    """Rewrite complete inline ``[text](../path)`` links in ``text``."""
    out: list[str] = []
    index = 0
    while index < len(text):
        if text[index] == "\\":
            out.append(text[index : index + 2])
            index += 2
            continue

        code_match = INLINE_CODE.match(text, index)
        if code_match is not None:
            out.append(code_match.group(0))
            index = code_match.end()
            continue

        is_image = text.startswith("![", index)
        if is_image:
            bracket_start = index + 2
        elif index < len(text) and text[index] == "[":
            bracket_start = index + 1
        else:
            out.append(text[index])
            index += 1
            continue

        parsed = read_balanced_brackets(text, bracket_start)
        if parsed is None:
            out.append(text[index])
            index += 1
            continue
        _label, after_bracket = parsed

        if after_bracket >= len(text) or text[after_bracket] != "(":
            out.append(text[index:after_bracket])
            index = after_bracket
            continue

        dest = read_inline_destination(text, after_bracket)
        if dest is None:
            out.append(text[index : after_bracket + 1])
            index = after_bracket + 1
            continue

        link_end = dest.end
        if is_image:
            out.append(text[index:link_end])
            index = link_end
            continue

        prefix = text[index:after_bracket]
        rewritten_suffix = _rewritten_inline_dest(dest, ctx)
        if rewritten_suffix is None:
            out.append(text[index:link_end])
        else:
            out.append(prefix + rewritten_suffix)
        index = link_end

    return "".join(out)


def _rewrite_inline_links(markdown: str, ctx: _RewriteContext) -> str:
    """Rewrite inline links only on markdown outside fenced code blocks."""
    return "".join(
        text if in_fence else _rewrite_inline_links_text(text, ctx)
        for text, in_fence in iter_fence_runs(markdown)
    )


def _rewrite_ref_def_line(body: str, ctx: _RewriteContext) -> str | None:
    """Return a rewritten reference-definition line, or ``None`` if unchanged."""
    ref = parse_ref_def(body)
    if ref is None or not ref.path.startswith("../"):
        return None
    if normalize_ref_label(ref.label) in ctx.image_ref_labels:
        if ctx.report_skipped_shared_label is not None:
            ctx.report_skipped_shared_label(ref.label)
        return None
    url = _parent_link_forge_url(ref.path, ref.fragment, ctx)
    if url is None:
        return None
    if ctx.report_rewrite is not None:
        ctx.report_rewrite()
    title_suffix = f" {ref.title}" if ref.title else ""
    return f"{ref.indent}[{ref.label}]: {url}{title_suffix}"


def _rewrite_reference_definitions(markdown: str, ctx: _RewriteContext) -> str:
    """Rewrite ``[label]: ../path`` reference definitions to forge URLs."""
    out: list[str] = []

    for line in iter_fenced_lines(markdown):
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
    report_unknown_forge: Callable[[], None] | None = None,
    report_skipped_shared_label: Callable[[str], None] | None = None,
) -> str:
    """Replace complete inline ``[text](../…)`` links and ``[ref]: ../…`` definitions with
    forge URLs.

    Inline rewrites require a bracket-balanced ``[label](../path)`` pair; lonely ``](../path)``
    suffixes in prose are left unchanged. Only links whose target resolves to an existing file or
    directory inside ``repo_root`` are rewritten. Unsupported hosts, paths outside the repo, and
    missing targets are left unchanged.

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
    report_unknown_forge : Callable[[], None] | None
        Optional callback invoked when a ``../`` link would be rewritten but the git forge could
        not be determined from ``repo_url`` and no explicit ``forge`` was set.
    report_skipped_shared_label : Callable[[str], None] | None
        Optional callback invoked when a ``[label]: ../path`` definition is skipped because
        ``label`` is also used by an image reference on the page.

    Returns
    -------
    str
        Markdown with matching inline and reference links rewritten to forge URLs.

    Notes
    -----
    Directory targets use ``tree`` URLs; file targets use ``blob`` URLs (on forges that
    distinguish them). URL fragments (``#anchor``) and link titles are preserved, and
    angle-bracket destinations (``[text](<../x>)``) are supported. Inline images
    (``![alt](../path)``), including alt text with nested or escaped ``]`` characters, and image
    reference definitions are left unchanged because forge blob URLs are HTML pages, not raw image
    assets. Links inside fenced code blocks and inline code spans are left unchanged.
    Reference-style definitions (``[ref]: ../path``) are rewritten when not inside a fenced code
    block and not used as an image reference label.

    The ``report_*`` callbacks are opt-in: when omitted, the corresponding events (missing targets,
    rewrites, undetectable forge, skipped shared labels) are silently ignored and only affect the
    returned markdown. The plugin (:class:`mkdocs_source_links.plugin.SourceLinksPlugin`) wires
    these callbacks to MkDocs logging — for example it passes ``report_unknown_forge`` only when no
    explicit ``forge`` is configured and warns once per build. Direct API callers that want the
    same warnings must pass their own callbacks.
    """

    image_ref_labels = collect_image_reference_labels(markdown)
    ctx = _RewriteContext(
        page_abs_path=page_abs_path,
        repo_root=repo_root,
        repo_url=repo_url,
        view_ref=view_ref,
        resolved_forge=forge or detect_forge(repo_url),
        report_missing=report_missing,
        report_rewrite=report_rewrite,
        report_unknown_forge=report_unknown_forge,
        report_skipped_shared_label=report_skipped_shared_label,
        image_ref_labels=image_ref_labels,
    )

    rewritten = _rewrite_inline_links(markdown, ctx)
    return _rewrite_reference_definitions(rewritten, ctx)
