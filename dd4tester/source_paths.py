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

# The live server is currently deployed before the upstream undead and
# archetype/species rollout.  Keep the latest checkout available for source
# research, but do not let these newer templates authorize a live hunt until
# a live probe proves that deployment has caught up.
LIVE_UNDEPLOYED_TEMPLATE_NAMES = frozenset(
    {
        "animated_soft_toy",
        "animated_toy_soldier",
        "banshee",
        "death_knight",
        "dracolich",
        "dwarf",
        "dwarf_untrained",
        "goblin",
        "half_orc",
        "hobgoblin",
        "lich",
        "mummy",
        "ogre_mage",
        "troll",
        "vampire",
        "vampire_bat_form",
    }
)

_CURRENT_SOURCE_DIRECTORY: ContextVar[Path | None] = ContextVar(
    "dd4tester_current_source_directory",
    default=None,
)
_CURRENT_LIVE_DEPLOYMENT: ContextVar[bool] = ContextVar(
    "dd4tester_current_live_deployment",
    default=False,
)


def current_source_directory() -> Path:
    """Return the source area directory for the current execution scope."""
    return _CURRENT_SOURCE_DIRECTORY.get() or DEFAULT_SOURCE_DIRECTORY


def current_live_deployment() -> bool:
    """Return whether source loads are serving a live campaign."""
    return _CURRENT_LIVE_DEPLOYMENT.get()


@contextmanager
def source_directory_context(
    directory: Path | str | None,
    *,
    live_deployment: bool | None = None,
) -> Iterator[Path]:
    """Pin one source directory and deployment profile for nested helpers."""
    selected = (
        Path(directory)
        if directory is not None
        else DEFAULT_SOURCE_DIRECTORY
    )
    source_token = _CURRENT_SOURCE_DIRECTORY.set(selected)
    deployment_token = _CURRENT_LIVE_DEPLOYMENT.set(
        current_live_deployment()
        if live_deployment is None
        else live_deployment
    )
    try:
        yield selected
    finally:
        _CURRENT_LIVE_DEPLOYMENT.reset(deployment_token)
        _CURRENT_SOURCE_DIRECTORY.reset(source_token)
