#!/usr/bin/env python3
"""Two-step release helper.

The changelog is always hand-written: you keep an ``## [Unreleased]`` section
curated by hand. This script only handles the mechanics — version bump,
promoting ``[Unreleased]`` to a dated section, maintaining the compare-link
footer, opening the release PR, creating a signed tag, and creating the GitHub release. It
never generates release-note prose.

Usage
-----
    # Step 1 (before merge): open the release PR off the latest main.
    python scripts/release.py prep 0.4.0

    # Step 2 (after the PR merges): signed tag, push, and create the GitHub release.
    python scripts/release.py tag 0.4.0
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

REPO = "filipchristiansen/mkdocs-source-links"
COMPARE_URL = f"https://github.com/{REPO}/compare"

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
CHANGELOG = ROOT / "CHANGELOG.md"

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
VERSION_LINE_RE = re.compile(r'(?m)^version = "(?P<version>[^"]+)"')
HEADING_RE = re.compile(r"(?m)^## \[(?P<version>\d+\.\d+\.\d+)\]")
UNRELEASED_BODY_RE = re.compile(r"## \[Unreleased\]\n(?P<body>.*?)(?=\n## \[)", re.DOTALL)
UNRELEASED_LINK_RE = re.compile(r"(?m)^\[Unreleased\]: .*$")


def _fail(message: str) -> NoReturn:
    """Print an error and exit non-zero.

    Parameters
    ----------
    message : str
        The error message to display.

    Raises
    ------
    SystemExit
        Always exits with status 1.
    """
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def _run(*args: str, capture: bool = False) -> str:
    """Run a command, echoing it first.

    Parameters
    ----------
    *args : str
        The command and its arguments.
    capture : bool
        When True, return captured stdout instead of streaming it.

    Returns
    -------
    str
        The captured stdout (stripped) when ``capture`` is True, else "".
    """
    print(f"$ {' '.join(args)}")
    try:
        result = subprocess.run(args, check=True, text=True, capture_output=capture)
    except FileNotFoundError:
        _fail(f"command not found: {args[0]}")
    except subprocess.CalledProcessError as exc:
        _fail(f"command failed (exit {exc.returncode}): {' '.join(args)}")
    return result.stdout.strip() if capture else ""


def _parse_version(value: str) -> str:
    """Validate a semver string.

    Parameters
    ----------
    value : str
        The version to validate (e.g. ``0.4.0``).

    Returns
    -------
    str
        The validated version.
    """
    if not SEMVER_RE.match(value):
        _fail(f"version must be X.Y.Z, got {value!r}")
    return value


def _as_tuple(version: str) -> tuple[int, ...]:
    """Convert a semver string to a comparable tuple.

    Parameters
    ----------
    version : str
        A validated ``X.Y.Z`` version.

    Returns
    -------
    tuple[int, ...]
        The numeric components for ordering comparisons.
    """
    return tuple(int(part) for part in version.split("."))


def _current_version() -> str:
    """Read the version currently declared in ``pyproject.toml``.

    Returns
    -------
    str
        The current project version.
    """
    match = VERSION_LINE_RE.search(PYPROJECT.read_text())
    if match is None:
        _fail("could not find version in pyproject.toml")
    return match.group("version")


def _latest_changelog_version() -> str:
    """Return the most recent released version from the changelog.

    Returns
    -------
    str
        The newest ``## [X.Y.Z]`` heading, used as the compare base.
    """
    match = HEADING_RE.search(CHANGELOG.read_text())
    if match is None:
        _fail("no released version heading found in CHANGELOG.md")
    return match.group("version")


def _ensure_clean_tree() -> None:
    """Abort unless the working tree is clean."""
    if _run("git", "status", "--porcelain", capture=True):
        _fail("working tree is not clean; commit or stash first")


def _extract_notes(version: str) -> str:
    """Return the body of a versioned changelog section.

    Parameters
    ----------
    version : str
        The version whose section body to extract.

    Returns
    -------
    str
        The section body (without the heading), used as PR / release notes.
    """
    pattern = re.compile(
        rf"## \[{re.escape(version)}\][^\n]*\n(?P<body>.*?)(?=\n## \[|\n\[[^\]]+\]: )",
        re.DOTALL,
    )
    match = pattern.search(CHANGELOG.read_text())
    if match is None:
        _fail(f"no changelog section found for {version}")
    return match.group("body").strip()


def _compare_link(version: str) -> str:
    """Return the compare URL for a version from the changelog link footer.

    Parameters
    ----------
    version : str
        The version whose ``[version]: <url>`` link definition to read.

    Returns
    -------
    str
        The compare URL (e.g. ``.../compare/v0.3.0...v0.4.0``).
    """
    pattern = re.compile(rf"(?m)^\[{re.escape(version)}\]: (?P<url>.+)$")
    match = pattern.search(CHANGELOG.read_text())
    if match is None:
        _fail(f"no compare link found for {version} in CHANGELOG.md")
    return match.group("url").strip()


def _bump_pyproject(version: str) -> None:
    """Set the project version in ``pyproject.toml``.

    Parameters
    ----------
    version : str
        The new version to write.
    """
    text = PYPROJECT.read_text()
    new_text, count = VERSION_LINE_RE.subn(f'version = "{version}"', text, count=1)
    if count != 1:
        _fail("could not update version in pyproject.toml")
    PYPROJECT.write_text(new_text)


def _roll_changelog(version: str, prev: str) -> None:
    """Promote ``[Unreleased]`` to a dated section and fix compare links.

    Parameters
    ----------
    version : str
        The version being released.
    prev : str
        The previous released version (the compare base).
    """
    text = CHANGELOG.read_text()
    today = dt.date.today().isoformat()

    body_match = UNRELEASED_BODY_RE.search(text)
    if body_match is None:
        _fail("could not locate the [Unreleased] section in CHANGELOG.md")
    body = body_match.group("body").strip("\n")
    if not body.strip():
        _fail("the [Unreleased] section is empty; nothing to release")

    new_block = f"## [Unreleased]\n\n## [{version}] - {today}\n\n{body}\n"
    text = UNRELEASED_BODY_RE.sub(lambda _: new_block, text, count=1)

    new_links = (
        f"[Unreleased]: {COMPARE_URL}/v{version}...HEAD\n"
        f"[{version}]: {COMPARE_URL}/v{prev}...v{version}"
    )
    text, count = UNRELEASED_LINK_RE.subn(new_links, text, count=1)
    if count != 1:
        _fail("could not find the [Unreleased] compare link in CHANGELOG.md")

    CHANGELOG.write_text(text)


def _cmd_prep(version: str) -> None:
    """Run step 1: bump, roll changelog, validate, and open the release PR.

    Parameters
    ----------
    version : str
        The version to prepare.
    """
    _ensure_clean_tree()
    _run("git", "fetch", "origin", "main", "--tags")

    prev = _current_version()
    if _as_tuple(version) <= _as_tuple(prev):
        _fail(f"{version} is not greater than current version {prev}")

    branch = f"release/v{version}"
    _run("git", "checkout", "-B", branch, "origin/main")

    changelog_prev = _latest_changelog_version()
    if changelog_prev != prev:
        _fail(
            f"pyproject version {prev} disagrees with latest changelog version "
            f"{changelog_prev}; reconcile before releasing"
        )

    _bump_pyproject(version)
    _roll_changelog(version, prev)

    _run("make", "ci")

    _run("git", "add", "pyproject.toml", "CHANGELOG.md", "uv.lock")
    _run("git", "commit", "-m", f"chore: release v{version}")
    _run("git", "push", "-u", "origin", branch)

    notes = _extract_notes(version)
    _run(
        "gh",
        "pr",
        "create",
        "--base",
        "main",
        "--head",
        branch,
        "--title",
        f"release: v{version}",
        "--label",
        "release",
        "--body",
        notes,
    )
    print(f"\nrelease PR opened for v{version}. Merge it, then run:")
    print(f"  make release-tag VERSION={version}")


def _cmd_tag(version: str) -> None:
    """Run step 2: tag the merged release and create the GitHub release.

    Parameters
    ----------
    version : str
        The version to tag and publish.
    """
    _ensure_clean_tree()
    _run("git", "fetch", "origin", "main", "--tags")
    _run("git", "checkout", "main")
    _run("git", "pull", "--ff-only", "origin", "main")

    on_main = _current_version()
    if on_main != version:
        _fail(f"main has version {on_main}, not {version}; is the release PR merged?")

    tag = f"v{version}"
    existing = _run("git", "tag", "--list", tag, capture=True)
    if existing:
        _fail(f"tag {tag} already exists")

    notes = f"{_extract_notes(version)}\n\n**Full changelog:** {_compare_link(version)}"
    _run("git", "tag", "-s", tag, "-m", notes)
    _run("git", "push", "origin", tag)
    print(
        f"\nsigned and pushed {tag}. "
        "The Publish workflow will push to PyPI and create the GitHub release "
        "with SLSA provenance and distribution archives."
    )


def main() -> None:
    """Parse arguments and dispatch to the requested step."""
    parser = argparse.ArgumentParser(description="Two-step release helper.")
    sub = parser.add_subparsers(dest="command", required=True)

    prep = sub.add_parser("prep", help="bump, roll changelog, open release PR")
    prep.add_argument("version", type=_parse_version)

    tag = sub.add_parser("tag", help="signed tag + GitHub release for merged version")
    tag.add_argument("version", type=_parse_version)

    args = parser.parse_args()
    if args.command == "prep":
        _cmd_prep(args.version)
    else:
        _cmd_tag(args.version)


if __name__ == "__main__":
    main()
