"""MkDocs plugin entry point."""

from __future__ import annotations

from pathlib import Path

from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin

from .branch import resolve_branch
from .rewrite import rewrite_repo_parent_links


class SourceLinksPlugin(BasePlugin):
    config_scheme = (("branch", config_options.Optional(config_options.Type(str))),)

    def on_page_markdown(self, markdown: str, *, page, config, **kwargs) -> str:
        if not config.repo_url:
            return markdown
        plugin_branch = self.config.get("branch")
        return rewrite_repo_parent_links(
            markdown,
            page_abs_path=Path(page.file.abs_src_path),
            repo_root=Path(config.config_file_path).parent,
            repo_url=config.repo_url,
            branch=resolve_branch(
                plugin_branch=plugin_branch,
                extra=config.extra or {},
                edit_uri=config.edit_uri,
            ),
        )
