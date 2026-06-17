"""MkDocs plugin entry point."""

from __future__ import annotations

from pathlib import Path

from mkdocs.config import config_options
from mkdocs.config.base import PlainConfigSchema
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

from .branch import resolve_branch
from .ref import ViewRef, resolve_view_ref
from .rewrite import rewrite_repo_parent_links
from .urls import SUPPORTED_FORGES


class SourceLinksPlugin(BasePlugin):
    """MkDocs plugin that rewrites parent-directory markdown links to forge URLs.

    During ``mkdocs build``, ``](../path)`` links in each page's markdown are replaced with GitHub
    blob/tree view URLs. Source files on disk are not modified.

    Attributes
    ----------
    config_scheme : PlainConfigSchema
        Plugin configuration schema. Supports ``branch`` (override the git branch used in forge
        URLs), ``forge`` (override forge autodetection: one of ``github``, ``gitlab``,
        ``bitbucket``, ``gitea``, ``azure``), and ``pin`` (``branch`` or ``commit`` — embed the
        current commit SHA instead of a branch name).

    Notes
    -----
    Requires ``repo_url`` in ``mkdocs.yml``. Pages without a backing file (virtual pages) are left
    unchanged. The git view ref is resolved once per build in ``on_config``.
    """

    config_scheme: PlainConfigSchema = (
        ("branch", config_options.Optional(config_options.Type(str))),
        ("forge", config_options.Optional(config_options.Choice(SUPPORTED_FORGES))),
        ("pin", config_options.Choice(("branch", "commit"), default="branch")),
    )

    _view_ref: ViewRef

    def on_config(self, config: MkDocsConfig) -> MkDocsConfig:
        """Resolve the git view ref once per build and cache it.

        Resolving here (rather than per page) avoids running ``git`` for every page when
        ``pin: commit`` is set.

        Parameters
        ----------
        config : MkDocsConfig
            MkDocs site configuration.

        Returns
        -------
        MkDocsConfig
            The unmodified configuration.
        """
        branch = resolve_branch(
            plugin_branch=self.config.get("branch"),
            extra=config.extra or {},
            edit_uri=config.edit_uri,
        )
        self._view_ref = resolve_view_ref(
            pin=self.config.get("pin", "branch"),
            repo_root=Path(config.config_file_path).parent,
            branch=branch,
        )
        return config

    def on_page_markdown(
        self,
        markdown: str,
        /,
        *,
        page: Page,
        config: MkDocsConfig,
        files: Files,  # noqa: ARG002  # required by MkDocs hook signature; unused here
    ) -> str:
        """Rewrite ``](../…)`` links in page markdown to forge view URLs.

        Parameters
        ----------
        markdown : str
            Markdown source for the page after metadata has been stripped.
        page : Page
            MkDocs page whose ``file.abs_src_path`` locates the doc in the repo.
        config : MkDocsConfig
            MkDocs site configuration; ``repo_url`` must be set for any
            rewriting to occur.
        files : Files
            MkDocs file collection (required by the hook signature; unused).

        Returns
        -------
        str
            Markdown with parent-directory links rewritten, or the original ``markdown`` when
            ``repo_url`` is missing or the page has no backing file.
        """
        if not config.repo_url:
            return markdown
        if page.file.abs_src_path is None:
            return markdown
        return rewrite_repo_parent_links(
            markdown,
            page_abs_path=Path(page.file.abs_src_path),
            repo_root=Path(config.config_file_path).parent,
            repo_url=config.repo_url,
            view_ref=self._view_ref,
            forge=self.config.get("forge"),
        )
