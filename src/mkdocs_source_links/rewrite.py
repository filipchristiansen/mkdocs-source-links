"""Rewrite [text](../path) inline links and [ref]: ../path definitions to forge view URLs."""

from __future__ import annotations

import os
import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

from .anchors import translate_line_fragment
from .ref import ViewRef
from .urls import detect_forge, repo_view_url

# Left-to-right scan on markdown outside fenced code blocks: inline code spans are skipped,
# then complete ``[text](../path)`` links are parsed with bracket-aware scanning (nested and
# escaped ``]`` in labels). The ``(../path)`` destination is parsed with a CommonMark-style
# scanner (:func:`_read_destination_and_title`) that handles escaped and balanced parentheses,
# angle-bracket destinations, fragments, and titles. Inline images (``![alt](../path)``) are
# left unchanged. Fenced regions are skipped via :func:`_iter_fence_runs`. Reference definitions
# use a line pass.
_INLINE_CODE = re.compile(r"(?P<backticks>`+)[\s\S]*?(?P=backticks)")

# Reference-style link definitions: ``[label]: ../path`` (up to 3 spaces indent, optional title).
_REF_DEF = re.compile(
    r"""
    ^(?P<indent>[ \t]{0,3})
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

# ASCII punctuation recognized after a backslash as a CommonMark escape in link destinations.
_ASCII_PUNCTUATION = frozenset(r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~""")

_FENCE_OPEN = re.compile(r"^[ \t]*(?P<marker>`{3,}|~{3,})(?P<rest>.*)$")


def _normalize_ref_label(label: str) -> str:
    """Normalize a reference label (case-fold, collapse whitespace)."""
    return re.sub(r"\s+", " ", label.strip()).casefold()


def _collect_image_reference_label_at(text: str, index: int) -> tuple[str, int] | None:  # pylint: disable=too-many-return-statements
    """Return a normalized image-reference label and the index after the usage, or ``None``."""
    if not text.startswith("![", index):
        return None
    alt_parsed = _read_balanced_brackets(text, index + 2)
    if alt_parsed is None:
        return None
    alt, after_alt = alt_parsed
    if after_alt >= len(text):
        return _normalize_ref_label(alt), after_alt
    if text[after_alt] == "[":
        if after_alt + 1 < len(text) and text[after_alt + 1] == "]":
            return _normalize_ref_label(alt), after_alt + 2
        ref_parsed = _read_balanced_brackets(text, after_alt + 1)
        if ref_parsed is None:
            return None
        ref_label, after_ref = ref_parsed
        return _normalize_ref_label(ref_label), after_ref
    if text[after_alt] in "([":
        return None
    return _normalize_ref_label(alt), after_alt


def _collect_image_reference_labels(markdown: str) -> frozenset[str]:
    """Return normalized labels used by image reference usages in ``markdown``.

    Only scans text outside fenced code blocks so examples in fences cannot suppress real
    reference definitions elsewhere on the page.
    """
    labels: set[str] = set()
    for text, in_fence in _iter_fence_runs(markdown):
        if in_fence:
            continue
        index = 0
        while index < len(text):
            code_match = _INLINE_CODE.match(text, index)
            if code_match is not None:
                index = code_match.end()
                continue
            collected = _collect_image_reference_label_at(text, index)
            if collected is None:
                index += 1
                continue
            label, index = collected
            labels.add(label)
    return frozenset(labels)


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
    repo_rel = Path(
        os.path.relpath(
            os.path.normpath(str(page_abs_path.parent / href)),
            str(root),
        )
    ).as_posix()
    return repo_rel, resolved


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


def _read_balanced_brackets(text: str, start: int) -> tuple[str, int] | None:
    """Return bracketed text and the index after ``]`` when ``text[start - 1]`` is ``[``."""
    depth = 1
    index = start
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return text[start:index], index + 1
        index += 1
    return None


def _skip_link_whitespace(text: str, index: int) -> int:
    """Return the index of the first non-whitespace character at or after ``index``."""
    while index < len(text) and text[index] in " \t\r\n":
        index += 1
    return index


def _unescape_destination(raw: str) -> str:
    """Resolve CommonMark backslash escapes in a link destination or fragment."""
    if "\\" not in raw:
        return raw
    out: list[str] = []
    index = 0
    while index < len(raw):
        char = raw[index]
        if char == "\\" and index + 1 < len(raw) and raw[index + 1] in _ASCII_PUNCTUATION:
            out.append(raw[index + 1])
            index += 2
            continue
        out.append(char)
        index += 1
    return "".join(out)


def _split_destination_fragment(raw: str) -> tuple[str, str]:
    """Split a raw destination at its first unescaped ``#`` into (path, fragment)."""
    index = 0
    while index < len(raw):
        char = raw[index]
        if char == "\\" and index + 1 < len(raw):
            index += 2
            continue
        if char == "#":
            return raw[:index], raw[index:]
        index += 1
    return raw, ""


def _read_destination_token(text: str, index: int) -> tuple[str, int] | None:
    """Read a link destination at ``index``, returning the raw text and the next index.

    Supports both the angle-bracket form (``<...>``) and the bare form (no whitespace, with
    balanced or backslash-escaped parentheses). Backslash escapes are preserved in the returned
    text and resolved later by :func:`_unescape_destination`.
    """
    if index < len(text) and text[index] == "<":
        return _read_angle_destination(text, index)
    return _read_bare_destination(text, index)


def _read_angle_destination(text: str, index: int) -> tuple[str, int] | None:
    """Read a ``<...>`` link destination starting at the opening ``<``."""
    buf: list[str] = []
    cursor = index + 1
    while cursor < len(text):
        char = text[cursor]
        if char == "\\" and cursor + 1 < len(text):
            buf.append(text[cursor : cursor + 2])
            cursor += 2
            continue
        if char in "\n<":
            return None
        if char == ">":
            return "".join(buf), cursor + 1
        buf.append(char)
        cursor += 1
    return None


def _read_bare_destination(text: str, index: int) -> tuple[str, int] | None:
    """Read a bare link destination (stops at whitespace or an unbalanced ``)``)."""
    buf: list[str] = []
    depth = 0
    cursor = index
    while cursor < len(text):
        char = text[cursor]
        if char == "\\" and cursor + 1 < len(text):
            buf.append(text[cursor : cursor + 2])
            cursor += 2
            continue
        if char.isspace():
            break
        if char == "(":
            depth += 1
        elif char == ")":
            if depth == 0:
                break
            depth -= 1
        buf.append(char)
        cursor += 1
    if depth != 0 or not buf:
        return None
    return "".join(buf), cursor


def _read_link_title(text: str, index: int) -> tuple[str, int] | None:
    """Read a quoted or parenthesized link title starting at ``index``, with the delimiters."""
    opener = text[index]
    closer = ")" if opener == "(" else opener
    cursor = index + 1
    while cursor < len(text):
        char = text[cursor]
        if char == "\\" and cursor + 1 < len(text):
            cursor += 2
            continue
        if char == closer:
            return text[index : cursor + 1], cursor + 1
        cursor += 1
    return None


@dataclass(frozen=True)
class _LinkTarget:
    path: str
    fragment: str
    title: str | None
    end: int


def _read_destination_and_title(text: str, index: int) -> tuple[str, str | None, int] | None:
    """Parse a destination and optional whitespace-separated title at ``index``.

    Returns the raw destination text, the title (with its delimiters, or ``None``), and the index
    just past what was consumed. Trailing whitespace after the destination or title is not
    consumed.
    """
    token = _read_destination_token(text, index)
    if token is None:
        return None
    raw_dest, cursor = token
    after_ws = _skip_link_whitespace(text, cursor)
    if cursor < after_ws < len(text) and text[after_ws] in "\"'(":
        title_token = _read_link_title(text, after_ws)
        if title_token is None:
            return None
        title, cursor = title_token
        return raw_dest, title, cursor
    return raw_dest, None, cursor


def _read_inline_destination(text: str, start: int) -> _LinkTarget | None:
    """Parse a ``(../path "title")`` inline link target; ``text[start]`` must be ``(``."""
    index = _skip_link_whitespace(text, start + 1)
    parsed = _read_destination_and_title(text, index)
    if parsed is None:
        return None
    raw_dest, title, cursor = parsed
    cursor = _skip_link_whitespace(text, cursor)
    if cursor >= len(text) or text[cursor] != ")":
        return None
    raw_path, raw_fragment = _split_destination_fragment(raw_dest)
    return _LinkTarget(
        path=_unescape_destination(raw_path),
        fragment=_unescape_destination(raw_fragment),
        title=title,
        end=cursor + 1,
    )


def _rewritten_inline_dest(dest: _LinkTarget, ctx: _RewriteContext) -> str | None:
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
        code_match = _INLINE_CODE.match(text, index)
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

        parsed = _read_balanced_brackets(text, bracket_start)
        if parsed is None:
            out.append(text[index])
            index += 1
            continue
        _label, after_bracket = parsed

        if after_bracket >= len(text) or text[after_bracket] != "(":
            out.append(text[index:after_bracket])
            index = after_bracket
            continue

        dest = _read_inline_destination(text, after_bracket)
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
        for text, in_fence in _iter_fence_runs(markdown)
    )


def _rewrite_ref_def_line(body: str, ctx: _RewriteContext) -> str | None:
    """Return a rewritten reference-definition line, or ``None`` if unchanged."""
    ref_m = _REF_DEF.match(body)
    if ref_m is None:
        return None
    label = ref_m.group("label")
    if _normalize_ref_label(label) in ctx.image_ref_labels:
        if ctx.report_skipped_shared_label is not None:
            ctx.report_skipped_shared_label(label)
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
    indent = ref_m.group("indent")
    return f"{indent}[{label}]: {url}{title_suffix}"


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
    """

    image_ref_labels = _collect_image_reference_labels(markdown)
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
