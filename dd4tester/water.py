"""DD4's underwater survival gate is independent of flight."""

from __future__ import annotations

import json
from typing import Any, Collection, Mapping

from .hunt_candidates import WorldSource


def source_route_requires_water_breathing(world: WorldSource, rooms: Collection[int]) -> bool:
    return any(vnum not in world.rooms or world.rooms[vnum].sector_type in {8, 12}
               for vnum in rooms)


def can_breathe_underwater(state: Mapping[str, Any]) -> bool:
    """Mirror update.c's explicit exemptions; flight is not one of them."""
    if (str(state.get("race") or "").casefold() in {"sahuagin", "grung"}
            or str(state.get("subclass") or "").casefold() == "vampire"
            or str(state.get("form") or "").casefold() in {"snake", "hydra", "demon"}):
        return True

    def active(value: Any) -> bool:
        if isinstance(value, str):
            try:
                return active(json.loads(value))
            except (ValueError, TypeError):
                return False
        if isinstance(value, Mapping):
            if str(value.get("name") or "").casefold() in {
                    "breathe water", "mist walk", "astral sidestep"}:
                try:
                    return int(value.get("duration", 0)) > 0
                except (TypeError, ValueError):
                    return False
            return any(active(item) for item in value.values())
        return isinstance(value, (list, tuple)) and any(active(item) for item in value)

    return active(state.get("affects"))
