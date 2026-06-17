"""Tests for line-anchor fragment translation."""

from __future__ import annotations

import pytest

from mkdocs_source_links.anchors import translate_line_fragment


@pytest.mark.parametrize(
    ("forge", "fragment", "expected"),
    [
        ("github", "#L10", "#L10"),
        ("github", "#L10-L20", "#L10-L20"),
        ("github", "#section", "#section"),
        ("gitea", "#L10", "#L10"),
        ("gitea", "#L10-L20", "#L10-L20"),
        ("gitea", "#heading", "#heading"),
        ("gitlab", "#L10", "#L10"),
        ("gitlab", "#L10-L20", "#L10-20"),
        ("gitlab", "#notes", "#notes"),
        ("bitbucket", "#L10", "#lines-10"),
        ("bitbucket", "#L10-L20", "#lines-10:20"),
        ("bitbucket", "#foo", "#foo"),
        ("azure", "#L10", ""),
        ("azure", "#L10-L20", ""),
        ("azure", "#section", "#section"),
    ],
)
def test_translate_line_fragment(forge: str, fragment: str, expected: str) -> None:
    assert translate_line_fragment(fragment, forge=forge) == expected


def test_translate_line_fragment_empty() -> None:
    assert translate_line_fragment("", forge="github") == ""
