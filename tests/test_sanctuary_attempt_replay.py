import json
from copy import deepcopy

import pytest

from dd4tester.campaign import (
    _CAMPAIGN_POLICY_REVISION,
    _consume_sanctuary_invisible_carrier_revalidation,
    _consume_sanctuary_visibility_revalidation,
    _merge_campaign_research_result,
    _refresh_policy_revision,
    _repair_sanctuary_resource_acquisition_history,
    _research_fatal_failure_active,
    _research_retry_cooldown_active,
    _SANCTUARY_INVISIBLE_CARRIER_REVALIDATION_KEY,
    _sanctuary_invisible_carrier_revalidation_pending,
    _SANCTUARY_VISIBILITY_REVALIDATION_KEY,
    _sanctuary_visibility_revalidation_pending,
    _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY,
)


POLICY = _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
ATTEMPTS = "campaign_sanctuary_resource_attempts"


def state_with_count(count=None, *, boot="boot-1", level=18):
    state = {"world_boot_id": boot, "level": level}
    if count is not None:
        state[ATTEMPTS] = {
            POLICY: {"boot_id": boot, "level": level, "count": count},
        }
    return state


def segment(sequence, *, start_count=None, boot="boot-1", level=18,
            acquired=False, absent=False, died=False):
    start = state_with_count(start_count, boot=boot, level=level)
    end = {"world_boot_id": boot, "level": level}
    if acquired:
        end["verified_combat_pouch_potions"] = {"purple": 1}
    elif absent:
        end["campaign_fastwalk_target_absent"] = True
    elif died:
        end["campaign_died_during_segment"] = True
    else:
        end["campaign_fastwalk_abort_reason"] = (
            "field route preflight found source-registered hazard 'the drunk' in room 3001"
        )
    return {
        "sequence": sequence, "phase": POLICY, "status": "success",
        "start_state_json": json.dumps(start), "end_state_json": json.dumps(end),
    }


def repair(state, segments):
    return _repair_sanctuary_resource_acquisition_history(state, segments)


def count(state):
    return state.get(ATTEMPTS, {}).get(POLICY, {}).get("count", 0)


def legacy_visibility_failure():
    state = state_with_count(28)
    state.update({
        "campaign_policy_revision": 242,
        "character_class": "Mage",
        "subclass": "none",
        "campaign_known_skill_levels": {"invis": 42},
        "campaign_protection_recovery_required": {
            "boot_id": "boot-1", "level": 18, "xp_delta": -3768,
        },
        "campaign_research_results": {
            POLICY: {
                "boot_id": "boot-1", "level": 18,
                "fatal_failure": True, "viable": False,
                "route_hazard": (
                    "field route preflight found source-registered hazard "
                    "'the drunk' in room 3001"
                ),
            },
        },
        "campaign_research_absence_cooldowns": {POLICY: 3},
        "campaign_cleared_research_policies": [POLICY, "another-policy"],
        "campaign_explicit_research_retry_policies": {
            "boot_id": "boot-1", "policy_ids": [POLICY, "another-policy"],
        },
        "campaign_last_policy": POLICY,
        "campaign_fastwalk_abort_reason": (
            "field route preflight found source-registered hazard "
            "'the drunk' in room 3001"
        ),
        "campaign_fastwalk_target_absent": False,
    })
    return state


def completed_visibility_revalidation():
    previous = _refresh_policy_revision(legacy_visibility_failure())
    assert _consume_sanctuary_visibility_revalidation(
        previous, policy_id=POLICY,
    )
    current = deepcopy(previous)
    current.update({
        "campaign_last_policy": POLICY,
        "campaign_fastwalk_target_present_observed": True,
        "campaign_fastwalk_target_absent": False,
        "campaign_fastwalk_where_area_checks": [{
            "area_file": "moria.are",
            "result": "present",
            "room_vnum": "4014",
            "scope": "current_area",
            "source_mobile_vnum": 4055,
            "target": "large hobgoblin",
        }],
        "campaign_fastwalk_where_relocation_attempts": 1,
        "campaign_fastwalk_route_hazards": [],
        "campaign_fastwalk_route_preflight_complete": True,
        "campaign_fastwalk_route_preflight_hazard_observed": False,
        "campaign_fastwalk_route_preflight_inconclusive": False,
        "campaign_fastwalk_route_preflight_locations": ["The Cartography Store"],
        "campaign_fastwalk_route_invisibility_checks": [{
            "destination": "3001",
            "from_room": "3001",
            "reason": "live invisibility blocks source greet visibility",
            "source_mobile_vnum": 3064,
        }],
        "campaign_fastwalk_abort_reason": None,
        "campaign_fastwalk_consider_outcomes": {},
        "campaign_objective_kills": [],
        "campaign_fastwalk_required_object_vnums": [],
        "verified_combat_pouch_potions": {},
        "campaign_died_during_segment": False,
        "room_vnum": "3054",
        "room_flags": ["safe", "healing"],
        "hp": 218,
        "max_hp": 218,
    })
    merged = _merge_campaign_research_result(
        previous,
        current,
        policy=_SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY,
    )
    assert merged[_SANCTUARY_VISIBILITY_REVALIDATION_KEY]["status"] == "failed"
    assert count(merged) == 29
    assert merged["campaign_research_results"][POLICY]["fatal_failure"] is True
    # This fixture is the historical endpoint consumed by revision 244, not
    # a checkpoint written by whichever policy revision is current today.
    merged["campaign_policy_revision"] = 243
    return merged


def test_one_recorded_failure_does_not_become_fatal_on_startup_replay():
    state = state_with_count(1)
    rows = [segment(1)]
    first = repair(state, rows)
    assert count(first) == 1
    assert repair(first, rows) == first
    assert POLICY not in first.get("campaign_research_results", {})


def test_two_real_failures_remain_terminal_and_idempotent():
    rows = [segment(1), segment(2, start_count=1)]
    first = repair(state_with_count(), rows)
    assert count(first) == 2
    assert first["campaign_research_results"][POLICY]["fatal_failure"] is True
    assert repair(first, rows) == first


def test_bounded_history_uses_first_segment_start_for_earlier_attempts():
    rows = [segment(9, start_count=2), segment(10, start_count=3)]
    first = repair(state_with_count(), rows)
    assert count(first) == 4
    assert repair(first, rows) == first


def test_overlapping_history_does_not_add_again_to_saved_floor():
    state = state_with_count(4)
    rows = [segment(9, start_count=2), segment(10, start_count=3)]
    first = repair(state, rows)
    assert count(first) == 4
    assert count(repair(first, rows[1:])) == 4


def test_run_12828_count_stops_growing_without_rewriting_old_evidence():
    state = state_with_count(28)
    state["campaign_protection_recovery_required"] = {"xp_delta": -3768}
    state["campaign_research_results"] = {
        POLICY: {"boot_id": "boot-1", "level": 18, "fatal_failure": True,
                 "viable": False, "route_hazard": "preserved departure failure"},
    }
    original = deepcopy(state)
    rows = [segment(990, start_count=17, absent=True), segment(991, start_count=20)]
    for _ in range(3):
        state = repair(state, rows)
        assert count(state) == 28
    assert state == original


def test_unknown_earlier_history_keeps_existing_counter_and_terminal_gate():
    first = repair(state_with_count(2), [])
    assert count(first) == 2
    assert first["campaign_research_results"][POLICY]["fatal_failure"] is True
    assert repair(first, []) == first


def test_positive_acquisition_still_clears_attempts():
    rows = [segment(1), segment(2, start_count=1, acquired=True)]
    first = repair(state_with_count(2), rows)
    assert count(first) == 0
    assert first["campaign_research_results"][POLICY]["required_object_acquired"] is True
    assert repair(first, rows) == first


def test_failure_after_acquisition_counts_once_from_zero():
    rows = [segment(1, start_count=8, acquired=True), segment(2)]
    first = repair(state_with_count(1), rows)
    assert count(first) == 1
    assert repair(first, rows) == first


def test_other_reboot_does_not_add_current_attempts():
    state = state_with_count(1)
    first = repair(state, [segment(1, boot="old-boot")])
    assert first == state


def test_changed_level_has_its_own_count():
    rows = [segment(1, level=17), segment(2, level=18)]
    first = repair(state_with_count(1, level=17), rows)
    assert first[ATTEMPTS][POLICY] == {"boot_id": "boot-1", "level": 18, "count": 1}
    assert repair(first, rows) == first


def test_absence_and_death_do_not_become_retryable_attempts():
    state = state_with_count(1)
    first = repair(state, [segment(1, absent=True), segment(2, died=True)])
    assert first == state


def test_input_state_and_segments_are_not_mutated():
    state = state_with_count(1)
    rows = [segment(1)]
    original = deepcopy((state, rows))
    repair(state, rows)
    assert (state, rows) == original


def test_revision_243_archives_exact_visibility_failure_for_one_revalidation():
    original = legacy_visibility_failure()
    refreshed = _refresh_policy_revision(deepcopy(original))

    assert refreshed["campaign_policy_revision"] == _CAMPAIGN_POLICY_REVISION
    assert POLICY not in refreshed.get("campaign_research_results", {})
    assert count(refreshed) == 28
    assert refreshed["campaign_protection_recovery_required"]["xp_delta"] == -3768
    assert refreshed["campaign_cleared_research_policies"] == ["another-policy"]
    assert refreshed["campaign_explicit_research_retry_policies"]["policy_ids"] == [
        "another-policy"
    ]
    assert "campaign_last_policy" not in refreshed
    marker = refreshed[_SANCTUARY_VISIBILITY_REVALIDATION_KEY]
    assert marker["status"] == "pending"
    assert marker["superseded_result"] == original["campaign_research_results"][POLICY]
    assert _sanctuary_visibility_revalidation_pending(refreshed)
    assert _refresh_policy_revision(deepcopy(refreshed)) == refreshed


@pytest.mark.parametrize(
    "boundary",
    ["different_hazard", "no_skill", "unauthorized_class", "wrong_boot",
     "wrong_level", "completed", "no_protection"],
)
def test_visibility_revalidation_does_not_widen_other_terminal_failures(boundary):
    state = legacy_visibility_failure()
    result = state["campaign_research_results"][POLICY]
    if boundary == "different_hazard":
        result["route_hazard"] = "required-loot endpoint contained an orc"
    elif boundary == "no_skill":
        state["campaign_known_skill_levels"] = {}
    elif boundary == "unauthorized_class":
        state["character_class"] = "Warrior"
    elif boundary == "wrong_boot":
        result["boot_id"] = "old-boot"
    elif boundary == "wrong_level":
        result["level"] = 17
    elif boundary == "completed":
        result["completed_kill"] = True
    else:
        state.pop("campaign_protection_recovery_required")

    refreshed = _refresh_policy_revision(state)

    assert _SANCTUARY_VISIBILITY_REVALIDATION_KEY not in refreshed
    assert refreshed["campaign_research_results"][POLICY] == result


def test_pending_revalidation_prevents_history_from_recreating_old_terminal_gate():
    refreshed = _refresh_policy_revision(legacy_visibility_failure())
    replayed = repair(refreshed, [segment(990, start_count=17, absent=True),
                                  segment(991, start_count=20)])

    assert count(replayed) == 28
    assert POLICY not in replayed.get("campaign_research_results", {})
    assert _sanctuary_visibility_revalidation_pending(replayed)
    assert repair(replayed, [segment(991, start_count=20)]) == replayed


def test_revalidation_is_consumed_once_and_restores_terminal_checks():
    state = _refresh_policy_revision(legacy_visibility_failure())
    state["campaign_research_results"] = {
        POLICY: {
            "boot_id": "boot-1", "level": 18,
            "fatal_failure": True, "viable": False,
        },
    }
    state["campaign_research_absence_cooldowns"] = {POLICY: 3}

    assert not _research_fatal_failure_active(state, POLICY)
    assert not _research_retry_cooldown_active(state, POLICY)
    assert _consume_sanctuary_visibility_revalidation(state, policy_id=POLICY)
    assert not _sanctuary_visibility_revalidation_pending(state)
    assert _research_fatal_failure_active(state, POLICY)
    assert _research_retry_cooldown_active(state, POLICY)
    assert not _consume_sanctuary_visibility_revalidation(state, policy_id=POLICY)


def test_pending_revalidation_is_bound_to_level_and_reboot():
    state = _refresh_policy_revision(legacy_visibility_failure())
    assert _sanctuary_visibility_revalidation_pending(state)
    state["level"] = 19
    assert not _sanctuary_visibility_revalidation_pending(state)
    state["level"] = 18
    state["world_boot_id"] = "boot-2"
    assert not _sanctuary_visibility_revalidation_pending(state)


@pytest.mark.parametrize("acquired", [False, True])
def test_fresh_segment_records_revalidation_outcome(acquired):
    previous = _refresh_policy_revision(legacy_visibility_failure())
    assert _consume_sanctuary_visibility_revalidation(previous, policy_id=POLICY)
    current = deepcopy(previous)
    if acquired:
        current["verified_combat_pouch_potions"] = {"purple": 1}
        current["campaign_fastwalk_required_object_vnums"] = [4050]
    else:
        current["campaign_fastwalk_target_absent"] = True
        current["campaign_fastwalk_target_present_observed"] = False
        current["campaign_fastwalk_consider_outcomes"] = {}
        current["campaign_objective_kills"] = []

    merged = _merge_campaign_research_result(
        previous, current, policy=_SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY,
    )

    marker = merged[_SANCTUARY_VISIBILITY_REVALIDATION_KEY]
    assert marker["status"] == ("succeeded" if acquired else "failed")
    result = merged["campaign_research_results"][POLICY]
    assert bool(result.get("required_object_acquired")) is acquired
    assert result.get("fatal_failure") is not True


def test_revision_246_opens_only_the_source_located_carrier_graph_after_clean_route_preflight():
    original = completed_visibility_revalidation()
    refreshed = _refresh_policy_revision(deepcopy(original))

    assert refreshed["campaign_policy_revision"] == _CAMPAIGN_POLICY_REVISION
    assert POLICY not in refreshed.get("campaign_research_results", {})
    assert count(refreshed) == 29
    assert refreshed["campaign_protection_recovery_required"]["xp_delta"] == -3768
    assert (
        refreshed[_SANCTUARY_VISIBILITY_REVALIDATION_KEY]
        == original[_SANCTUARY_VISIBILITY_REVALIDATION_KEY]
    )
    marker = refreshed[_SANCTUARY_INVISIBLE_CARRIER_REVALIDATION_KEY]
    assert marker["status"] == "pending"
    assert marker["source_location_evidence"] == {
        "source_mobile_vnum": 4055,
        "area_file": "moria.are",
        "scope": "current_area",
        "where_relocation_attempts": 1,
        "city_route_preflight_locations": ["The Cartography Store"],
    }
    assert marker["superseded_result"] == original[
        "campaign_research_results"
    ][POLICY]
    assert _sanctuary_invisible_carrier_revalidation_pending(refreshed)
    assert _refresh_policy_revision(deepcopy(refreshed)) == refreshed


def test_invisibility_evidence_without_clean_route_preflight_does_not_reopen_carrier():
    original = completed_visibility_revalidation()
    for key in (
        "campaign_fastwalk_route_preflight_complete",
        "campaign_fastwalk_route_preflight_hazard_observed",
        "campaign_fastwalk_route_preflight_inconclusive",
        "campaign_fastwalk_route_preflight_locations",
    ):
        original.pop(key, None)

    refreshed = _refresh_policy_revision(deepcopy(original))

    assert _SANCTUARY_INVISIBLE_CARRIER_REVALIDATION_KEY not in refreshed
    assert POLICY in refreshed.get("campaign_research_results", {})


@pytest.mark.parametrize(
    "boundary",
    [
        "no_target",
        "target_absent",
        "where_missing",
        "wrong_vnum",
        "route_hazard",
        "abort",
        "death",
        "xp_loss",
        "object_acquired",
        "no_invis",
        "wrong_boot",
        "wrong_level",
        "prior_pending",
        "different_result",
        "no_protection",
        "unsafe_endpoint",
    ],
)
def test_invisible_carrier_revalidation_does_not_widen_other_failures(boundary):
    state = completed_visibility_revalidation()
    if boundary == "no_target":
        state["campaign_fastwalk_target_present_observed"] = False
    elif boundary == "target_absent":
        state["campaign_fastwalk_target_absent"] = True
    elif boundary == "where_missing":
        state["campaign_fastwalk_where_area_checks"] = []
    elif boundary == "wrong_vnum":
        state["campaign_fastwalk_where_area_checks"][0][
            "source_mobile_vnum"
        ] = 4005
    elif boundary == "route_hazard":
        state["campaign_fastwalk_route_hazards"] = ["an orc"]
    elif boundary == "abort":
        state["campaign_fastwalk_abort_reason"] = "field route aborted"
    elif boundary == "death":
        state["campaign_died_during_segment"] = True
    elif boundary == "xp_loss":
        state["campaign_research_results"][POLICY][
            "xp_loss_observed"
        ] = True
    elif boundary == "object_acquired":
        state["verified_combat_pouch_potions"] = {"purple": 1}
    elif boundary == "no_invis":
        state["campaign_known_skill_levels"] = {}
    elif boundary == "wrong_boot":
        state["world_boot_id"] = "boot-2"
    elif boundary == "wrong_level":
        state["level"] = 19
    elif boundary == "prior_pending":
        state[_SANCTUARY_VISIBILITY_REVALIDATION_KEY]["status"] = "pending"
    elif boundary == "different_result":
        state["campaign_research_results"][POLICY]["route_hazard"] = (
            "a different terminal failure"
        )
    elif boundary == "no_protection":
        state.pop("campaign_protection_recovery_required")
    else:
        state["room_vnum"] = "3001"

    refreshed = _refresh_policy_revision(state)

    assert _SANCTUARY_INVISIBLE_CARRIER_REVALIDATION_KEY not in refreshed


def test_pending_invisible_carrier_revalidation_survives_history_repair():
    refreshed = _refresh_policy_revision(completed_visibility_revalidation())
    replayed = repair(
        refreshed,
        [segment(990, start_count=17, absent=True), segment(991, start_count=20)],
    )

    assert count(replayed) == 29
    assert POLICY not in replayed.get("campaign_research_results", {})
    assert _sanctuary_invisible_carrier_revalidation_pending(replayed)
    assert repair(replayed, [segment(991, start_count=20)]) == replayed


def test_invisible_carrier_revalidation_is_consumed_once_before_connection():
    state = _refresh_policy_revision(completed_visibility_revalidation())
    state["campaign_research_results"] = {
        POLICY: deepcopy(
            state[_SANCTUARY_INVISIBLE_CARRIER_REVALIDATION_KEY][
                "superseded_result"
            ]
        ),
    }
    state["campaign_research_absence_cooldowns"] = {POLICY: 3}

    assert not _research_fatal_failure_active(state, POLICY)
    assert not _research_retry_cooldown_active(state, POLICY)
    assert _consume_sanctuary_invisible_carrier_revalidation(
        state, policy_id=POLICY,
    )
    assert not _sanctuary_invisible_carrier_revalidation_pending(state)
    assert _research_fatal_failure_active(state, POLICY)
    assert _research_retry_cooldown_active(state, POLICY)
    assert not _consume_sanctuary_invisible_carrier_revalidation(
        state, policy_id=POLICY,
    )


@pytest.mark.parametrize("acquired", [False, True])
def test_expanded_carrier_segment_records_its_own_outcome(acquired):
    previous = _refresh_policy_revision(completed_visibility_revalidation())
    assert _consume_sanctuary_invisible_carrier_revalidation(
        previous, policy_id=POLICY,
    )
    current = deepcopy(previous)
    current["campaign_fastwalk_target_present_observed"] = False
    current["campaign_fastwalk_target_absent"] = not acquired
    current["campaign_fastwalk_consider_outcomes"] = {}
    current["campaign_objective_kills"] = []
    if acquired:
        current["verified_combat_pouch_potions"] = {"purple": 1}
        current["campaign_fastwalk_required_object_vnums"] = [4050]

    merged = _merge_campaign_research_result(
        previous,
        current,
        policy=_SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY,
    )

    marker = merged[_SANCTUARY_INVISIBLE_CARRIER_REVALIDATION_KEY]
    assert marker["status"] == ("succeeded" if acquired else "failed")
    result = merged["campaign_research_results"][POLICY]
    assert bool(result.get("required_object_acquired")) is acquired
    assert result.get("fatal_failure") is not True
