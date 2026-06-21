"""Integration tests: plugin rewrites links in real mkdocs builds."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from git_utils import init_git_repo

PluginOption = bool | str


def _setup_nested_doc_site(root: Path) -> None:
    guide = root / "docs" / "guide"
    guide.mkdir(parents=True)
    (guide / "page.md").write_text("[cfg](../../backend/config.py)\n")
    backend = root / "backend"
    backend.mkdir()
    (backend / "config.py").write_text("X = 1\n")


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
    _run_mkdocs_build_site(root)
    return (root / "site" / "index.html").read_text()


def _run_mkdocs_build_site(root: Path) -> None:
    site = root / "site"
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "-d", str(site)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def _run_mkdocs_build_stderr(root: Path, *, quiet: bool = False) -> str:
    site = root / "site"
    cmd = [sys.executable, "-m", "mkdocs", "build"]
    if quiet:
        cmd.append("-q")
    cmd.extend(["-d", str(site)])
    result = subprocess.run(
        cmd,
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stderr


@pytest.mark.parametrize(
    ("repo_url", "edit_uri", "file_url", "dir_url"),
    [
        (
            "https://github.com/example/test-repo",
            "edit/main/docs/",
            "https://github.com/example/test-repo/blob/main/backend/config.py",
            "https://github.com/example/test-repo/tree/main/scripts",
        ),
        (
            "https://gitlab.com/example/test-repo",
            "-/edit/main/docs/",
            "https://gitlab.com/example/test-repo/-/blob/main/backend/config.py",
            "https://gitlab.com/example/test-repo/-/tree/main/scripts",
        ),
        (
            "https://bitbucket.org/example/test-repo",
            "src/main/docs/",
            "https://bitbucket.org/example/test-repo/src/main/backend/config.py",
            "https://bitbucket.org/example/test-repo/src/main/scripts",
        ),
    ],
)
def test_mkdocs_build_rewrites_parent_links_by_forge(
    tmp_path: Path,
    repo_url: str,
    edit_uri: str,
    file_url: str,
    dir_url: str,
) -> None:
    _setup_doc_site(tmp_path)
    _write_mkdocs_yml(tmp_path, repo_url=repo_url, edit_uri=edit_uri)

    html = _run_mkdocs_build(tmp_path)

    assert f'href="{file_url}"' in html
    assert f'href="{dir_url}"' in html


def test_mkdocs_build_bitbucket_src_edit_uri_uses_branch_from_path(tmp_path: Path) -> None:
    _setup_doc_site(tmp_path)
    _write_mkdocs_yml(
        tmp_path,
        repo_url="https://bitbucket.org/example/test-repo",
        edit_uri="src/develop/docs/",
    )

    html = _run_mkdocs_build(tmp_path)

    assert 'href="https://bitbucket.org/example/test-repo/src/develop/backend/config.py"' in html
    assert 'href="https://bitbucket.org/example/test-repo/src/develop/scripts"' in html


def test_mkdocs_build_pin_commit_uses_head_sha(tmp_path: Path, git_exe: str) -> None:
    _setup_doc_site(tmp_path)
    sha = init_git_repo(tmp_path, git_exe)
    _write_mkdocs_yml(tmp_path, plugin_options={"pin": "commit"})

    html = _run_mkdocs_build(tmp_path)

    assert f'href="https://github.com/example/test-repo/blob/{sha}/backend/config.py"' in html
    assert f'href="https://github.com/example/test-repo/tree/{sha}/scripts"' in html


def test_mkdocs_build_pin_tag_uses_exact_tag(tmp_path: Path, git_exe: str) -> None:
    _setup_doc_site(tmp_path)
    init_git_repo(tmp_path, git_exe)
    subprocess.run([git_exe, "tag", "v1.0.0"], cwd=tmp_path, check=True)
    _write_mkdocs_yml(tmp_path, plugin_options={"pin": "tag"})

    html = _run_mkdocs_build(tmp_path)

    assert 'href="https://github.com/example/test-repo/blob/v1.0.0/backend/config.py"' in html
    assert 'href="https://github.com/example/test-repo/tree/v1.0.0/scripts"' in html


def test_mkdocs_build_pin_tag_uses_exact_tag_on_codeberg(tmp_path: Path, git_exe: str) -> None:
    _setup_doc_site(tmp_path)
    init_git_repo(tmp_path, git_exe)
    subprocess.run([git_exe, "tag", "v1.0.0"], cwd=tmp_path, check=True)
    _write_mkdocs_yml(
        tmp_path,
        repo_url="https://codeberg.org/example/test-repo",
        edit_uri="main/docs/",
        plugin_options={"pin": "tag"},
    )

    html = _run_mkdocs_build(tmp_path)

    assert 'href="https://codeberg.org/example/test-repo/src/tag/v1.0.0/backend/config.py"' in html
    assert 'href="https://codeberg.org/example/test-repo/src/tag/v1.0.0/scripts"' in html


def test_mkdocs_build_azure_branch_uses_gb_version(tmp_path: Path) -> None:
    _setup_doc_site(tmp_path)
    _write_mkdocs_yml(
        tmp_path,
        repo_url="https://dev.azure.com/org/project/_git/test-repo",
        plugin_options={"branch": "main", "forge": "azure"},
    )

    html = _run_mkdocs_build(tmp_path)

    azure_file = (
        "https://dev.azure.com/org/project/_git/test-repo"
        "?path=/backend/config.py&amp;version=GBmain"
    )
    assert f'href="{azure_file}"' in html


def test_mkdocs_build_pin_tag_uses_gt_on_azure(tmp_path: Path, git_exe: str) -> None:
    _setup_doc_site(tmp_path)
    init_git_repo(tmp_path, git_exe)
    subprocess.run([git_exe, "tag", "v1.0.0"], cwd=tmp_path, check=True)
    _write_mkdocs_yml(
        tmp_path,
        repo_url="https://dev.azure.com/org/project/_git/test-repo",
        plugin_options={"pin": "tag", "forge": "azure"},
    )

    html = _run_mkdocs_build(tmp_path)

    azure_file = (
        "https://dev.azure.com/org/project/_git/test-repo"
        "?path=/backend/config.py&amp;version=GTv1.0.0"
    )
    assert f'href="{azure_file}"' in html


def test_mkdocs_build_enabled_false_leaves_links_unchanged(tmp_path: Path) -> None:
    _setup_doc_site(tmp_path)
    _write_mkdocs_yml(tmp_path, plugin_options={"enabled": False})

    html = _run_mkdocs_build(tmp_path)

    assert "../backend/config.py" in html
    assert "../scripts/" in html
    assert "github.com/example/test-repo/blob" not in html


def test_mkdocs_build_rewrites_reference_definitions(tmp_path: Path) -> None:
    _setup_doc_site(tmp_path)
    (tmp_path / "docs" / "index.md").write_text(
        "See [config][cfg].\n\n[cfg]: ../backend/config.py\n"
    )
    _write_mkdocs_yml(tmp_path)

    html = _run_mkdocs_build(tmp_path)

    assert 'href="https://github.com/example/test-repo/blob/main/backend/config.py"' in html
    assert "../backend/config.py" not in html


def test_mkdocs_build_rewrites_nested_docs_page_links(tmp_path: Path) -> None:
    _setup_nested_doc_site(tmp_path)
    (tmp_path / "mkdocs.yml").write_text(
        """site_name: test
repo_url: https://github.com/example/test-repo
edit_uri: edit/main/docs/
nav:
  - Guide: guide/page.md
plugins:
  - source-links
"""
    )

    _run_mkdocs_build_site(tmp_path)
    html = (tmp_path / "site" / "guide" / "page" / "index.html").read_text()

    assert 'href="https://github.com/example/test-repo/blob/main/backend/config.py"' in html
    assert "../../backend/config.py" not in html


def test_mkdocs_build_warn_on_missing_target(tmp_path: Path) -> None:
    _setup_doc_site(tmp_path)
    (tmp_path / "docs" / "index.md").write_text("[gone](../missing.py)\n")
    _write_mkdocs_yml(tmp_path)

    stderr = _run_mkdocs_build_stderr(tmp_path)

    assert "does not exist" in stderr
    assert "missing.py" in stderr


def test_mkdocs_build_pin_commit_fallback_warns_without_git_repo(tmp_path: Path) -> None:
    _setup_doc_site(tmp_path)
    _write_mkdocs_yml(tmp_path, plugin_options={"pin": "commit"})

    stderr = _run_mkdocs_build_stderr(tmp_path)

    assert "could not be resolved via git" in stderr
    html = (tmp_path / "site" / "index.html").read_text()
    assert 'href="https://github.com/example/test-repo/blob/main/backend/config.py"' in html


def test_mkdocs_build_forge_override_on_custom_host(tmp_path: Path) -> None:
    _setup_doc_site(tmp_path)
    _write_mkdocs_yml(
        tmp_path,
        repo_url="https://scm.internal.example/org/test-repo",
        edit_uri="-/edit/main/docs/",
        plugin_options={"forge": "gitlab"},
    )

    html = _run_mkdocs_build(tmp_path)

    assert "scm.internal.example/org/test-repo/-/blob/main/backend/config.py" in html
    assert "scm.internal.example/org/test-repo/-/tree/main/scripts" in html


def test_mkdocs_build_log_rewrites_summary(tmp_path: Path) -> None:
    _setup_doc_site(tmp_path)
    _write_mkdocs_yml(tmp_path, plugin_options={"log_rewrites": "summary"})

    stderr = _run_mkdocs_build_stderr(tmp_path)

    assert "Rewrote 2 links across 1 page" in stderr


def test_mkdocs_build_log_rewrites_verbose(tmp_path: Path) -> None:
    _setup_doc_site(tmp_path)
    _write_mkdocs_yml(tmp_path, plugin_options={"log_rewrites": "verbose"})

    stderr = _run_mkdocs_build_stderr(tmp_path)

    assert "index.md: rewrote 2 links" in stderr
    assert "Rewrote 2 links across 1 page" in stderr


def test_mkdocs_build_log_rewrites_silent_with_quiet_flag(tmp_path: Path) -> None:
    _setup_doc_site(tmp_path)
    _write_mkdocs_yml(tmp_path, plugin_options={"log_rewrites": "summary"})

    stderr = _run_mkdocs_build_stderr(tmp_path, quiet=True)

    assert "Rewrote" not in stderr


def test_mkdocs_build_log_rewrites_silent_without_repo_url(tmp_path: Path) -> None:
    _setup_doc_site(tmp_path)
    (tmp_path / "mkdocs.yml").write_text(
        """site_name: test
plugins:
  - source-links:
      log_rewrites: summary
"""
    )

    stderr = _run_mkdocs_build_stderr(tmp_path)

    assert "Rewrote" not in stderr


def test_mkdocs_build_pin_tag_fallback_warns_when_head_not_tagged(
    tmp_path: Path, git_exe: str
) -> None:
    _setup_doc_site(tmp_path)
    init_git_repo(tmp_path, git_exe)
    _write_mkdocs_yml(tmp_path, plugin_options={"pin": "tag"})

    stderr = _run_mkdocs_build_stderr(tmp_path)

    assert "could not be resolved via git" in stderr
    html = (tmp_path / "site" / "index.html").read_text()
    assert 'href="https://github.com/example/test-repo/blob/main/backend/config.py"' in html


@pytest.mark.parametrize(
    ("repo_url", "edit_uri", "file_url"),
    [
        (
            "https://github.com/example/test-repo",
            "edit/main/docs/",
            "https://github.com/example/test-repo/blob/main/backend/config.py#L1-L2",
        ),
        (
            "https://gitlab.com/example/test-repo",
            "-/edit/main/docs/",
            "https://gitlab.com/example/test-repo/-/blob/main/backend/config.py#L1-2",
        ),
        (
            "https://bitbucket.org/example/test-repo",
            "src/main/docs/",
            "https://bitbucket.org/example/test-repo/src/main/backend/config.py#lines-1:2",
        ),
    ],
)
def test_mkdocs_build_translates_line_fragment_by_forge(
    tmp_path: Path,
    repo_url: str,
    edit_uri: str,
    file_url: str,
) -> None:
    _setup_doc_site(tmp_path)
    (tmp_path / "docs" / "index.md").write_text("See [config](../backend/config.py#L1-L2).\n")
    _write_mkdocs_yml(tmp_path, repo_url=repo_url, edit_uri=edit_uri)

    html = _run_mkdocs_build(tmp_path)

    assert f'href="{file_url}"' in html


def test_mkdocs_build_normalizes_repo_url_git_suffix_and_query(tmp_path: Path) -> None:
    _setup_doc_site(tmp_path)
    _write_mkdocs_yml(tmp_path, repo_url="https://github.com/example/test-repo.git?foo=bar")

    html = _run_mkdocs_build(tmp_path)

    assert 'href="https://github.com/example/test-repo/blob/main/backend/config.py"' in html
    assert "test-repo.git" not in html


def test_mkdocs_build_rewrites_link_with_escaped_parens(tmp_path: Path) -> None:
    _setup_doc_site(tmp_path)
    (tmp_path / "backend" / "weird(name).py").write_text("X = 1\n")
    (tmp_path / "docs" / "index.md").write_text(r"See [w](../backend/weird\(name\).py)." + "\n")
    _write_mkdocs_yml(tmp_path)

    html = _run_mkdocs_build(tmp_path)

    assert (
        'href="https://github.com/example/test-repo/blob/main/backend/weird%28name%29.py"' in html
    )
