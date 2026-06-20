"""Tests for the MkDocs plugin hook."""

# pylint: disable=protected-access

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
    assert plugin._view_ref == ViewRef("develop", "branch")


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
    assert plugin._view_ref == ViewRef("develop", "branch")


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
        ViewRef("main", "branch"),
        used_fallback=True,
        requested_pin="commit",
    )

    with (
        patch("mkdocs_source_links.plugin.resolve_view_ref", return_value=fallback),
        caplog.at_level(logging.WARNING),
    ):
        plugin.on_config(config)

    assert "could not be resolved via git" in caplog.text
    assert plugin._view_ref == ViewRef("main", "branch")


def test_on_config_branch_pin_uses_plugin_branch_override() -> None:
    plugin = SourceLinksPlugin()
    plugin.config = {"pin": "branch", "branch": "release-1.0"}
    config = _config(
        repo_url=REPO,
        config_file_path="/repo/mkdocs.yml",
        edit_uri="edit/main/docs/",
    )

    with patch("mkdocs_source_links.plugin.resolve_view_ref") as resolve_mock:
        resolve_mock.return_value = ResolvedViewRef(
            ViewRef("release-1.0", "branch"),
            used_fallback=False,
            requested_pin="branch",
        )
        plugin.on_config(config)

    resolve_mock.assert_called_once_with(
        pin="branch",
        repo_root=Path("/repo"),
        branch="release-1.0",
    )
    assert plugin._view_ref == ViewRef("release-1.0", "branch")


def test_on_config_commit_pin_sets_commit_view_ref() -> None:
    plugin = SourceLinksPlugin()
    plugin.config = {"pin": "commit"}
    config = _config(
        repo_url=REPO,
        config_file_path="/repo/mkdocs.yml",
        edit_uri="edit/main/docs/",
    )
    commit_ref = ResolvedViewRef(
        ViewRef("abc123", "commit"),
        used_fallback=False,
        requested_pin="commit",
    )

    with patch("mkdocs_source_links.plugin.resolve_view_ref", return_value=commit_ref):
        plugin.on_config(config)

    assert plugin._view_ref == ViewRef("abc123", "commit")


def test_on_config_tag_pin_sets_tag_view_ref() -> None:
    plugin = SourceLinksPlugin()
    plugin.config = {"pin": "tag"}
    config = _config(
        repo_url=REPO,
        config_file_path="/repo/mkdocs.yml",
        edit_uri="edit/main/docs/",
    )
    tag_ref = ResolvedViewRef(ViewRef("v1.2.3", "tag"), used_fallback=False, requested_pin="tag")

    with patch("mkdocs_source_links.plugin.resolve_view_ref", return_value=tag_ref):
        plugin.on_config(config)

    assert plugin._view_ref == ViewRef("v1.2.3", "tag")


def test_on_page_markdown_passes_forge_to_rewrite(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    page_path = docs / "page.md"
    page_path.write_text("# Page\n")
    (tmp_path / "env.example").write_text("x\n")
    mkdocs_yml = tmp_path / "mkdocs.yml"
    mkdocs_yml.write_text("site_name: test\n")

    plugin = SourceLinksPlugin()
    plugin.config = {"forge": "gitlab"}
    markdown = "[cfg](../env.example)."
    page = _page(str(page_path))
    config = _config(
        repo_url=REPO,
        config_file_path=str(mkdocs_yml),
        edit_uri="edit/main/docs/",
    )
    files = cast(Files, SimpleNamespace())

    with patch("mkdocs_source_links.plugin.rewrite_repo_parent_links") as rewrite_mock:
        rewrite_mock.return_value = markdown
        plugin.on_config(config)
        plugin.on_page_markdown(markdown, page=page, config=config, files=files)

    rewrite_mock.assert_called_once()
    assert rewrite_mock.call_args.kwargs["forge"] == "gitlab"


def _rewrite_logging_setup(tmp_path: Path) -> tuple[SourceLinksPlugin, Page, MkDocsConfig, Files]:
    docs = tmp_path / "docs"
    docs.mkdir()
    page_path = docs / "page.md"
    page_path.write_text("# Page\n")
    (tmp_path / "README.md").write_text("# Readme\n")
    (tmp_path / "src.py").write_text("x\n")
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


def test_log_rewrites_default_is_silent(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    plugin, page, config, files = _rewrite_logging_setup(tmp_path)
    plugin.config = {}
    markdown = "[readme](../README.md) and [src](../src.py)."

    plugin.on_config(config)
    with caplog.at_level(logging.INFO):
        plugin.on_page_markdown(markdown, page=page, config=config, files=files)
        plugin.on_post_build(config=config)

    assert "Rewrote" not in caplog.text


def test_log_rewrites_summary_logs_build_total(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    plugin, page, config, files = _rewrite_logging_setup(tmp_path)
    plugin.config = {"log_rewrites": "summary"}
    markdown = "[readme](../README.md) and [src](../src.py)."

    plugin.on_config(config)
    with caplog.at_level(logging.INFO):
        plugin.on_page_markdown(markdown, page=page, config=config, files=files)
        plugin.on_post_build(config=config)

    assert "Rewrote 2 ../ links across 1 page" in caplog.text
    assert "page.md: rewrote" not in caplog.text


def test_log_rewrites_verbose_logs_per_page_and_summary(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    plugin, page, config, files = _rewrite_logging_setup(tmp_path)
    plugin.config = {"log_rewrites": "verbose"}
    markdown = "[readme](../README.md)."

    plugin.on_config(config)
    with caplog.at_level(logging.INFO):
        plugin.on_page_markdown(markdown, page=page, config=config, files=files)
        plugin.on_post_build(config=config)

    assert "page.md: rewrote 1 link" in caplog.text
    assert "Rewrote 1 ../ link across 1 page" in caplog.text


def test_log_rewrites_verbose_skips_pages_with_zero_rewrites(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    plugin, page, config, files = _rewrite_logging_setup(tmp_path)
    plugin.config = {"log_rewrites": "verbose"}
    markdown = "No parent links here."

    plugin.on_config(config)
    with caplog.at_level(logging.INFO):
        plugin.on_page_markdown(markdown, page=page, config=config, files=files)
        plugin.on_post_build(config=config)

    assert "page.md: rewrote" not in caplog.text
    assert "Rewrote 0 ../ links across 0 pages" in caplog.text


def test_log_rewrites_summary_logs_zero_when_no_rewrites(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    plugin, page, config, files = _rewrite_logging_setup(tmp_path)
    plugin.config = {"log_rewrites": "summary"}
    markdown = "No parent links here."

    plugin.on_config(config)
    with caplog.at_level(logging.INFO):
        plugin.on_page_markdown(markdown, page=page, config=config, files=files)
        plugin.on_post_build(config=config)

    assert "page.md: rewrote" not in caplog.text
    assert "Rewrote 0 ../ links across 0 pages" in caplog.text


def test_log_rewrites_silent_without_repo_url(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    plugin, page, config, files = _rewrite_logging_setup(tmp_path)
    plugin.config = {"log_rewrites": "summary"}
    markdown = "[readme](../README.md)."
    config = _config(
        repo_url=None,
        config_file_path=config.config_file_path,
        edit_uri="edit/main/docs/",
    )

    plugin.on_config(config)
    with caplog.at_level(logging.INFO):
        plugin.on_page_markdown(markdown, page=page, config=config, files=files)
        plugin.on_post_build(config=config)

    assert "Rewrote" not in caplog.text


def test_log_rewrites_summary_across_multiple_pages(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    plugin, page, config, files = _rewrite_logging_setup(tmp_path)
    plugin.config = {"log_rewrites": "summary"}
    page_b_path = tmp_path / "docs" / "other.md"
    page_b_path.write_text("# Other\n")
    page_b = _page(str(page_b_path), src_path="other.md")

    plugin.on_config(config)
    with caplog.at_level(logging.INFO):
        plugin.on_page_markdown(
            "[readme](../README.md).",
            page=page,
            config=config,
            files=files,
        )
        plugin.on_page_markdown(
            "[src](../src.py) and [readme](../README.md).",
            page=page_b,
            config=config,
            files=files,
        )
        plugin.on_post_build(config=config)

    assert "Rewrote 3 ../ links across 2 pages" in caplog.text


def test_log_rewrites_disabled_when_plugin_disabled(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    plugin, page, config, files = _rewrite_logging_setup(tmp_path)
    plugin.config = {"enabled": False, "log_rewrites": "summary"}
    markdown = "[readme](../README.md)."

    plugin.on_config(config)
    with caplog.at_level(logging.INFO):
        plugin.on_page_markdown(markdown, page=page, config=config, files=files)
        plugin.on_post_build(config=config)

    assert "Rewrote" not in caplog.text


def test_log_rewrites_zero_for_virtual_page(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    plugin, _, config, files = _rewrite_logging_setup(tmp_path)
    plugin.config = {"log_rewrites": "summary"}
    page = _page(None)
    markdown = "[readme](../README.md)."

    plugin.on_config(config)
    with caplog.at_level(logging.INFO):
        plugin.on_page_markdown(markdown, page=page, config=config, files=files)
        plugin.on_post_build(config=config)

    assert "Rewrote 0 ../ links across 0 pages" in caplog.text


def test_log_rewrites_counters_reset_on_config(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    plugin, page, config, files = _rewrite_logging_setup(tmp_path)
    plugin.config = {"log_rewrites": "summary"}
    markdown = "[readme](../README.md)."

    plugin.on_config(config)
    plugin.on_page_markdown(markdown, page=page, config=config, files=files)

    plugin.on_config(config)
    with caplog.at_level(logging.INFO):
        plugin.on_post_build(config=config)

    assert "Rewrote 0 ../ links across 0 pages" in caplog.text


def test_unknown_forge_warns_once_per_build(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    page_path = docs / "page.md"
    page_path.write_text("# Page\n")
    (tmp_path / "README.md").write_text("# Readme\n")
    (tmp_path / "src.py").write_text("x\n")
    mkdocs_yml = tmp_path / "mkdocs.yml"
    mkdocs_yml.write_text("site_name: test\n")

    plugin = SourceLinksPlugin()
    plugin.config = {}
    page = _page(str(page_path), src_path="page.md")
    unknown = "https://example.com/org/repo"
    config = _config(
        repo_url=unknown,
        config_file_path=str(mkdocs_yml),
        edit_uri="edit/main/docs/",
    )
    files = cast(Files, SimpleNamespace())
    markdown = "[readme](../README.md) and [src](../src.py)."

    plugin.on_config(config)
    with caplog.at_level(logging.WARNING):
        plugin.on_page_markdown(markdown, page=page, config=config, files=files)
        plugin.on_page_markdown(markdown, page=page, config=config, files=files)

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "Could not detect git forge" in warnings[0].message


def test_unknown_forge_silent_with_explicit_forge_override(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    page_path = docs / "page.md"
    page_path.write_text("# Page\n")
    (tmp_path / "README.md").write_text("# Readme\n")
    mkdocs_yml = tmp_path / "mkdocs.yml"
    mkdocs_yml.write_text("site_name: test\n")

    plugin = SourceLinksPlugin()
    plugin.config = {"forge": "gitlab"}
    page = _page(str(page_path), src_path="page.md")
    config = _config(
        repo_url="https://example.com/org/repo",
        config_file_path=str(mkdocs_yml),
        edit_uri="edit/main/docs/",
    )
    files = cast(Files, SimpleNamespace())

    plugin.on_config(config)
    with caplog.at_level(logging.WARNING):
        plugin.on_page_markdown("[readme](../README.md).", page=page, config=config, files=files)

    assert "Could not detect git forge" not in caplog.text


def test_log_rewrites_verbose_logs_skipped_shared_image_ref_label(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    page_path = docs / "page.md"
    page_path.write_text("# Page\n")
    (tmp_path / "img.png").write_bytes(b"\x89PNG\r\n")
    mkdocs_yml = tmp_path / "mkdocs.yml"
    mkdocs_yml.write_text("site_name: test\n")

    plugin = SourceLinksPlugin()
    plugin.config = {"log_rewrites": "verbose"}
    page = _page(str(page_path), src_path="page.md")
    config = _config(
        repo_url=REPO,
        config_file_path=str(mkdocs_yml),
        edit_uri="edit/main/docs/",
    )
    files = cast(Files, SimpleNamespace())
    markdown = "[docs][ref]\n![docs]\n\n[docs]: ../img.png\n"

    plugin.on_config(config)
    with caplog.at_level(logging.INFO):
        plugin.on_page_markdown(markdown, page=page, config=config, files=files)

    assert "page.md: skipped [docs] reference definition (image reference label)" in caplog.text
