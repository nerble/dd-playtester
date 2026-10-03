"""Small, evidence-preserving upgrades for historical run contexts."""

from __future__ import annotations

import re
from typing import Any

_SOURCE_FOOD_ROUTE = re.compile(
    r"^source food reserve (?P<item>[a-z0-9][a-z0-9 -]*?) \d+$",
    re.IGNORECASE,
)


def migrate_legacy_run_context(value: Any) -> dict[str, Any]:
    """Remove the old unsafe item guess made from a food-route name."""
    if not isinstance(value, dict):
        return {}
    objective = value.get("objective")
    if not isinstance(objective, dict):
        return value
    if objective.get("required_items_source") != "legacy_source_food_route":
        return value
    route = objective.get("fastwalk_route")
    match = (
        _SOURCE_FOOD_ROUTE.fullmatch(route.strip())
        if isinstance(route, str)
        else None
    )
    if match is None:
        return value
    migrated = dict(value)
    migrated_objective = dict(objective)
    migrated_objective.pop("required_items", None)
    migrated_objective.pop("required_items_source", None)
    migrated["objective"] = migrated_objective
    return migrated
