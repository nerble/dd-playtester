import json
from dataclasses import replace
from types import SimpleNamespace

from dd4tester.campaign import (
    _SOURCE_RANKED_CONSIDER_RESET_WAIT_KEY,
    _SOURCE_RANKED_CONSIDER_FUZZ_REVALIDATION_HISTORY_KEY,
    _arm_source_ranked_consider_revalidation_after_reset,
    _close_source_ranked_consider_fuzz_revalidation,
    _consume_source_ranked_consider_fuzz_revalidation,
    _repair_source_ranked_consider_fuzz_revalidation_history,
    _source_ranked_candidate_excluded_by_below_band_evidence,
    _source_ranked_consider_fuzz_revalidation_pending,
    _source_ranked_consider_fuzz_revalidation_should_defer,
    _source_ranked_policy_id,
)
from dd4tester.hunt_candidates import HuntCandidate


def _fixture() -> tuple[dict[str, object], HuntCandidate, SimpleNamespace]:
    candidate = HuntCandidate(
        status="caution",
        score=250.0,
        area_file="test.are",
        mobile_vnum=9306,
        target="a plain target",
        target_keyword="target",
        level=37,
        room_vnum=9306,
        room_name="Target room",
        route=("north",),
        source_spawn_limit=1,
        room_spawn_count=1,
        boot_kills=0,
        loot=(),
        source_value=0,
        contained_coins=0,
        hazards=(),
        target_identity="a plain target",
        estimated_level_range=(35, 39),
        estimated_base_hp_range=(100, 200),
        sentinel=True,
        stay_area=True,
        route_origin_room_vnum=3001,
    )
    policy_id = _source_ranked_policy_id(candidate, character_level=39)
    state: dict[str, object] = {
        "level": 39,
        "world_boot_id": "boot-1",
        "campaign_source_revision": "source-1",
        "xp": 1_000,
        "campaign_xp_loss_total": 0,
        "max_hp": 500,
        "dead": False,
        "in_combat": False,
        _SOURCE_RANKED_CONSIDER_RESET_WAIT_KEY: {
            "boot_id": "boot-1",
            "level": 39,
            "after_segment_id": 77,
        },
        "campaign_below_band_policy_exclusions": {
            policy_id: {
                "level": 39,
                "boot_id": "boot-1",
                "source_mobile_keys": ["mobile:9306"],
                "targets": ["a plain target"],
            }
        },
        "campaign_research_results": {
            policy_id: {
                "boot_id": "boot-1",
                "observed": True,
                "consider_viable": False,
                "completed_kill": False,
                "viable": False,
                "xp_delta": 0,
            }
        },
    }
    mobile = SimpleNamespace(
        aggressive=False,
        fear_aura=False,
        non_corporeal=False,
        programs=(),
    )
    world = SimpleNamespace(
        mobiles={9306: mobile},
        mobile_specials={},
    )
    return state, candidate, world


def test_area_reset_opens_one_exact_live_consider_recheck() -> None:
    state, candidate, world = _fixture()
    policy_id = _source_ranked_policy_id(candidate, character_level=39)

    assert _source_ranked_candidate_excluded_by_below_band_evidence(
        candidate, state, character_level=39
    )

    armed = _arm_source_ranked_consider_revalidation_after_reset(
        state,
        [candidate],
        character_level=39,
        source_world=world,
    )

    marker = armed["campaign_source_ranked_consider_fuzz_revalidation"]
    assert marker["status"] == "pending"
    assert marker["policy_id"] == policy_id
    assert marker["maximum_level_offset"] == 5
    assert not _source_ranked_candidate_excluded_by_below_band_evidence(
        candidate, armed, character_level=39
    )
    assert _source_ranked_consider_fuzz_revalidation_pending(
        armed, candidate, character_level=39
    )

    assert _consume_source_ranked_consider_fuzz_revalidation(
        armed, candidate, character_level=39
    )
    reset_marker = armed[_SOURCE_RANKED_CONSIDER_RESET_WAIT_KEY]
    assert reset_marker["revalidation_count"] == 1
    assert reset_marker["revalidation_targets"] == [
        {
            "policy_id": policy_id,
            "mobile_vnum": candidate.mobile_vnum,
            "room_vnum": candidate.room_vnum,
        }
    ]
    assert armed[_SOURCE_RANKED_CONSIDER_FUZZ_REVALIDATION_HISTORY_KEY][0][
        "policy_id"
    ] == policy_id
    assert not _source_ranked_consider_fuzz_revalidation_pending(
        armed, candidate, character_level=39
    )


def test_area_reset_recheck_does_not_arm_without_reset_boundary() -> None:
    state, candidate, world = _fixture()
    state.pop(_SOURCE_RANKED_CONSIDER_RESET_WAIT_KEY)

    assert _arm_source_ranked_consider_revalidation_after_reset(
        state,
        [candidate],
        character_level=39,
        source_world=world,
    ) == state


def test_area_reset_recheck_uses_compacted_source_exclusion() -> None:
    state, candidate, world = _fixture()
    state.pop("campaign_research_results")

    armed = _arm_source_ranked_consider_revalidation_after_reset(
        state,
        [candidate],
        character_level=39,
        source_world=world,
    )

    assert armed["campaign_source_ranked_consider_fuzz_revalidation"][
        "status"
    ] == "pending"


def test_area_reset_recheck_does_not_repeat_an_attempted_negative() -> None:
    state, candidate, world = _fixture()
    policy_id = _source_ranked_policy_id(candidate, character_level=39)
    state[_SOURCE_RANKED_CONSIDER_RESET_WAIT_KEY] = {
        "boot_id": "boot-1",
        "level": 39,
        "after_segment_id": 88,
    }
    state["campaign_source_ranked_consider_fuzz_revalidation"] = {
        "status": "attempted",
        "world_boot_id": "boot-1",
        "level": 39,
        "policy_id": policy_id,
        "reset_after_segment_id": 77,
    }

    armed = _arm_source_ranked_consider_revalidation_after_reset(
        state,
        [candidate],
        character_level=39,
        source_world=world,
    )

    assert armed["campaign_source_ranked_consider_fuzz_revalidation"][
        "status"
    ] == "attempted"
    assert armed["campaign_source_ranked_consider_fuzz_revalidation"][
        "reset_after_segment_id"
    ] == 77


def test_pending_consider_recheck_can_close_before_unrelated_rotation() -> None:
    state, candidate, world = _fixture()
    armed = _arm_source_ranked_consider_revalidation_after_reset(
        state,
        [candidate],
        character_level=39,
        source_world=world,
    )

    assert _close_source_ranked_consider_fuzz_revalidation(
        armed,
        reason="exact candidate failed ordinary selector gates",
    )
    marker = armed["campaign_source_ranked_consider_fuzz_revalidation"]
    assert marker["status"] == "closed"
    assert marker["reason"] == "exact candidate failed ordinary selector gates"
    assert not _source_ranked_consider_fuzz_revalidation_pending(
        armed,
        candidate,
        character_level=39,
    )


def test_area_reset_recheck_history_blocks_an_older_attempted_negative() -> None:
    state, candidate, world = _fixture()
    policy_id = _source_ranked_policy_id(candidate, character_level=39)
    state[_SOURCE_RANKED_CONSIDER_RESET_WAIT_KEY] = {
        "boot_id": "boot-1",
        "level": 39,
        "after_segment_id": 99,
    }
    state[_SOURCE_RANKED_CONSIDER_FUZZ_REVALIDATION_HISTORY_KEY] = [
        {
            "world_boot_id": "boot-1",
            "level": 39,
            "policy_id": policy_id,
            "mobile_vnum": candidate.mobile_vnum,
            "room_vnum": candidate.room_vnum,
        }
    ]

    armed = _arm_source_ranked_consider_revalidation_after_reset(
        state,
        [candidate],
        character_level=39,
        source_world=world,
    )

    assert armed[_SOURCE_RANKED_CONSIDER_FUZZ_REVALIDATION_HISTORY_KEY][0][
        "policy_id"
    ] == policy_id
    assert "campaign_source_ranked_consider_fuzz_revalidation" not in armed


def test_weak_reset_recheck_defers_to_a_likely_current_hunt() -> None:
    _, candidate, _ = _fixture()
    weak = replace(
        candidate,
        mobile_vnum=9308,
        room_vnum=9308,
        target="a weak reset target",
        target_keyword="weak",
        target_identity="a weak reset target",
        estimated_level_range=(32, 36),
    )
    likely_current = replace(
        candidate,
        mobile_vnum=9309,
        room_vnum=9309,
        target="a likely current target",
        target_keyword="likely",
        target_identity="a likely current target",
        estimated_level_range=(40, 44),
    )

    assert _source_ranked_consider_fuzz_revalidation_should_defer(
        weak,
        likely_current,
        "fresh",
        character_level=39,
    )


def test_reset_recheck_remains_available_without_a_likely_current_hunt() -> None:
    _, candidate, _ = _fixture()
    weak = replace(
        candidate,
        mobile_vnum=9310,
        room_vnum=9310,
        estimated_level_range=(32, 36),
    )

    assert not _source_ranked_consider_fuzz_revalidation_should_defer(
        weak,
        None,
        None,
        character_level=39,
    )


def test_other_revalidation_keeps_priority_over_reset_deferral() -> None:
    _, candidate, _ = _fixture()
    weak = replace(
        candidate,
        mobile_vnum=9311,
        room_vnum=9311,
        estimated_level_range=(32, 36),
    )
    likely_current = replace(
        candidate,
        mobile_vnum=9312,
        room_vnum=9312,
        estimated_level_range=(40, 44),
    )

    assert not _source_ranked_consider_fuzz_revalidation_should_defer(
        weak,
        likely_current,
        "fresh",
        character_level=39,
        other_revalidation_selected=True,
    )


def test_repair_recovers_multiple_current_boot_attempts_from_segment_tail() -> None:
    state, candidate, _ = _fixture()
    second = replace(
        candidate,
        mobile_vnum=9307,
        room_vnum=9307,
        target="a second plain target",
        target_keyword="second",
        target_identity="a second plain target",
        route=("east",),
        route_origin_room_vnum=3002,
    )
    first_policy_id = _source_ranked_policy_id(candidate, character_level=39)
    second_policy_id = _source_ranked_policy_id(second, character_level=39)

    repaired = _repair_source_ranked_consider_fuzz_revalidation_history(
        state,
        [
            {
                "id": 101,
                "end_state_json": json.dumps(
                    {
                        "campaign_source_ranked_consider_fuzz_revalidation": {
                            "status": "attempted",
                            "world_boot_id": "boot-1",
                            "level": 39,
                            "policy_id": first_policy_id,
                            "mobile_vnum": candidate.mobile_vnum,
                            "room_vnum": candidate.room_vnum,
                            "campaign_source_revision": "source-1",
                            "reset_after_segment_id": 77,
                        }
                    }
                ),
            },
            {
                "id": 102,
                "end_state_json": json.dumps(
                    {
                        "campaign_source_ranked_consider_fuzz_revalidation": {
                            "status": "closed",
                            "world_boot_id": "boot-1",
                            "level": 39,
                            "policy_id": second_policy_id,
                            "mobile_vnum": second.mobile_vnum,
                            "room_vnum": second.room_vnum,
                            "campaign_source_revision": "source-1",
                            "reset_after_segment_id": 88,
                        }
                    }
                ),
            },
        ],
    )

    history = repaired[_SOURCE_RANKED_CONSIDER_FUZZ_REVALIDATION_HISTORY_KEY]
    assert {record["policy_id"] for record in history} == {
        first_policy_id,
        second_policy_id,
    }
