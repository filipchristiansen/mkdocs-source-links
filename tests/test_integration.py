"""Integration tests: plugin rewrites links in real mkdocs builds."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

PluginOption = bool | str


def _setup_doc_site(root: Path) -> None:
    docs = root / "docs"
    docs.mkdir()
    (docs / "index.md").write_text(
        "See [config](../backend/config.py) and [scripts](../scripts/).\n"
    )
    backend = root / "backend"
    backend.mkdir()
    (backend / "config.py").write_text("X = 1\n")
    (root / "scripts").mkdir()


def _yaml_scalar(value: PluginOption) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _write_mkdocs_yml(
    root: Path,
    *,
    repo_url: str = "https://github.com/example/test-repo",
    edit_uri: str = "edit/main/docs/",
    plugin_options: dict[str, PluginOption] | None = None,
) -> None:
    lines = [
        "site_name: test",
        f"repo_url: {repo_url}",
        f"edit_uri: {edit_uri}",
        "plugins:",
    ]
    if plugin_options:
        lines.append("  - source-links:")
        for key, value in plugin_options.items():
            lines.append(f"      {key}: {_yaml_scalar(value)}")
    else:
        lines.append("  - source-links")
    lines.append("")
    (root / "mkdocs.yml").write_text("\n".join(lines))


def _run_mkdocs_build(root: Path) -> str:
    site = root / "site"
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "-d", str(site)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return (site / "index.html").read_text()


@pytest.mark.parametrize(
    ("repo_url", "edit_uri", "file_url_fragment", "dir_url_fragment"),
    [
        (
            "https://github.com/example/test-repo",
            "edit/main/docs/",
            "github.com/example/test-repo/blob/main/backend/config.py",
            "github.com/example/test-repo/tree/main/scripts",
        ),
        (
            "https://gitlab.com/example/test-repo",
            "-/edit/main/docs/",
            "gitlab.com/example/test-repo/-/blob/main/backend/config.py",
            "gitlab.com/example/test-repo/-/tree/main/scripts",
        ),
    ],
)
def test_mkdocs_build_rewrites_parent_links_by_forge(
    tmp_path: Path,
    repo_url: str,
    edit_uri: str,
    file_url_fragment: str,
    dir_url_fragment: str,
) -> None:
    _setup_doc_site(tmp_path)
    _write_mkdocs_yml(tmp_path, repo_url=repo_url, edit_uri=edit_uri)

    html = _run_mkdocs_build(tmp_path)

    assert file_url_fragment in html
    assert dir_url_fragment in html
