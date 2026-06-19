"""Tests for the MkDocs plugin hook."""

from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import patch

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

from conftest import REPO
from mkdocs_source_links.plugin import SourceLinksPlugin
from mkdocs_source_links.ref import ResolvedViewRef, ViewRef

if TYPE_CHECKING:
    import pytest


def _page(abs_src_path: str | None, *, src_path: str = "page.md") -> Page:
    return cast(
        Page,
        SimpleNamespace(file=SimpleNamespace(abs_src_path=abs_src_path, src_path=src_path)),
    )


def _config(
    *,
    repo_url: str | None,
    config_file_path: str,
    extra: dict[str, Any] | None = None,
    edit_uri: str | None = None,
) -> MkDocsConfig:
    return cast(
        MkDocsConfig,
        SimpleNamespace(
            repo_url=repo_url,
            config_file_path=config_file_path,
            extra=extra,
            edit_uri=edit_uri,
        ),
    )


def test_on_page_markdown_without_repo_url() -> None:
    plugin = SourceLinksPlugin()
    plugin.config = {}
    markdown = "[readme](../README.md)."
    page = _page("/repo/docs/page.md")
    config = _config(repo_url=None, config_file_path="/repo/mkdocs.yml")
    files = cast(Files, SimpleNamespace())

    assert plugin.on_page_markdown(markdown, page=page, config=config, files=files) == markdown


def test_on_page_markdown_without_backing_file() -> None:
    plugin = SourceLinksPlugin()
    plugin.config = {}
    markdown = "[readme](../README.md)."
    page = _page(None)
    config = _config(repo_url=REPO, config_file_path="/repo/mkdocs.yml")
    files = cast(Files, SimpleNamespace())

    assert plugin.on_page_markdown(markdown, page=page, config=config, files=files) == markdown


def test_on_page_markdown_rewrites_links(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    page_path = docs / "page.md"
    page_path.write_text("# Page\n")
    (tmp_path / "README.md").write_text("# Readme\n")
    mkdocs_yml = tmp_path / "mkdocs.yml"
    mkdocs_yml.write_text("site_name: test\n")

    plugin = SourceLinksPlugin()
    plugin.config = {}
    markdown = "[readme](../README.md)."
    page = _page(str(page_path))
    config = _config(
        repo_url=REPO,
        config_file_path=str(mkdocs_yml),
        edit_uri="edit/main/docs/",
    )
    files = cast(Files, SimpleNamespace())

    plugin.on_config(config)
    out = plugin.on_page_markdown(markdown, page=page, config=config, files=files)
    assert out == f"[readme]({REPO}/blob/main/README.md)."


def test_on_config_disabled_sets_branch_view_ref() -> None:
    plugin = SourceLinksPlugin()
    plugin.config = {"enabled": False}
    config = _config(
        repo_url=REPO,
        config_file_path="/repo/mkdocs.yml",
        edit_uri="-/edit/develop/docs/",
    )

    assert plugin.on_config(config) is config
    assert plugin._view_ref == ViewRef("develop", "branch")  # pylint: disable=protected-access


def test_on_page_markdown_disabled_leaves_markdown() -> None:
    plugin = SourceLinksPlugin()
    plugin.config = {"enabled": False}
    markdown = "[readme](../README.md)."
    page = _page("/repo/docs/page.md")
    config = _config(repo_url=REPO, config_file_path="/repo/mkdocs.yml")
    files = cast(Files, SimpleNamespace())

    assert plugin.on_page_markdown(markdown, page=page, config=config, files=files) == markdown


def _missing_target_setup(tmp_path: Path) -> tuple[SourceLinksPlugin, Page, MkDocsConfig, Files]:
    docs = tmp_path / "docs"
    docs.mkdir()
    page_path = docs / "page.md"
    page_path.write_text("# Page\n")
    mkdocs_yml = tmp_path / "mkdocs.yml"
    mkdocs_yml.write_text("site_name: test\n")

    plugin = SourceLinksPlugin()
    page = _page(str(page_path), src_path="page.md")
    config = _config(
        repo_url=REPO,
        config_file_path=str(mkdocs_yml),
        edit_uri="edit/main/docs/",
    )
    files = cast(Files, SimpleNamespace())
    return plugin, page, config, files


def test_warn_on_missing_logs_warning(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    plugin, page, config, files = _missing_target_setup(tmp_path)
    plugin.config = {}
    markdown = "[gone](../missing.py)."

    plugin.on_config(config)
    with caplog.at_level(logging.WARNING):
        out = plugin.on_page_markdown(markdown, page=page, config=config, files=files)

    assert out == markdown
    assert "does not exist" in caplog.text
    assert "missing.py" in caplog.text


def test_warn_on_missing_disabled_is_silent(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    plugin, page, config, files = _missing_target_setup(tmp_path)
    plugin.config = {"warn_on_missing": False}
    markdown = "[gone](../missing.py)."

    plugin.on_config(config)
    with caplog.at_level(logging.WARNING):
        out = plugin.on_page_markdown(markdown, page=page, config=config, files=files)

    assert out == markdown
    assert "does not exist" not in caplog.text


def test_on_config_without_repo_url_skips_git_and_sets_branch_ref() -> None:
    plugin = SourceLinksPlugin()
    plugin.config = {"pin": "commit"}
    config = _config(
        repo_url=None,
        config_file_path="/repo/mkdocs.yml",
        edit_uri="edit/develop/docs/",
    )

    with patch("mkdocs_source_links.plugin.resolve_view_ref") as resolve_mock:
        assert plugin.on_config(config) is config

    resolve_mock.assert_not_called()
    assert plugin._view_ref == ViewRef("develop", "branch")  # pylint: disable=protected-access


def test_on_config_warns_when_pin_falls_back_to_branch(
    caplog: pytest.LogCaptureFixture,
) -> None:
    plugin = SourceLinksPlugin()
    plugin.config = {"pin": "commit"}
    config = _config(
        repo_url=REPO,
        config_file_path="/repo/mkdocs.yml",
        edit_uri="edit/main/docs/",
    )
    fallback = ResolvedViewRef(
        ViewRef("main", "branch"), used_fallback=True, requested_pin="commit"
    )

    with (
        patch("mkdocs_source_links.plugin.resolve_view_ref", return_value=fallback),
        caplog.at_level(logging.WARNING),
    ):
        plugin.on_config(config)

    assert "could not be resolved via git" in caplog.text
    assert plugin._view_ref == ViewRef("main", "branch")  # pylint: disable=protected-access
