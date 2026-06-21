"""Detect fenced code blocks and iterate markdown lines/runs by fence state."""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass

_FENCE_OPEN = re.compile(r"^[ \t]*(?P<marker>`{3,}|~{3,})(?P<rest>.*)$")


def _fence_closes_line(body: str, *, char: str, min_len: int) -> bool:
    """Return whether ``body`` closes a fence opened with ``char`` repeated ``min_len`` times."""
    return re.match(rf"^[ \t]*({re.escape(char)}{{{min_len},}})[ \t]*$", body) is not None


def _fence_closes_on_same_line(*, marker: str, rest: str) -> bool:
    """Return whether a fence opener and closer appear on the same line."""
    if not rest.strip():
        return False
    char = marker[0]
    min_len = len(marker)
    trailing = re.search(rf"({re.escape(char)}{{{min_len},}})\s*$", rest)
    return trailing is not None


@dataclass(frozen=True)
class _FencedLine:
    raw: str
    body: str
    in_fence: bool

    @property
    def suffix(self) -> str:
        """Return line-ending characters stripped from :attr:`body`."""
        return self.raw[len(self.body) :]


def iter_fenced_lines(markdown: str) -> Iterator[_FencedLine]:
    """Yield each line with whether it lies inside a fenced code block."""
    in_fence = False
    fence_char = ""
    fence_min_len = 0

    for raw_line in markdown.splitlines(keepends=True):
        body = raw_line.rstrip("\r\n")

        if in_fence:
            yield _FencedLine(raw_line, body, in_fence=True)
            if _fence_closes_line(body, char=fence_char, min_len=fence_min_len):
                in_fence = False
                fence_char = ""
                fence_min_len = 0
            continue

        if open_m := _FENCE_OPEN.match(body):
            marker = open_m.group("marker")
            if not _fence_closes_on_same_line(marker=marker, rest=open_m.group("rest")):
                in_fence = True
                fence_char = marker[0]
                fence_min_len = len(marker)
                yield _FencedLine(raw_line, body, in_fence=True)
                continue

        yield _FencedLine(raw_line, body, in_fence=False)


def iter_fence_runs(markdown: str) -> Iterator[tuple[str, bool]]:
    """Yield maximal contiguous markdown runs and whether each run is inside a fence."""
    run: list[str] = []
    run_in_fence = False
    have_run = False

    for line in iter_fenced_lines(markdown):
        if have_run and line.in_fence != run_in_fence:
            yield "".join(run), run_in_fence
            run.clear()
        have_run = True
        run_in_fence = line.in_fence
        run.append(line.raw)

    if have_run:
        yield "".join(run), run_in_fence
