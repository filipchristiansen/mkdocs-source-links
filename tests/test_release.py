"""Tests for the two-step release helper (``scripts/release.py``)."""

# These tests deliberately exercise the module's private helpers.
# pylint: disable=protected-access

from __future__ import annotations

import subprocess
import sys
from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
import release

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

PYPROJECT_SAMPLE = '[project]\nname = "demo"\nversion = "0.3.0"\n'

CHANGELOG_SAMPLE = """# Changelog

## [Unreleased]

### Added

- Unreleased thing.

## [0.3.0] - 2026-06-17

### Added

- Released 0.3.0 thing.

## [0.2.0] - 2026-06-16

### Fixed

- Old fix.

[Unreleased]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/filipchristiansen/mkdocs-source-links/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/filipchristiansen/mkdocs-source-links/releases/tag/v0.2.0
"""


def _setup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    pyproject: str = PYPROJECT_SAMPLE,
    changelog: str = CHANGELOG_SAMPLE,
) -> tuple[Path, Path]:
    pyproject_path = tmp_path / "pyproject.toml"
    changelog_path = tmp_path / "CHANGELOG.md"
    pyproject_path.write_text(pyproject)
    changelog_path.write_text(changelog)
    monkeypatch.setattr(release, "PYPROJECT", pyproject_path)
    monkeypatch.setattr(release, "CHANGELOG", changelog_path)
    return pyproject_path, changelog_path


def _recording_run(calls: list[tuple[str, ...]], *, tag_list: str = "") -> Callable[..., str]:
    def fake(*args: str, capture: bool = False) -> str:
        calls.append(args)
        if capture and args[:3] == ("git", "tag", "--list"):
            return tag_list
        return ""

    return fake


# --- pure helpers ---------------------------------------------------------


def test_parse_version_valid() -> None:
    assert release._parse_version("1.2.3") == "1.2.3"


def test_parse_version_invalid() -> None:
    with pytest.raises(SystemExit):
        release._parse_version("1.2")


def test_as_tuple() -> None:
    assert release._as_tuple("0.4.0") == (0, 4, 0)
    assert release._as_tuple("0.10.0") > release._as_tuple("0.9.0")


def test_current_version(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _setup(monkeypatch, tmp_path)
    assert release._current_version() == "0.3.0"


def test_current_version_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _setup(monkeypatch, tmp_path, pyproject='[project]\nname = "demo"\n')
    with pytest.raises(SystemExit):
        release._current_version()


def test_latest_changelog_version(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _setup(monkeypatch, tmp_path)
    assert release._latest_changelog_version() == "0.3.0"


def test_latest_changelog_version_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _setup(monkeypatch, tmp_path, changelog="# Changelog\n\n## [Unreleased]\n")
    with pytest.raises(SystemExit):
        release._latest_changelog_version()


# --- _run -----------------------------------------------------------------


def test_run_capture(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        release.subprocess,
        "run",
        Mock(return_value=SimpleNamespace(stdout="hi\n")),
    )
    assert release._run("anything", capture=True) == "hi"
    assert release._run("anything") == ""


def test_run_command_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(release.subprocess, "run", Mock(side_effect=FileNotFoundError))
    with pytest.raises(SystemExit):
        release._run("missing-binary")


def test_run_called_process_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        release.subprocess,
        "run",
        Mock(side_effect=subprocess.CalledProcessError(2, ["cmd"])),
    )
    with pytest.raises(SystemExit):
        release._run("cmd")


def test_ensure_clean_tree_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(release, "_run", _recording_run([]))
    release._ensure_clean_tree()


def test_ensure_clean_tree_dirty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(release, "_run", lambda *a, **k: " M file.py")  # noqa: ARG005
    with pytest.raises(SystemExit):
        release._ensure_clean_tree()


# --- _extract_notes -------------------------------------------------------


def test_extract_notes_stops_at_next_heading(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _setup(monkeypatch, tmp_path)
    notes = release._extract_notes("0.3.0")
    assert "Released 0.3.0 thing." in notes
    assert "Old fix." not in notes


def test_extract_notes_stops_at_link_defs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _setup(monkeypatch, tmp_path)
    notes = release._extract_notes("0.2.0")
    assert notes == "### Fixed\n\n- Old fix."
    assert "compare/" not in notes


def test_extract_notes_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _setup(monkeypatch, tmp_path)
    with pytest.raises(SystemExit):
        release._extract_notes("9.9.9")


# --- _compare_link --------------------------------------------------------


def test_compare_link(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _setup(monkeypatch, tmp_path)
    assert release._compare_link("0.3.0").endswith("/compare/v0.2.0...v0.3.0")


def test_compare_link_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _setup(monkeypatch, tmp_path)
    with pytest.raises(SystemExit):
        release._compare_link("9.9.9")


# --- _bump_pyproject ------------------------------------------------------


def test_bump_pyproject(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    pyproject_path, _ = _setup(monkeypatch, tmp_path)
    release._bump_pyproject("0.4.0")
    assert 'version = "0.4.0"' in pyproject_path.read_text()


def test_bump_pyproject_no_match(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _setup(monkeypatch, tmp_path, pyproject='[project]\nname = "demo"\n')
    with pytest.raises(SystemExit):
        release._bump_pyproject("0.4.0")


# --- _roll_changelog ------------------------------------------------------


def test_roll_changelog(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _, changelog_path = _setup(monkeypatch, tmp_path)
    release._roll_changelog("0.4.0", "0.3.0")
    text = changelog_path.read_text()

    assert "## [0.4.0] - " in text
    assert "- Unreleased thing." in text
    # A fresh, empty Unreleased section sits above the new version.
    assert text.index("## [Unreleased]") < text.index("## [0.4.0]")
    base = release.COMPARE_URL
    assert f"[Unreleased]: {base}/v0.4.0...HEAD" in text
    assert f"[0.4.0]: {base}/v0.3.0...v0.4.0" in text


def test_roll_changelog_no_unreleased(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    changelog = "# Changelog\n\n## [0.3.0] - 2026-06-17\n\n- x.\n\n[0.3.0]: url\n"
    _setup(monkeypatch, tmp_path, changelog=changelog)
    with pytest.raises(SystemExit):
        release._roll_changelog("0.4.0", "0.3.0")


def test_roll_changelog_empty_unreleased(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    changelog = (
        "# Changelog\n\n## [Unreleased]\n\n## [0.3.0] - 2026-06-17\n\n- x.\n\n[0.3.0]: url\n"
    )
    _setup(monkeypatch, tmp_path, changelog=changelog)
    with pytest.raises(SystemExit):
        release._roll_changelog("0.4.0", "0.3.0")


def test_roll_changelog_no_link(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    changelog = "# Changelog\n\n## [Unreleased]\n\n- thing.\n\n## [0.3.0] - 2026-06-17\n\n- x.\n"
    _setup(monkeypatch, tmp_path, changelog=changelog)
    with pytest.raises(SystemExit):
        release._roll_changelog("0.4.0", "0.3.0")


# --- _cmd_prep ------------------------------------------------------------


def test_cmd_prep(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    pyproject_path, changelog_path = _setup(monkeypatch, tmp_path)
    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(release, "_run", _recording_run(calls))

    release._cmd_prep("0.4.0")

    assert 'version = "0.4.0"' in pyproject_path.read_text()
    assert "## [0.4.0] - " in changelog_path.read_text()
    assert ("make", "ci") in calls
    assert ("git", "add", "pyproject.toml", "CHANGELOG.md", "uv.lock") in calls
    assert any(call[:3] == ("gh", "pr", "create") for call in calls)
    assert any(call[:2] == ("git", "push") for call in calls)


def test_cmd_prep_not_greater(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _setup(monkeypatch, tmp_path)
    monkeypatch.setattr(release, "_run", _recording_run([]))
    with pytest.raises(SystemExit):
        release._cmd_prep("0.3.0")


def test_cmd_prep_changelog_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    changelog = CHANGELOG_SAMPLE.replace("## [0.3.0] - 2026-06-17", "## [0.2.5] - 2026-06-17", 1)
    _setup(monkeypatch, tmp_path, changelog=changelog)
    monkeypatch.setattr(release, "_run", _recording_run([]))
    with pytest.raises(SystemExit):
        release._cmd_prep("0.4.0")


# --- _cmd_tag -------------------------------------------------------------


def test_cmd_tag(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    base = "https://github.com/filipchristiansen/mkdocs-source-links/compare"
    changelog = (
        CHANGELOG_SAMPLE.replace("## [Unreleased]\n\n", "", 1)
        .replace("## [0.3.0] - 2026-06-17", "## [0.4.0] - 2026-06-18", 1)
        .replace(f"[0.3.0]: {base}/v0.2.0...v0.3.0", f"[0.4.0]: {base}/v0.3.0...v0.4.0", 1)
    )
    _setup(
        monkeypatch,
        tmp_path,
        pyproject='[project]\nname = "demo"\nversion = "0.4.0"\n',
        changelog=changelog,
    )
    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(release, "_run", _recording_run(calls))

    release._cmd_tag("0.4.0")

    assert ("git", "tag", "-a", "v0.4.0", "-m", "v0.4.0") in calls
    release_call = next(call for call in calls if call[:3] == ("gh", "release", "create"))
    notes = release_call[-1]
    assert f"**Full changelog:** {base}/v0.3.0...v0.4.0" in notes


def test_cmd_tag_version_mismatch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _setup(monkeypatch, tmp_path)
    monkeypatch.setattr(release, "_run", _recording_run([]))
    with pytest.raises(SystemExit):
        release._cmd_tag("0.4.0")


def test_cmd_tag_existing_tag(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _setup(monkeypatch, tmp_path, pyproject='[project]\nname = "demo"\nversion = "0.4.0"\n')
    monkeypatch.setattr(release, "_run", _recording_run([], tag_list="v0.4.0"))
    with pytest.raises(SystemExit):
        release._cmd_tag("0.4.0")


# --- main -----------------------------------------------------------------


def test_main_prep(monkeypatch: pytest.MonkeyPatch) -> None:
    recorded: list[str] = []
    monkeypatch.setattr(release, "_cmd_prep", recorded.append)
    monkeypatch.setattr(sys, "argv", ["release", "prep", "0.4.0"])
    release.main()
    assert recorded == ["0.4.0"]


def test_main_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    recorded: list[str] = []
    monkeypatch.setattr(release, "_cmd_tag", recorded.append)
    monkeypatch.setattr(sys, "argv", ["release", "tag", "0.4.0"])
    release.main()
    assert recorded == ["0.4.0"]
