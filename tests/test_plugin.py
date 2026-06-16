"""Tests for the MkDocs plugin hook."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

from mkdocs_source_links.plugin import SourceLinksPlugin

REPO = "https://github.com/example/example-repo"


def _page(abs_src_path: str | None) -> Page:
    return cast(Page, SimpleNamespace(file=SimpleNamespace(abs_src_path=abs_src_path)))


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

    out = plugin.on_page_markdown(markdown, page=page, config=config, files=files)
    assert out == f"[readme]({REPO}/blob/main/README.md)."
