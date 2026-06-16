"""Tests for package metadata."""

from __future__ import annotations

import importlib
from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

import mkdocs_source_links


def test_version_fallback_when_not_installed() -> None:
    with patch("importlib.metadata.version", side_effect=PackageNotFoundError()):
        importlib.reload(mkdocs_source_links)
        assert mkdocs_source_links.__version__ == "0.0.0.dev0"
    importlib.reload(mkdocs_source_links)
