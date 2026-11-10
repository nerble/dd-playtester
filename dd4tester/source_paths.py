"""Resolve and pin the DD4 source snapshot used by a campaign.

The default remains repository-relative for existing scenario and campaign
files.  A running campaign can install an explicit source directory in a
context-local scope so every source-backed planner sees the same snapshot.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


DEFAULT_SOURCE_DIRECTORY = Path("runs/dd4-source/server/area")

# The live server is currently deployed before the upstream undead and
# archetype/species rollout. Keep the latest checkout available for source
# research, but do not let these newer or revised template definitions
# authorize a live hunt until a live probe proves that deployment has caught up.
LIVE_UNDEPLOYED_TEMPLATE_NAMES = frozenset(
    {
        "animated_soft_toy",
        "animated_toy_soldier",
        "banshee",
        "death_knight",
        "dracolich",
        "dwarf",
        "dwarf_untrained",
        "ghast",
        "ghoul",
        "goblin",
        "half_orc",
        "hobgoblin",
        "lich",
        "mummy",
        "ogre_mage",
        "skeleton",
        "troll",
        "vampire",
        "vampire_bat_form",
        "wyvern",
        "zombie",
    }
)


@dataclass(frozen=True)
class LiveMobileSourceOverride:
    """Legacy prototype facts preserved across a known source conversion."""

    source_revision: str
    template_name: str
    keywords: str
    short_description: str
    level: int
    alignment: int
    act_flags: int
    affected_flags: int


# Dwarven Home's October 26 conversion only replaced these prototypes' direct
# flags with the new dwarf template. The live MUD still uses the old records.
LIVE_MOBILE_SOURCE_OVERRIDES = {
    ("dwarven_home.are", 20512): LiveMobileSourceOverride(
        source_revision="6b1ffdab647b3329a056a9d122c2fda59de6b9ec",
        template_name="dwarf",
        keywords="dwarf chess player",
        short_description="the dwarf",
        level=40,
        alignment=-750,
        act_flags=66,
        affected_flags=8712,
    ),
    ("dwarven_home.are", 20515): LiveMobileSourceOverride(
        source_revision="6b1ffdab647b3329a056a9d122c2fda59de6b9ec",
        template_name="dwarf",
        keywords="dwarf gambler",
        short_description="the dwarven gambler",
        level=49,
        alignment=-750,
        act_flags=66,
        affected_flags=8712,
    ),
}

_CURRENT_SOURCE_DIRECTORY: ContextVar[Path | None] = ContextVar(
    "dd4tester_current_source_directory",
    default=None,
)
_CURRENT_LIVE_DEPLOYMENT: ContextVar[bool] = ContextVar(
    "dd4tester_current_live_deployment",
    default=False,
)


def resolve_source_area_directory(
    directory: Path | str | None = None,
) -> Path:
    """Return the area directory paired with a DD4 source checkout.

    Callers commonly have a checkout root, ``server``, ``server/src``,
    ``const.c``, or the area directory itself. Treating those forms as one
    source identity prevents a valid source audit from silently parsing zero
    area files when the caller points at the C source directory.
    """
    if directory is None:
        return DEFAULT_SOURCE_DIRECTORY

    supplied = Path(directory)
    if supplied.is_file() and supplied.name.casefold() == "const.c":
        supplied = supplied.parent
    if supplied.name.casefold() == "area":
        return supplied
    if supplied.name.casefold() == "src":
        paired_area = supplied.parent / "area"
        return paired_area if paired_area.is_dir() else supplied
    if (supplied / "area").is_dir() and (supplied / "src").is_dir():
        return supplied / "area"
    paired_area = supplied / "server" / "area"
    if paired_area.is_dir():
        return paired_area
    return supplied


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
    selected = resolve_source_area_directory(directory)
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
