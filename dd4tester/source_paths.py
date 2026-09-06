"""Resolve and pin the DD4 source snapshot used by a campaign.

The default remains repository-relative for existing scenario and campaign
files.  A running campaign can install an explicit source directory in a
context-local scope so every source-backed planner sees the same snapshot.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Iterator


DEFAULT_SOURCE_DIRECTORY = Path("runs/dd4-source/server/area")

_CURRENT_SOURCE_DIRECTORY: ContextVar[Path | None] = ContextVar(
    "dd4tester_current_source_directory",
    default=None,
)


def current_source_directory() -> Path:
    """Return the source area directory for the current execution scope."""
    return _CURRENT_SOURCE_DIRECTORY.get() or DEFAULT_SOURCE_DIRECTORY


@contextmanager
def source_directory_context(directory: Path | str | None) -> Iterator[Path]:
    """Pin one source area directory for all nested source-backed helpers."""
    selected = (
        Path(directory)
        if directory is not None
        else DEFAULT_SOURCE_DIRECTORY
    )
    token = _CURRENT_SOURCE_DIRECTORY.set(selected)
    try:
        yield selected
    finally:
        _CURRENT_SOURCE_DIRECTORY.reset(token)
