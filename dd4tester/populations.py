"""Source proofs for bounded, non-aggressive same-prototype populations."""

import json
import re
from collections.abc import Mapping
from typing import Any

from .equipment import normalize_item_name
from .hunt_candidates import (
    ACT_IS_NPC,
    ACT_SENTINEL,
    ACT_STAY_AREA,
    ITEM_FOOD,
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
POPULATION_LOCATOR_MISMATCHES_KEY = "campaign_population_locator_mismatches"
POPULATION_LOCATOR_DETECT_INVIS_VERIFIED_KEY = (
    "campaign_population_locator_detect_invisibility_verified"
)
POPULATION_LOCATOR_ABORT_PREFIX = (
    "field locator did not confirm the exact source population "
)
_SOURCE_HUNT_ID = re.compile(
    r"source-ranked-hunt-[a-z0-9-]+-(?P<mobile>[1-9]\d*)-(?P<room>[1-9]\d*)-(?P<level>[1-9]\d*)\Z"
)

# These source affects are passive perception flags.  They do not add an
# attack, protection, movement, or crowd hazard to an otherwise plain reset.
# Keep this list deliberately narrow: any unreviewed affect remains a reason
# to reject sequential duplicate selection.
# Detect-evil, detect-hidden, and infrared are passive perception flags. They
# do not add an attack, protection, movement, or crowd hazard to a plain reset.
_SOURCE_SEQUENTIAL_PASSIVE_AFFECTS = (1 << 2) | (1 << 5) | (1 << 9)

# Population checks are called repeatedly while the source-ranked selector
# rotates through candidates.  The source world is immutable for a campaign
# plan, so build the reset index once instead of scanning every reset for each
# candidate.
_WORLD_RESET_INDEX_CACHE: dict[
    int, tuple[WorldSource, dict[int, tuple[Any, ...]]]
] = {}


def _resets_by_mobile_for_world(
    world: WorldSource,
) -> dict[int, tuple[Any, ...]]:
    cache_key = id(world)
    cached = _WORLD_RESET_INDEX_CACHE.get(cache_key)
    if cached is not None and cached[0] is world:
        return cached[1]
    indexed: dict[int, list[Any]] = {}
    for reset in world.mob_resets:
        indexed.setdefault(reset.mobile_vnum, []).append(reset)
    result = {mobile_vnum: tuple(resets) for mobile_vnum, resets in indexed.items()}
    _WORLD_RESET_INDEX_CACHE[cache_key] = (world, result)
    return result


def _source_sequential_reset_objects_are_harmless(
    world: WorldSource,
    object_vnums: tuple[int, ...],
) -> bool:
    """Allow only inert food or simple healing items on a plain reset."""
    for object_vnum in object_vnums:
        item = world.objects.get(object_vnum)
        if item is None or item.item_type not in {ITEM_FOOD, ITEM_PILL}:
            return False
        if item.affects:
            return False
        if item.item_type == ITEM_PILL:
            effect = (
                str(item.value_strings[1]).casefold()
                if len(item.value_strings) > 1
                else ""
            )
            if effect not in {
                "heal",
                "cure light",
                "cure serious",
                "cure critical",
            }:
                return False
    return True


def source_sequential_duplicate_reset_limit(
    world: WorldSource | None,
    *,
    mobile_vnum: int,
    room_vnum: int | str,
) -> int | None:
    """Prove a small plain stationary or stay-area reset safe to select sequentially.

    This is not multi-target combat permission or the capacity-only population
    research path. It applies only to one unprogrammed, unspecial, unequipped
    sentinel or stay-area reset with two to four instances in one room. A
    stay-area mobile is included only when its source reset is otherwise
    plain; the live locator still has to find the exact copy before each
    bounded action. The caller still has to prove every live selector and
    keep the sequential kill bound.
    """
    try:
        room = int(room_vnum)
    except (TypeError, ValueError):
        return None
    mobile = world.mobiles.get(mobile_vnum) if world is not None else None
    resets = [
        reset for reset in world.mob_resets
        if reset.mobile_vnum == mobile_vnum
    ] if world is not None else []
    room_resets = [reset for reset in resets if reset.room_vnum == room]
    if (
        mobile is None
        or mobile.act_flags not in {
            ACT_SENTINEL,
            ACT_IS_NPC | ACT_SENTINEL,
            ACT_SENTINEL | ACT_STAY_AREA,
            ACT_IS_NPC | ACT_SENTINEL | ACT_STAY_AREA,
            ACT_STAY_AREA,
            ACT_IS_NPC | ACT_STAY_AREA,
        }
        or mobile.affected_flags & ~_SOURCE_SEQUENTIAL_PASSIVE_AFFECTS
        or mobile.programs
        or world.mobile_specials.get(mobile_vnum)
        or mobile.rank.casefold() not in {"common", "none"}
        or not mobile.short_description.strip()
        or not room_resets
        or len(room_resets) != 1
        or type(room_resets[0].maximum_count) is not int
        or not 2 <= room_resets[0].maximum_count <= 4
        or any(
            type(reset.maximum_count) is not int
            or reset.maximum_count != room_resets[0].maximum_count
            or reset.equipment
            or not _source_sequential_reset_objects_are_harmless(
                world,
                reset.object_vnums,
            )
            for reset in resets
        )
    ):
        return None
    return room_resets[0].maximum_count


def population_locator_mismatch_receipt(state: Mapping[str, Any]) -> dict[str, Any] | None:
    """Keep a positive, source-bound locator mismatch distinct from absence."""
    if not str(state.get("campaign_fastwalk_abort_reason") or "").startswith(
        POPULATION_LOCATOR_ABORT_PREFIX,
    ):
        return None
    run_id = state.get("campaign_population_locator_run_id")
    level, boot = state.get("level"), state.get("world_boot_id")
    revision = state.get("campaign_source_revision")
    candidate = state.get("campaign_source_ranked_hunt_candidate")
    requires_detection = (
        isinstance(candidate, Mapping)
        and candidate.get("requires_detect_invisibility") is True
    )
    detection_verified = (
        state.get(POPULATION_LOCATOR_DETECT_INVIS_VERIFIED_KEY) is True
    )
    policy_id = str(state.get("campaign_last_policy") or "")
    policy_identity = _SOURCE_HUNT_ID.fullmatch(policy_id)
    audits = state.get("campaign_fastwalk_where_decisions")
    if (
        type(run_id) is not int or run_id <= 0
        or type(level) is not int or not 1 <= level <= 100
        or not isinstance(boot, str) or not boot
        or not isinstance(revision, str) or not revision
        or policy_identity is None
        or int(policy_identity["level"]) != level
        or not isinstance(audits, list)
        or requires_detection and not detection_verified
    ):
        return None
    for audit in reversed(audits[-8:]):
        if not isinstance(audit, Mapping):
            continue
        mobile = audit.get("source_mobile_vnum")
        counts = audit.get("location_counts")
        locations = audit.get("locations")
        if (
            type(mobile) is not int or mobile <= 0
            or int(policy_identity["mobile"]) != mobile
            or isinstance(candidate, Mapping) and candidate.get("mobile_vnum") != mobile
            or not isinstance(counts, Mapping) or not 1 <= len(counts) <= 8
            or not isinstance(locations, list)
            or not all(isinstance(label, str) for label in locations)
            or set(locations) != set(counts)
            or any(
                not isinstance(label, str) or not label or len(label) > 160
                or type(count) is not int or not 1 <= count <= 4
                for label, count in counts.items()
            )
            or sum(counts.values()) > 4
        ):
            continue
        receipt = {
            "run_id": run_id, "mobile_vnum": mobile, "level": level,
            "boot_id": boot, "source_revision": revision,
            "location_counts": dict(counts), "reason": "population_mismatch",
            "policy_id": policy_id,
        }
        if requires_detection:
            receipt["detect_invisibility_verified"] = True
        return receipt
    return None


def merge_population_locator_mismatches(
    previous: Mapping[str, Any], current: Mapping[str, Any],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for state in (previous, current):
        saved = state.get(POPULATION_LOCATOR_MISMATCHES_KEY)
        additions = list(saved[-8:]) if isinstance(saved, list) else []
        receipt = population_locator_mismatch_receipt(state)
        if receipt is not None:
            additions.append(receipt)
        for item in additions:
            if (
                not isinstance(item, Mapping)
                or item.get("reason") != "population_mismatch"
                or type(item.get("run_id")) is not int or item["run_id"] <= 0
                or type(item.get("mobile_vnum")) is not int or item["mobile_vnum"] <= 0
                or type(item.get("level")) is not int or not 1 <= item["level"] <= 100
                or not isinstance(item.get("boot_id"), str) or not item["boot_id"]
                or not isinstance(item.get("source_revision"), str) or not item["source_revision"]
                or not isinstance(item.get("location_counts"), Mapping)
                or not 1 <= len(item["location_counts"]) <= 8
                or (
                    "detect_invisibility_verified" in item
                    and type(item["detect_invisibility_verified"]) is not bool
                )
                or any(
                    not isinstance(label, str) or not label
                    or type(count) is not int or not 1 <= count <= 4
                    for label, count in item["location_counts"].items()
                )
                or sum(item["location_counts"].values()) > 4
            ):
                continue
            identity = tuple(item.get(k) for k in ("mobile_vnum", "level", "boot_id", "source_revision"))
            records = [
                old for old in records
                if tuple(old.get(k) for k in ("mobile_vnum", "level", "boot_id", "source_revision")) != identity
            ]
            records.append(dict(item))
    return records[-8:]


def population_locator_mismatch_blocks(
    state: Mapping[str, Any], candidate: HuntCandidate, *, character_level: int,
) -> bool:
    return any(
        record.get("mobile_vnum") == candidate.mobile_vnum
        and record.get("level") == character_level
        and record.get("boot_id") == state.get("world_boot_id")
        and record.get("source_revision") == state.get("campaign_source_revision")
        and type(record.get("run_id")) is int
        and record["run_id"] > 0
        and record.get("reason") == "population_mismatch"
        and (
            not getattr(candidate, "requires_detect_invisibility", False)
            or record.get("detect_invisibility_verified") is True
        )
        for record in merge_population_locator_mismatches({}, state)
    )


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


def plain_bounded_mobile_population(
    mobile_vnum: int,
    world: WorldSource | None,
    *,
    resets_by_mobile: Mapping[int, tuple[Any, ...]] | None = None,
) -> bool:
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
    reset_index = (
        resets_by_mobile
        if resets_by_mobile is not None
        else _resets_by_mobile_for_world(world)
    )
    resets = list(reset_index.get(mobile.vnum, ()))
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


def plain_bounded_population(
    candidate: HuntCandidate,
    world: WorldSource | None,
    *,
    resets_by_mobile: Mapping[int, tuple[Any, ...]] | None = None,
) -> bool:
    """Permit a live isolation check, never infer that a room is uncrowded."""
    if not plain_bounded_mobile_population(
        candidate.mobile_vnum,
        world,
        resets_by_mobile=resets_by_mobile,
    ):
        return False
    mobile = world.mobiles[candidate.mobile_vnum]
    # Source ranking represents a passive multi-room population as a normal
    # caution candidate: the copies are in distinct rooms, so no room-local
    # crowd rejection is emitted. Keep that source shape eligible for the
    # capacity-research contract alongside the older same-room rejection
    # shape. Live isolation and consider checks still decide the encounter.
    source_ranked_plain_population_shape = bool(
        candidate.status in {"caution", "promising"}
        and not candidate.autonomy_rejections
    )
    legacy_capacity_research_shape = bool(
        candidate.status == "reject"
        and candidate.autonomy_rejections
        == ("target reset capacity exceeds one",)
    )
    reset_index = (
        resets_by_mobile
        if resets_by_mobile is not None
        else _resets_by_mobile_for_world(world)
    )
    target_resets = tuple(
        reset for reset in reset_index.get(mobile.vnum, ())
        if reset.mobile_vnum == mobile.vnum
    )
    return bool(
        not candidate.specials and not candidate.equipped_weapons
        and not candidate.is_coin_stash
        and (
            source_ranked_plain_population_shape
            or legacy_capacity_research_shape
        )
        and type(candidate.source_spawn_limit) is int
        and 2 <= candidate.source_spawn_limit <= 4
        and type(candidate.room_spawn_count) is int and candidate.room_spawn_count == 1
        and candidate.level == mobile.level and candidate.area_file == mobile.area_file
        and any(reset.room_vnum == candidate.room_vnum for reset in target_resets)
        and all(
            reset.maximum_count == candidate.source_spawn_limit
            for reset in target_resets
        )
    )
