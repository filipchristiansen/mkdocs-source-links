"""Property-based robustness tests for the markdown link rewriter.

These act as a lightweight in-repo fuzzer over :func:`rewrite_repo_parent_links`: they assert that
rewriting never raises on arbitrary input, is idempotent, and leaves text without ``../`` links
unchanged. The token-based strategy mixes the bracket, parenthesis, angle, backslash-escape, fence,
and fragment characters that drive the CommonMark-style scanners, plus paths that exist in the
``repo_tree`` fixture so links are actually resolved and rewritten.
"""

from __future__ import annotations

from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from conftest import rewrite_on_docs_page

# ``../`` targets that exist in the ``repo_tree`` fixture, so links built from them resolve and
# rewrite. Shared by the token pool and the image strategy.
_EXISTING_TARGETS = [
    "../src.py",
    "../env.example",
    "../img.png",
    "../backend/src/config.py",
    "../scripts",
]

# Fragments that build link-like markdown: delimiters, escapes, fences, fragments, a missing
# target, and the real ``repo_tree`` targets (so a fraction of generated links resolve and rewrite).
_TOKENS = [
    "[",
    "]",
    "(",
    ")",
    "<",
    ">",
    "`",
    "\\",
    '"',
    "'",
    " ",
    "\n",
    "\t",
    "#",
    "!",
    "a",
    "-",
    ":",
    "..",
    "/",
    "../",
    "../missing.txt",
    '"title"',
    "#L1-L2",
    "label",
    *_EXISTING_TARGETS,
]

_MAX_SIZE = 24
_LINKY = st.lists(st.sampled_from(_TOKENS), max_size=_MAX_SIZE).map("".join)

# Single-line link-like bodies with no backticks (so a one-backtick code span can't close early)
# and no newlines (so the span stays on one line and is not mistaken for a fenced block).
_INLINE_BODY_TOKENS = [t for t in _TOKENS if "`" not in t and "\n" not in t]
_INLINE_BODY = st.lists(st.sampled_from(_INLINE_BODY_TOKENS), max_size=_MAX_SIZE).map("".join)

# Plain image alt text (no brackets/links) and ``../`` targets that exist in the ``repo_tree``
# fixture, so the image is well-formed and resolvable yet must still be left unrewritten.
_IMAGE_ALT = st.text(alphabet="ab -_", max_size=20)
_EXISTING_TARGET = st.sampled_from(_EXISTING_TARGETS)

# Characters with no ``/`` (so ``../`` can never form): link delimiters, fences, escapes,
# quotes, whitespace, and prose. Used to prove non-link text is returned unchanged.
_NO_PARENT_CHARS = [
    "[",
    "]",
    "(",
    ")",
    "<",
    ">",
    "`",  # backtick fence
    "\\",  # backslash escape
    '"',  # double quote
    "'",  # single quote
    " ",  # space
    "\n",  # newline
    "\t",  # tab
    "#",  # hash
    "!",  # bang
    "a",  # letter
    "-",  # hyphen
    ":",  # colon
    ".",  # dot (but no slash, so never ``../``)
]

_NO_PARENT = st.text(alphabet=_NO_PARENT_CHARS, max_size=40)

_SETTINGS = settings(
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)


@_SETTINGS
@given(md=_LINKY)
def test_rewrite_never_raises(repo_tree: Path, md: str) -> None:
    rewrite_on_docs_page(repo_tree, md)


@_SETTINGS
@given(md=_LINKY)
def test_rewrite_is_idempotent(repo_tree: Path, md: str) -> None:
    once = rewrite_on_docs_page(repo_tree, md)
    assert rewrite_on_docs_page(repo_tree, once) == once


@_SETTINGS
@given(md=_NO_PARENT)
def test_text_without_parent_links_is_unchanged(repo_tree: Path, md: str) -> None:
    assert "../" not in md
    assert rewrite_on_docs_page(repo_tree, md) == md


@_SETTINGS
@given(body=_LINKY)
def test_fenced_code_blocks_are_left_unchanged(repo_tree: Path, body: str) -> None:
    # A backtick fence is closed only by a line of at least as many backticks. Sizing the fence
    # longer than every backtick in the body means no body line (even with real ``../`` links) can
    # close it early, so the whole block must pass through unchanged. max(3, ...) keeps it a valid
    # fence (needs >= 3 backticks) when the body has no backticks.
    fence = "`" * max(3, body.count("`") + 1)
    md = f"{fence}\n{body}\n{fence}\n"
    assert rewrite_on_docs_page(repo_tree, md) == md


@_SETTINGS
@given(md=_LINKY)
def test_rewrite_preserves_line_count(repo_tree: Path, md: str) -> None:
    # Rewriting only substitutes ``../`` destinations with single-line forge URLs, so it can never
    # add or drop newlines; a changed line count would mean content was duplicated or lost.
    assert rewrite_on_docs_page(repo_tree, md).count("\n") == md.count("\n")


@_SETTINGS
@given(body=_INLINE_BODY)
def test_inline_code_spans_are_left_unchanged(repo_tree: Path, body: str) -> None:
    # A ``../`` link inside an inline code span must be skipped (a different code path from fenced
    # blocks). The leading prose keeps the single backtick off the line start so it parses as an
    # inline span, not a fence; ``body`` has no backtick, so it closes only on the trailing one.
    md = f"see `{body}` here\n"
    assert rewrite_on_docs_page(repo_tree, md) == md


@_SETTINGS
@given(alt=_IMAGE_ALT, dest=_EXISTING_TARGET)
def test_image_links_are_never_rewritten(repo_tree: Path, alt: str, dest: str) -> None:
    # Image links resolve to forge HTML pages, not raw assets, so ``![alt](../path)`` is left
    # unchanged even when the target exists -- a distinct branch from normal inline links.
    md = f"![{alt}]({dest})\n"
    assert rewrite_on_docs_page(repo_tree, md) == md
