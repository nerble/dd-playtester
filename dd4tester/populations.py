"""Source proofs for bounded, non-aggressive same-prototype populations."""

import json
from collections.abc import Mapping
from typing import Any

from .equipment import normalize_item_name
from .hunt_candidates import (
    ITEM_PILL,
    ITEM_POTION,
    ITEM_SCROLL,
    ITEM_STAFF,
    ITEM_WAND,
    ITEM_WEAPON,
    WEAR_DUAL,
    WEAR_WIELD,
    HuntCandidate,
    WorldSource,
)


POPULATION_SEARCH_REVALIDATIONS_KEY = "campaign_population_search_revalidations"


def population_search_revalidation_pending(
    state: Mapping[str, Any], candidate: HuntCandidate, policy_id: str,
) -> bool:
    records = state.get(POPULATION_SEARCH_REVALIDATIONS_KEY)
    receipt = records.get(policy_id) if isinstance(records, Mapping) else None
    return bool(
        isinstance(receipt, Mapping) and receipt.get("revision") == 1
        and receipt.get("status") == "pending"
        and receipt.get("policy_id") == policy_id
        and receipt.get("level") == state.get("level")
        and receipt.get("boot_id") == state.get("world_boot_id")
        and receipt.get("source_revision") == state.get("campaign_source_revision")
        and receipt.get("xp") == state.get("xp")
        and receipt.get("xp_loss_total") == state.get("campaign_xp_loss_total")
        and receipt.get("mobile_vnum") == candidate.mobile_vnum
        and receipt.get("reset_room_vnum") == candidate.room_vnum
        and tuple(receipt.get("route") or ()) == candidate.route
        and receipt.get("remaining_rooms")
    )


def incomplete_population_search_evidence(
    state: Mapping[str, Any], segment: Mapping[str, Any], summary: Mapping[str, Any],
    candidate: HuntCandidate, world: WorldSource, *, policy_id: str,
    location_routes: Mapping[str, tuple[str, ...]], maximum_relocations: int,
) -> dict[str, Any] | None:
    """Bind one legacy premature return to its still-registered unchecked rooms."""
    records = state.get(POPULATION_SEARCH_REVALIDATIONS_KEY)
    if isinstance(records, Mapping) and policy_id in records:
        return None
    if not plain_bounded_population(candidate, world) or candidate.sentinel:
        return None
    run, outcomes, progress = (summary.get(key) for key in ("run", "outcomes", "progress"))
    if not all(isinstance(value, Mapping) for value in (run, outcomes, progress)):
        return None
    if (
        segment.get("phase") != policy_id or segment.get("status") != "success"
        or type(segment.get("run_id")) is not int or run.get("id") != segment["run_id"]
        or not segment.get("finished_at") or segment.get("error")
        or type(segment.get("command_count")) is not int or segment["command_count"] <= 0
        or outcomes != {"execution": "success", "objective": "not_achieved", "safety": "safe"}
        or type(progress.get("combat_starts")) is not int or progress["combat_starts"] != 0
        or not (progress.get("confirmed_kills") == [] or (
            type(progress.get("confirmed_kills")) is int and progress["confirmed_kills"] == 0
        ))
        or type(state.get("level")) is not int or state["level"] < 1
        or type(state.get("xp")) is not int or state["xp"] < 0
        or type(state.get("campaign_xp_loss_total")) is not int or state["campaign_xp_loss_total"] < 0
        or type(maximum_relocations) is not int or not 1 <= maximum_relocations <= 8
    ):
        return None
    try:
        start, end = (json.loads(segment.get(key) or "{}")
                      for key in ("start_state_json", "end_state_json"))
    except (TypeError, ValueError):
        return None
    if not isinstance(start, Mapping) or not isinstance(end, Mapping):
        return None
    for key in ("level", "world_boot_id", "campaign_source_revision", "xp", "campaign_xp_loss_total"):
        if state.get(key) is None or not state[key] == start.get(key) == end.get(key):
            return None
    for snapshot in (state, start, end):
        if (
            str(snapshot.get("room_vnum")) != "3054" or snapshot.get("dead") is not False
            or snapshot.get("in_combat") is not False or snapshot.get("enemies") not in (None, [])
            or type(snapshot.get("hp")) is not int or type(snapshot.get("max_hp")) is not int
            or snapshot["max_hp"] <= 0 or snapshot["hp"] < snapshot["max_hp"] * .95
        ):
            return None
    recorded = start.get("campaign_source_ranked_hunt_candidate")
    sightings = end.get("campaign_fastwalk_source_below_band_sightings")
    decisions = end.get("campaign_fastwalk_where_decisions")
    attempts = end.get("campaign_fastwalk_where_relocation_attempts")
    if (
        not isinstance(recorded, Mapping) or recorded.get("policy_id") != policy_id
        or recorded.get("mobile_vnum") != candidate.mobile_vnum
        or recorded.get("room_vnum") != candidate.room_vnum
        or recorded.get("source_revision") != state["campaign_source_revision"]
        or tuple(recorded.get("route") or ()) != candidate.route
        or not isinstance(sightings, list) or len(sightings) != 1
        or not isinstance(sightings[0], Mapping) or sightings[0].get("policy_id") != policy_id
        or normalize_item_name(str(sightings[0].get("target") or "")) not in {
            normalize_item_name(candidate.target_identity or ""), normalize_item_name(candidate.target),
        }
        or not isinstance(decisions, list) or not decisions or len(decisions) > 16
        or any(not isinstance(d, Mapping) or d.get("source_mobile_vnum") != candidate.mobile_vnum
               for d in decisions)
        or type(attempts) is not int or not 0 <= attempts < maximum_relocations
        or any(end.get(key) for key in (
            "campaign_fastwalk_abort_reason", "campaign_fastwalk_crowded",
            "campaign_fastwalk_target_vnum_mismatch", "campaign_fastwalk_unattackable_target",
            "campaign_fastwalk_route_hazards", "campaign_objective_kills", "campaign_completed_kills",
        ))
    ):
        return None
    checked = {str(d.get("room_vnum")) for d in decisions}
    checked.add(str(sightings[0].get("room_vnum")))
    latest = decisions[-1]
    mapped = latest.get("mapped_rooms")
    locations = latest.get("locations")
    if (
        not isinstance(mapped, Mapping) or not isinstance(locations, (list, tuple)) or not locations
        or any(not isinstance(label, str) or not isinstance(mapped.get(label), (list, tuple))
               for label in locations)
        or any(not isinstance(decision.get("planned_endpoints", ()), (list, tuple)) for decision in decisions)
    ):
        return None
    reported = {str(room) for label in locations
                for room in mapped.get(label, ()) if isinstance(room, (str, int))}
    registered = {str(room) for rooms in location_routes.values() for room in rooms}
    planned = {str(room) for decision in decisions for room in decision.get("planned_endpoints", ())}
    remaining = sorted((reported & registered & planned) - checked)
    if not remaining:
        return None
    return {
        "revision": 1, "status": "pending", "policy_id": policy_id,
        "level": state["level"], "boot_id": state["world_boot_id"],
        "source_revision": state["campaign_source_revision"], "xp": state["xp"],
        "xp_loss_total": state["campaign_xp_loss_total"],
        "mobile_vnum": candidate.mobile_vnum, "reset_room_vnum": candidate.room_vnum,
        "route": list(candidate.route), "run_id": segment["run_id"], "segment_id": segment["id"],
        "checked_rooms": sorted(checked), "remaining_rooms": remaining,
        "below_band_sightings": sightings, "locator_evidence": decisions,
        "prior_relocations": attempts, "maximum_relocations": maximum_relocations,
        "reason": "one search repair after a weak individual prematurely ended a bounded population visit",
    }


def plain_bounded_mobile_population(mobile_vnum: int, world: WorldSource | None) -> bool:
    """Audit every reset of a small passive population, not its live occupants."""
    if world is None:
        return False
    mobile = world.mobiles.get(mobile_vnum)
    if (
        mobile is None
        or mobile.aggressive
        or mobile.fear_aura
        or mobile.confused
        or mobile.non_corporeal
        or mobile.programs
        or not (mobile.sentinel or mobile.stay_area)
        or world.mobile_specials.get(mobile.vnum)
    ):
        return False
    resets = [reset for reset in world.mob_resets if reset.mobile_vnum == mobile.vnum]
    if (
        not 2 <= len(resets) <= 4
        or len({reset.room_vnum for reset in resets}) != len(resets)
        or type(resets[0].maximum_count) is not int
        or not 2 <= resets[0].maximum_count <= 4
        or any(type(reset.maximum_count) is not int or reset.maximum_count != resets[0].maximum_count
               for reset in resets)
    ):
        return False
    for reset in resets:
        room = world.rooms.get(reset.room_vnum)
        if room is None or room.area_file != mobile.area_file or room.random_exits:
            return False
        for slot, object_vnum in reset.equipment:
            if object_vnum not in world.objects or slot in {WEAR_WIELD, WEAR_DUAL}:
                return False
        for object_vnum in set(reset.object_vnums) | {
            object_vnum for _slot, object_vnum in reset.equipment
        }:
            item = world.objects.get(object_vnum)
            if item is None or item.item_type in {
                ITEM_SCROLL, ITEM_WAND, ITEM_STAFF, ITEM_WEAPON, ITEM_POTION, ITEM_PILL,
            }:
                return False
    return True


def plain_bounded_population(candidate: HuntCandidate, world: WorldSource | None) -> bool:
    """Permit a live isolation check, never infer that a room is uncrowded."""
    if not plain_bounded_mobile_population(candidate.mobile_vnum, world):
        return False
    mobile = world.mobiles[candidate.mobile_vnum]
    return bool(
        not candidate.specials and not candidate.equipped_weapons
        and not candidate.is_coin_stash and candidate.status == "reject"
        and candidate.autonomy_rejections == ("target reset capacity exceeds one",)
        and type(candidate.source_spawn_limit) is int
        and 2 <= candidate.source_spawn_limit <= 4
        and type(candidate.room_spawn_count) is int and candidate.room_spawn_count == 1
        and candidate.level == mobile.level and candidate.area_file == mobile.area_file
        and any(reset.room_vnum == candidate.room_vnum for reset in world.mob_resets
                if reset.mobile_vnum == mobile.vnum)
        and all(reset.maximum_count == candidate.source_spawn_limit for reset in world.mob_resets
                if reset.mobile_vnum == mobile.vnum)
    )
