"""Tests for ../ link rewriting."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import REPO
from mkdocs_source_links.ref import ViewRef
from mkdocs_source_links.rewrite import repo_relative_path, rewrite_repo_parent_links
from mkdocs_source_links.urls import detect_forge


def test_repo_relative_path_from_docs(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    assert (
        repo_relative_path(page_abs_path=page, href="../env.example", repo_root=repo_tree)
        == "env.example"
    )


def test_repo_relative_path_to_nested_file(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    assert (
        repo_relative_path(
            page_abs_path=page,
            href="../backend/src/config.py",
            repo_root=repo_tree,
        )
        == "backend/src/config.py"
    )


def test_repo_relative_path_from_nested_docs_page(repo_tree: Path) -> None:
    guide = repo_tree / "docs" / "guide"
    guide.mkdir()
    page = guide / "page.md"
    page.write_text("# Guide\n")
    assert (
        repo_relative_path(
            page_abs_path=page,
            href="../../backend/src/config.py",
            repo_root=repo_tree,
        )
        == "backend/src/config.py"
    )


def test_rewrite_nested_docs_page_parent_links(repo_tree: Path) -> None:
    guide = repo_tree / "docs" / "guide"
    guide.mkdir()
    page = guide / "page.md"
    page.write_text("# Guide\n")
    md = "[cfg](../../backend/src/config.py)."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    assert out == f"[cfg]({REPO}/blob/main/backend/src/config.py)."


def test_repo_relative_path_outside_repo(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    assert (
        repo_relative_path(
            page_abs_path=page,
            href="../../etc/passwd",
            repo_root=repo_tree,
        )
        is None
    )


def test_repo_relative_path_non_parent_href(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    assert repo_relative_path(page_abs_path=page, href="other.md", repo_root=repo_tree) is None


def test_repo_relative_path_filename_starting_with_dot_dot(repo_tree: Path) -> None:
    weird = repo_tree / "..weird"
    weird.mkdir()
    (weird / "file.txt").write_text("x\n")
    page = repo_tree / "docs" / "page.md"
    assert (
        repo_relative_path(
            page_abs_path=page,
            href="../..weird/file.txt",
            repo_root=repo_tree,
        )
        == "..weird/file.txt"
    )


def _require_symlink_support(base: Path) -> None:
    """Skip the calling test when the platform/privilege level can't create symlinks."""
    probe = base / "_symlink_probe"
    try:
        probe.symlink_to(base)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not supported on this platform")
    finally:
        probe.unlink(missing_ok=True)


def test_repo_relative_path_symlinked_repo_root(tmp_path: Path) -> None:
    _require_symlink_support(tmp_path)
    real = tmp_path / "real_repo"
    (real / "docs").mkdir(parents=True)
    (real / "docs" / "page.md").write_text("# Page\n")
    (real / "README.md").write_text("# Readme\n")
    link = tmp_path / "link_repo"
    link.symlink_to(real, target_is_directory=True)
    page = link / "docs" / "page.md"
    assert (
        repo_relative_path(page_abs_path=page, href="../README.md", repo_root=link) == "README.md"
    )


def test_repo_relative_path_in_repo_symlink_target_keeps_lexical_name(repo_tree: Path) -> None:
    _require_symlink_support(repo_tree)
    real = repo_tree / "real_config.py"
    real.write_text("X = 1\n")
    link = repo_tree / "linked_config.py"
    link.symlink_to(real)
    page = repo_tree / "docs" / "page.md"
    assert (
        repo_relative_path(page_abs_path=page, href="../linked_config.py", repo_root=repo_tree)
        == "linked_config.py"
    )


def test_repo_relative_path_symlinked_root_outside_target_rejected(tmp_path: Path) -> None:
    _require_symlink_support(tmp_path)
    real = tmp_path / "real_repo"
    (real / "docs").mkdir(parents=True)
    (real / "docs" / "page.md").write_text("# Page\n")
    (tmp_path / "secret.txt").write_text("nope\n")
    link = tmp_path / "link_repo"
    link.symlink_to(real, target_is_directory=True)
    page = link / "docs" / "page.md"
    assert repo_relative_path(page_abs_path=page, href="../../secret.txt", repo_root=link) is None


def test_rewrite_link_to_filename_starting_with_dot_dot(repo_tree: Path) -> None:
    weird = repo_tree / "..weird"
    weird.mkdir()
    (weird / "file.txt").write_text("x\n")
    md = "[f](../..weird/file.txt)\n"
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=repo_tree / "docs" / "page.md",
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    assert out == f"[f]({REPO}/blob/main/..weird/file.txt)\n"


def test_rewrite_outside_repo_unchanged(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[etc](../../etc/passwd)."
    assert (
        rewrite_repo_parent_links(
            md,
            page_abs_path=page,
            repo_root=repo_tree,
            repo_url=REPO,
            view_ref=ViewRef("main", "branch"),
        )
        == md
    )


def test_report_missing_called_for_missing_target(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[gone](../does_not_exist.py)."
    missing: list[str] = []
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
        report_missing=missing.append,
    )
    assert out == md
    assert missing == ["../does_not_exist.py"]


def test_report_missing_not_called_outside_repo(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[etc](../../etc/does_not_exist)."
    missing: list[str] = []
    rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
        report_missing=missing.append,
    )
    assert not missing


def test_report_rewrite_called_for_inline_link(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[cfg](../env.example)."
    rewrites: list[None] = []
    rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
        report_rewrite=lambda: rewrites.append(None),
    )
    assert len(rewrites) == 1


def test_report_rewrite_called_for_reference_definition(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[cfg]: ../env.example\n"
    rewrites: list[None] = []
    rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
        report_rewrite=lambda: rewrites.append(None),
    )
    assert len(rewrites) == 1


def test_report_rewrite_not_called_for_missing_target(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[gone](../does_not_exist.py)."
    rewrites: list[None] = []
    rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
        report_rewrite=lambda: rewrites.append(None),
    )
    assert not rewrites


def test_report_rewrite_not_called_outside_repo(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[etc](../../etc/passwd)."
    rewrites: list[None] = []
    rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
        report_rewrite=lambda: rewrites.append(None),
    )
    assert not rewrites


def test_report_rewrite_not_called_for_inline_image(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "![alt](../img.png)\n"
    rewrites: list[None] = []
    rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
        report_rewrite=lambda: rewrites.append(None),
    )
    assert not rewrites


def test_report_rewrite_counts_mixed_links(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[a](../env.example) and [b](../src.py)\n\n[c]: ../backend/src/config.py\n"
    rewrites: list[None] = []
    rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
        report_rewrite=lambda: rewrites.append(None),
    )
    assert len(rewrites) == 3


@pytest.mark.parametrize(
    ("md", "kwargs"),
    [
        ("```markdown\n[env](../env.example)\n```\n", {}),
        ("Write `[env](../env.example)` to link a repo file.", {}),
        (
            "[cfg](../backend/src/config.py).",
            {"repo_url": "https://example.com/example/example-repo"},
        ),
        ("![logo][img]\n\n[img]: ../img.png\n", {}),
    ],
    ids=["fenced_code", "inline_code", "unsupported_host", "image_reference_definition"],
)
def test_report_rewrite_not_called_for_skipped_links(
    repo_tree: Path,
    md: str,
    kwargs: dict[str, str],
) -> None:
    page = repo_tree / "docs" / "page.md"
    rewrites: list[None] = []
    rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=kwargs.get("repo_url", REPO),
        view_ref=ViewRef("main", "branch"),
        report_rewrite=lambda: rewrites.append(None),
    )
    assert not rewrites


def test_rewrite_leaves_in_doc_links(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "See [other](other.md#anchor)."
    assert (
        rewrite_repo_parent_links(
            md,
            page_abs_path=page,
            repo_root=repo_tree,
            repo_url=REPO,
            view_ref=ViewRef("main", "branch"),
        )
        == md
    )


def test_rewrite_file_link_to_blob(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[`config.py`](../backend/src/config.py)."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    assert out == (f"[`config.py`]({REPO}/blob/main/backend/src/config.py).")


def test_rewrite_directory_link_to_tree(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[scripts](../scripts/)."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("develop", "branch"),
    )
    assert out == f"[scripts]({REPO}/tree/develop/scripts)."


def test_rewrite_directory_link_without_trailing_slash(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[scripts](../scripts)."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("develop", "branch"),
    )
    assert out == f"[scripts]({REPO}/tree/develop/scripts)."


def test_rewrite_link_with_fragment(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[env](../env.example#section)."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    assert out == f"[env]({REPO}/blob/main/env.example#section)."


def test_rewrite_missing_path_unchanged(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[missing](../no/such/file.py)."
    assert (
        rewrite_repo_parent_links(
            md,
            page_abs_path=page,
            repo_root=repo_tree,
            repo_url=REPO,
            view_ref=ViewRef("main", "branch"),
        )
        == md
    )


def test_rewrite_unsupported_host_unchanged(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[cfg](../backend/src/config.py)."
    unknown = "https://example.com/example/example-repo"
    assert (
        rewrite_repo_parent_links(
            md,
            page_abs_path=page,
            repo_root=repo_tree,
            repo_url=unknown,
            view_ref=ViewRef("main", "branch"),
        )
        == md
    )


def test_rewrite_reports_unknown_forge_for_each_eligible_link(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[a](../src.py) and [b](../env.example)."
    unknown = "https://example.com/example/example-repo"
    warnings: list[None] = []

    def _report() -> None:
        warnings.append(None)

    rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=unknown,
        view_ref=ViewRef("main", "branch"),
        report_unknown_forge=_report,
    )
    assert len(warnings) == 2


def test_rewrite_detects_forge_once_per_page(
    repo_tree: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[a](../src.py) and [b](../env.example)."
    calls: list[str] = []

    def _tracking_detect(repo_url: str) -> str | None:
        calls.append(repo_url)
        return detect_forge(repo_url)

    monkeypatch.setattr("mkdocs_source_links.rewrite.detect_forge", _tracking_detect)

    rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    assert calls == [REPO]


def test_rewrite_reports_skipped_shared_image_ref_label(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[docs][ref]\n![docs]\n\n[docs]: ../img.png\n"
    skipped: list[str] = []

    rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
        report_skipped_shared_label=skipped.append,
    )
    assert skipped == ["docs"]


def test_rewrite_forge_override(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[cfg](../backend/src/config.py)."
    self_hosted = "https://scm.internal.example/example/example-repo"
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=self_hosted,
        view_ref=ViewRef("main", "branch"),
        forge="gitlab",
    )
    assert out == f"[cfg]({self_hosted}/-/blob/main/backend/src/config.py)."


def test_rewrite_skips_fenced_code_block(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "```markdown\n[env](../env.example)\n```\n"
    assert (
        rewrite_repo_parent_links(
            md,
            page_abs_path=page,
            repo_root=repo_tree,
            repo_url=REPO,
            view_ref=ViewRef("main", "branch"),
        )
        == md
    )


def test_rewrite_inside_html_comment_is_rewritten(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "<!-- [env](../env.example) -->\n"
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    assert out == f"<!-- [env]({REPO}/blob/main/env.example) -->\n"


def test_rewrite_reference_definition_inside_html_comment_is_rewritten(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "<!--\n[cfg]: ../backend/src/config.py\n-->\n"
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    assert out == f"<!--\n[cfg]: {REPO}/blob/main/backend/src/config.py\n-->\n"


def test_rewrite_skips_inline_code_span(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "Write `[env](../env.example)` to link a repo file."
    assert (
        rewrite_repo_parent_links(
            md,
            page_abs_path=page,
            repo_root=repo_tree,
            repo_url=REPO,
            view_ref=ViewRef("main", "branch"),
        )
        == md
    )


def test_rewrite_real_link_with_adjacent_code(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = (
        "Example `](../x)` then real [env](../env.example) and:\n\n"
        "```\n[env](../env.example)\n```\n"
    )
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    # Inline code and fenced blocks stay literal; lonely `](../x)` in prose is not matched.
    assert out == (
        f"Example `](../x)` then real [env]({REPO}/blob/main/env.example) and:\n\n"
        "```\n[env](../env.example)\n```\n"
    )


def test_rewrite_titled_link_preserves_title(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = '[env](../env.example "The env file").'
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    assert out == f'[env]({REPO}/blob/main/env.example "The env file").'


def test_rewrite_titled_link_single_quotes(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[env](../env.example 'title')."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    assert out == f"[env]({REPO}/blob/main/env.example 'title')."


def test_rewrite_angle_bracket_link(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[env](<../env.example>)."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    assert out == f"[env]({REPO}/blob/main/env.example)."


def test_rewrite_angle_bracket_link_with_fragment(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[env](<../env.example#section>)."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    assert out == f"[env]({REPO}/blob/main/env.example#section)."


def test_rewrite_angle_bracket_link_with_space(repo_tree: Path) -> None:
    (repo_tree / "my file.py").write_text("X = 1\n")
    page = repo_tree / "docs" / "page.md"
    md = "[f](<../my file.py>)."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    assert out == f"[f]({REPO}/blob/main/my%20file.py)."


def test_rewrite_angle_bracket_link_with_space_and_fragment(repo_tree: Path) -> None:
    (repo_tree / "my file.py").write_text("X = 1\n")
    page = repo_tree / "docs" / "page.md"
    md = "[f](<../my file.py#L2>)."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("main", "branch"),
    )
    assert out == f"[f]({REPO}/blob/main/my%20file.py#L2)."


def test_rewrite_uses_branch(repo_tree: Path) -> None:
    page = repo_tree / "docs" / "page.md"
    md = "[env](../env.example)."
    out = rewrite_repo_parent_links(
        md,
        page_abs_path=page,
        repo_root=repo_tree,
        repo_url=REPO,
        view_ref=ViewRef("master", "branch"),
    )
    assert out == f"[env]({REPO}/blob/master/env.example)."
