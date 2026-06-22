"""CommonMark-style scanners for inline links, image references, and reference definitions.

These helpers are pure text operations: they parse markdown link syntax (bracket-balanced labels,
angle-bracket and bare destinations, titles, fragments, and escapes) without resolving paths or
building forge URLs. Fenced regions are skipped via :func:`~._fences.iter_fence_runs`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ._fences import iter_fence_runs

# Complete inline ``[text](../path)`` links are parsed with bracket-aware scanning (nested and
# escaped ``]`` in labels). The ``(../path)`` destination is parsed by
# :func:`_read_destination_and_title`, which handles escaped and balanced parentheses,
# angle-bracket destinations, fragments, and titles.
INLINE_CODE = re.compile(r"(?P<backticks>`+)[\s\S]*?(?P=backticks)")

# Reference-style link definitions start with an indented label: ``[label]: ../path``. The label
# (which may contain nested or escaped ``]``) and destination are parsed by :func:`parse_ref_def`.
_REF_DEF_LABEL_START = re.compile(r"^(?P<indent>[ \t]{0,3})\[")

# ASCII punctuation recognized after a backslash as a CommonMark escape in link destinations.
_ASCII_PUNCTUATION = frozenset(r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~""")


def normalize_ref_label(label: str) -> str:
    """Normalize a reference label (case-fold, collapse whitespace)."""
    return re.sub(r"\s+", " ", label.strip()).casefold()


def read_balanced_brackets(text: str, start: int) -> tuple[str, int] | None:
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


def _collect_image_reference_label_at(text: str, index: int) -> tuple[str, int] | None:  # pylint: disable=too-many-return-statements
    """Return a normalized image-reference label and the index after the usage, or ``None``."""
    if not text.startswith("![", index):
        return None
    alt_parsed = read_balanced_brackets(text, index + 2)
    if alt_parsed is None:
        return None
    alt, after_alt = alt_parsed
    if after_alt >= len(text):
        return normalize_ref_label(alt), after_alt
    if text[after_alt] == "[":
        if after_alt + 1 < len(text) and text[after_alt + 1] == "]":
            return normalize_ref_label(alt), after_alt + 2
        ref_parsed = read_balanced_brackets(text, after_alt + 1)
        if ref_parsed is None:
            return None
        ref_label, after_ref = ref_parsed
        return normalize_ref_label(ref_label), after_ref
    if text[after_alt] in "([":
        return None
    return normalize_ref_label(alt), after_alt


def collect_image_reference_labels(markdown: str) -> frozenset[str]:
    """Return normalized labels used by image reference usages in ``markdown``.

    Only scans text outside fenced code blocks so examples in fences cannot suppress real
    reference definitions elsewhere on the page.
    """
    labels: set[str] = set()
    for text, in_fence in iter_fence_runs(markdown):
        if in_fence:
            continue
        index = 0
        while index < len(text):
            if text[index] == "\\":
                index += 2
                continue
            code_match = INLINE_CODE.match(text, index)
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
class LinkTarget:
    """Parsed inline link target: destination path, fragment, optional title, and end index."""

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


def read_inline_destination(text: str, start: int) -> LinkTarget | None:
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
    return LinkTarget(
        path=_unescape_destination(raw_path),
        fragment=_unescape_destination(raw_fragment),
        title=title,
        end=cursor + 1,
    )


@dataclass(frozen=True)
class RefDef:
    """Parsed reference definition: indent, label, path, fragment, and optional title."""

    indent: str
    label: str
    path: str
    fragment: str
    title: str | None


def parse_ref_def(body: str) -> RefDef | None:  # pylint: disable=too-many-return-statements
    """Parse a single-line ``[label]: ../path "title"`` reference definition, or ``None``.

    The label is read with bracket-aware scanning so nested (``[a [b]]``) and backslash-escaped
    (``[a\\]b]``) ``]`` characters are matched, mirroring inline link labels.
    """
    start_m = _REF_DEF_LABEL_START.match(body)
    if start_m is None:
        return None
    label_parsed = read_balanced_brackets(body, start_m.end())
    if label_parsed is None:
        return None
    label, after_label = label_parsed
    if not label.strip():
        return None
    if after_label >= len(body) or body[after_label] != ":":
        return None
    after_ws = _skip_link_whitespace(body, after_label + 1)
    if after_ws == after_label + 1:
        return None
    parsed = _read_destination_and_title(body, after_ws)
    if parsed is None:
        return None
    raw_dest, title, cursor = parsed
    if _skip_link_whitespace(body, cursor) != len(body):
        return None
    raw_path, raw_fragment = _split_destination_fragment(raw_dest)
    return RefDef(
        indent=start_m.group("indent"),
        label=label,
        path=_unescape_destination(raw_path),
        fragment=_unescape_destination(raw_fragment),
        title=title,
    )
