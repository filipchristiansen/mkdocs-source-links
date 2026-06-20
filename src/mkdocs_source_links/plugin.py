"""MkDocs plugin entry point."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from mkdocs.config import config_options
from mkdocs.config.base import PlainConfigSchema
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin, get_plugin_logger
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

from .branch import resolve_branch
from .ref import ViewRef, resolve_view_ref
from .rewrite import rewrite_repo_parent_links
from .urls import SUPPORTED_FORGES

log = get_plugin_logger(__name__)


def _plural(count: int, noun: str) -> str:
    """Return ``noun`` or ``noun`` + ``s`` for log message wording."""
    return noun if count == 1 else f"{noun}s"


class SourceLinksPlugin(BasePlugin):
    """MkDocs plugin that rewrites parent-directory inline and reference markdown links to
    forge URLs.

    During ``mkdocs build``, complete inline ``[text](../path)`` links and ``[ref]: ../path``
    reference definitions in each page's markdown are replaced with git-forge blob/tree/view URLs.
    Source files on disk are not modified.

    Attributes
    ----------
    config_scheme : PlainConfigSchema
        Plugin configuration schema. Supports ``enabled`` (turn rewriting on or off),
        ``branch`` (override the git branch used in forge URLs), ``forge`` (override forge
        autodetection: one of ``github``, ``gitlab``, ``bitbucket``, ``gitea``, ``azure``),
        ``pin`` (``branch``, ``commit``, or ``tag`` — embed HEAD SHA or an exact tag name when
        set), ``warn_on_missing`` (warn when a ``../`` link target does not exist), and
        ``log_rewrites`` (opt-in INFO logging of successful rewrites: ``false``, ``summary``, or
        ``verbose``).

    Notes
    -----
    Requires ``repo_url`` in ``mkdocs.yml``. Pages without a backing file (virtual pages) are left
    unchanged. The git view ref is resolved once per build in ``on_config``, which MkDocs always
    runs before ``on_page_markdown``. ``_view_ref`` holds a placeholder until ``on_config`` runs.
    """

    config_scheme: PlainConfigSchema = (
        ("enabled", config_options.Type(bool, default=True)),
        ("pin", config_options.Choice(("branch", "commit", "tag"), default="branch")),
        ("branch", config_options.Optional(config_options.Type(str))),
        ("forge", config_options.Optional(config_options.Choice(SUPPORTED_FORGES))),
        ("warn_on_missing", config_options.Type(bool, default=True)),
        ("log_rewrites", config_options.Choice((False, "summary", "verbose"), default=False)),
    )

    _view_ref: ViewRef = ViewRef("", "branch")
    _rewrite_total: int = 0
    _rewrite_by_page: dict[str, int]

    def __init__(self) -> None:
        super().__init__()
        self._rewrite_by_page = {}

    def on_config(self, config: MkDocsConfig) -> MkDocsConfig:
        """Resolve the git view ref once per build and cache it.

        Resolving here (rather than per page) avoids running ``git`` for every page when
        ``pin: commit`` or ``pin: tag`` is set.

        Parameters
        ----------
        config : MkDocsConfig
            MkDocs site configuration.

        Returns
        -------
        MkDocsConfig
            The unmodified configuration.
        """
        self._rewrite_total = 0
        self._rewrite_by_page = {}
        branch = resolve_branch(
            plugin_branch=self.config.get("branch"),
            extra=config.extra or {},
            edit_uri=config.edit_uri,
        )
        if not self.config.get("enabled", True):
            self._view_ref = ViewRef(branch, "branch")
            return config
        if not config.repo_url:
            self._view_ref = ViewRef(branch, "branch")
            return config
        resolved = resolve_view_ref(
            pin=self.config.get("pin", "branch"),
            repo_root=Path(config.config_file_path).parent,
            branch=branch,
        )
        self._view_ref = resolved.view_ref
        if resolved.used_fallback:
            log.warning(
                "pin %r could not be resolved via git; using branch %r in forge URLs",
                resolved.requested_pin,
                resolved.view_ref.ref,
            )
        return config

    def on_page_markdown(
        self,
        markdown: str,
        /,
        *,
        page: Page,
        config: MkDocsConfig,
        files: Files,
    ) -> str:
        """Rewrite inline ``[text](../…)`` links and ``[ref]: ../…`` definitions to forge URLs.

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
            Markdown with matching inline and reference links rewritten, or the original
            ``markdown`` when the plugin is disabled, ``repo_url`` is missing, or the page has no
            backing file.
        """
        _ = files
        if not self.config.get("enabled", True):
            return markdown
        if not config.repo_url:
            return markdown
        if page.file.abs_src_path is None:
            return markdown

        report_missing: Callable[[str], None] | None = None
        if self.config.get("warn_on_missing", True):
            src_path = page.file.src_path

            def _warn(target: str) -> None:
                log.warning("Link target does not exist: %s (in %s)", target, src_path)

            report_missing = _warn

        log_mode = self.config.get("log_rewrites", False)
        report_rewrite: Callable[[], None] | None = None
        page_rewrites = 0
        if log_mode:

            def _count_rewrite() -> None:
                nonlocal page_rewrites
                page_rewrites += 1

            report_rewrite = _count_rewrite

        result = rewrite_repo_parent_links(
            markdown,
            page_abs_path=Path(page.file.abs_src_path),
            repo_root=Path(config.config_file_path).parent,
            repo_url=config.repo_url,
            view_ref=self._view_ref,
            forge=self.config.get("forge"),
            report_missing=report_missing,
            report_rewrite=report_rewrite,
        )
        if page_rewrites:
            src_path = page.file.src_path
            self._rewrite_total += page_rewrites
            self._rewrite_by_page[src_path] = self._rewrite_by_page.get(src_path, 0) + page_rewrites
        return result

    def on_post_build(
        self,
        *,
        config: MkDocsConfig,
        **kwargs: object,
    ) -> None:
        """Log rewrite statistics when ``log_rewrites`` is enabled.

        Parameters
        ----------
        config : MkDocsConfig
            MkDocs site configuration; ``repo_url`` must be set for rewrite statistics.
        **kwargs : object
            Additional keyword arguments passed by MkDocs (unused; reserved for hook
            compatibility).
        """
        _ = kwargs
        if not self.config.get("enabled", True):
            return
        if not config.repo_url:
            return
        log_mode = self.config.get("log_rewrites", False)
        if not log_mode:
            return

        if log_mode == "verbose":
            for src_path in sorted(self._rewrite_by_page):
                count = self._rewrite_by_page[src_path]
                log.info(
                    "%s: rewrote %d %s",
                    src_path,
                    count,
                    _plural(count, "link"),
                )

        page_count = len(self._rewrite_by_page)
        log.info(
            "Rewrote %d ../ %s across %d %s",
            self._rewrite_total,
            _plural(self._rewrite_total, "link"),
            page_count,
            _plural(page_count, "page"),
        )
