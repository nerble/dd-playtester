from copy import deepcopy
from dataclasses import replace
import json

import pytest

from dd4tester import campaign as c
from dd4tester.hunt_candidates import (
    ACT_STAY_AREA, ExitSource, HuntCandidate, MobileSource, MobReset, RoomSource, WorldSource,
)
from dd4tester.storage import RunStorage
from dd4tester.temporal_evidence import single_area_locator_miss


POLICY = "source-ranked-hunt-test-100-200-11"
FAILED = "source-ranked-hunt-test-101-202-11"


def event(kind, **payload):
    return {"kind": kind, "payload_json": json.dumps(payload)}


def setup():
    state = {
        "level": 11, "xp": 50711, "hp": 186, "max_hp": 186,
        "move": 250, "max_move": 250, "room_vnum": "3054", "world_boot_id": "boot-1",
        "campaign_last_policy": POLICY,
        c._SOURCE_RANKED_RETRY_EXHAUSTED_KEY: POLICY,
        c._SOURCE_RANKED_RETRY_EXHAUSTED_BOOT_KEY: "boot-1",
        c._PROTECTION_RECOVERY_KEY: {
            "boot_id": "boot-1", "level": 11, "policy_id": FAILED, "loss_count": 1,
        },
        c._PROTECTION_RECOVERY_ORDINARY_FALLBACK_KEY: {
            "boot_id": "boot-1", "level": 11, "policy_id": POLICY, "from_policy_id": FAILED,
            "attempted": True, "attempted_policy_ids": [POLICY],
        },
    }
    end = {
        **state, "campaign_fastwalk_abort_reason": "`where` listed no exact 'wanderer' in the current area",
    }
    row = {
        "id": 1, "sequence": 1, "run_id": 1000, "phase": POLICY,
        "status": "success", "command_count": 1, "finished_at": "2026-09-07T11:00:00+00:00",
        "start_state_json": json.dumps(state), "end_state_json": json.dumps(end),
    }
    events = [
        event("game_event", type="room_entered", data={"package": "Room.Info", "vnum": "200"}),
        event("decision", command="where wanderer", category="research"),
        event("command", command="where wanderer"),
        event("response", text="You fail to find anyone by that name."),
    ]
    world = WorldSource(
        mobiles={100: MobileSource(100, "wanderer", "a wanderer", 8, 0, 0, "test.are")},
        rooms={
            200: RoomSource(200, "First room", "test.are", exits={"east": ExitSource("east", 201, 0, -1)}),
            201: RoomSource(201, "Second room", "other.are", exits={"west": ExitSource("west", 200, 0, -1)}),
        },
        mob_resets=[MobReset(100, 200, 1, ())],
    )
    candidate = HuntCandidate(
        status="caution", score=100, area_file="test.are", mobile_vnum=100,
        target="a wanderer", target_keyword="wanderer", level=8, room_vnum=200,
        room_name="First room", route=("south",), source_spawn_limit=1,
        room_spawn_count=1, boot_kills=0, loot=(), source_value=0, contained_coins=0,
        hazards=(), estimated_level_range=(6, 10), estimated_base_hp_range=(10, 20),
        estimated_peak_round_damage=10,
    )
    return state, row, events, world, candidate


def proof(row, events, **kwargs):
    return single_area_locator_miss(
        row, events, boot_id="boot-1", level=11, keyword="wanderer", reset_room=200, **kwargs,
    )


def offer(state, row, events, world, candidate):
    c._offer_source_locator_revalidations(state, (candidate,), world, (row,), {1000: events})


def test_one_expanded_search_preserves_old_attempt_and_combat_loss():
    state, row, events, world, candidate = setup()
    old = deepcopy(state)
    assert c._source_ranked_candidate_blocked_by_protection_recovery(
        candidate, state, character_level=11, character_max_hp=186,
        allow_protection_recovery_fallback=True, source_world=world,
    )
    offer(state, row, events, world, candidate)
    assert c._source_locator_revalidation_pending(state, POLICY)
    assert state[c._PROTECTION_RECOVERY_KEY] == old[c._PROTECTION_RECOVERY_KEY]
    assert state[c._PROTECTION_RECOVERY_ORDINARY_FALLBACK_KEY] == old[c._PROTECTION_RECOVERY_ORDINARY_FALLBACK_KEY]
    selected = c._select_source_ranked_hunt_candidate(
        (candidate,), state, world=world, character_level=11, character_max_hp=186,
        allow_protection_recovery_fallback=True,
    )
    assert selected == candidate
    c._consume_source_locator_revalidation(state, POLICY)
    offer(state, row, events, world, candidate)
    assert not c._source_locator_revalidation_pending(state, POLICY)
    assert c._select_source_ranked_hunt_candidate(
        (candidate,), state, world=world, character_level=11, character_max_hp=186,
        allow_protection_recovery_fallback=True,
    ) is None


@pytest.mark.parametrize("change", [
    {"xp": 50710}, {"xp": 50712}, {"level": 12}, {"world_boot_id": "boot-2"},
    {"enemy": "a guard"}, {"in_combat": True}, {"dead": True}, {"room_vnum": "3001"},
    {"campaign_died_during_segment": True}, {"campaign_fastwalk_abort_reason": "combat failed"},
    {"campaign_fastwalk_consider_outcomes": {"wanderer": False}},
])
def test_non_search_terminal_evidence_cannot_reopen_attempt(change):
    _, row, events, _, _ = setup()
    row["end_state_json"] = json.dumps({**json.loads(row["end_state_json"]), **change})
    assert proof(row, events) is None


@pytest.mark.parametrize("extra", [
    event("game_event", type="combat_started", data={}),
    event("game_event", type="health_changed", data={"current": 185}),
    event("game_event", type="vitals_changed", data={"package": "Char.Vitals", "hp": "185"}),
    event("game_event", type="progress_changed", data={"xp": 50710}),
    event("game_event", type="unknown_future_event", data={}),
    event("decision", command="kill wanderer", category="combat"),
    event("decision", command="cast fireball wanderer", category="other"),
])
def test_combat_or_unknown_actions_prevent_expanded_search(extra):
    _, row, events, _, _ = setup()
    assert proof(row, [*events, extra]) is None


@pytest.mark.parametrize("change", ["missing_room", "wrong_room", "missing_command", "missing_reply", "count", "malformed", "overflow", "two_queries"])
def test_incomplete_or_expanded_locator_evidence_does_not_rearm(change):
    _, row, events, _, _ = setup()
    if change == "missing_room":
        events.pop(0)
    elif change == "wrong_room":
        events[0] = event("game_event", type="room_entered", data={"package": "Room.Info", "vnum": "201"})
    elif change == "missing_command":
        events.pop(2)
    elif change == "missing_reply":
        events.pop()
    elif change == "count":
        row["command_count"] = 2
    elif change == "malformed":
        events[0] = {"kind": "game_event", "payload_json": "{"}
    elif change == "overflow":
        events *= 130
    else:
        events += events[1:]
        row["command_count"] = 2
    assert proof(row, events) is None


def test_partial_vitals_and_unchanged_health_are_valid_evidence():
    _, row, events, _, _ = setup()
    events += [
        event("game_event", type="vitals_changed", data={"package": "Char.Vitals", "move": "245"}),
        event("game_event", type="health_changed", data={"package": "Char.Vitals", "current": 186}),
    ]
    assert proof(row, events)["query_room_vnum"] == "200"


@pytest.mark.parametrize("change", ["cooldown", "stay_area", "unsafe_neighbor", "new_boot", "failed_fallback", "missing_events"])
def test_revalidation_requires_expired_miss_and_executable_source_extension(change):
    state, row, events, world, candidate = setup()
    if change == "cooldown":
        state["campaign_research_results"] = {POLICY: {"absent": True, "boot_id": "boot-1"}}
        state[c._RESEARCH_ABSENCE_COOLDOWN_KEY] = {POLICY: 1}
    elif change == "stay_area":
        world.mobiles[100] = replace(world.mobiles[100], act_flags=ACT_STAY_AREA)
    elif change == "unsafe_neighbor":
        world.rooms[201].room_flags = 1 << 13
    elif change == "new_boot":
        state["world_boot_id"] = "boot-2"
    elif change == "failed_fallback":
        state[c._PROTECTION_RECOVERY_ORDINARY_FALLBACK_KEY]["failed"] = True
    elif change == "missing_events":
        events = []
    offer(state, row, events, world, candidate)
    assert not c._source_locator_revalidation_pending(state, POLICY)


@pytest.mark.parametrize("status", ["running", "failed", "success"])
def test_newer_attempt_consumes_pending_permission_after_restart(status):
    state, row, events, world, candidate = setup()
    offer(state, row, events, world, candidate)
    assert c._source_locator_revalidation_pending(state, POLICY)
    newer = {**row, "id": 2, "sequence": 2, "run_id": 1001, "status": status}
    c._offer_source_locator_revalidations(state, (candidate,), world, (row, newer), {1000: events})
    assert not c._source_locator_revalidation_pending(state, POLICY)
    offer(state, row, events, world, candidate)
    assert not c._source_locator_revalidation_pending(state, POLICY)


def test_pending_revalidation_does_not_override_three_probe_or_loss_limits():
    state, row, events, world, candidate = setup()
    offer(state, row, events, world, candidate)
    state[c._PROTECTION_RECOVERY_ORDINARY_FALLBACK_KEY]["attempted_policy_ids"] += ["second", "third"]
    assert not c._source_ranked_protection_recovery_fallback_candidate_allowed(
        candidate, state, character_level=11, character_max_hp=186, source_world=world,
    )
    state[c._PROTECTION_RECOVERY_KEY]["loss_count"] = 3
    assert c._select_source_ranked_hunt_candidate(
        (candidate,), state, world=world, character_level=11, character_max_hp=186,
        allow_protection_recovery_fallback=True,
    ) is None


@pytest.mark.parametrize("key", [c._SOURCE_RANKED_XP_LOSS_POLICIES_KEY, c._SOURCE_RANKED_TIMEOUT_POLICIES_KEY])
def test_actual_loss_or_timeout_overrides_pending_search(key):
    state, row, events, world, candidate = setup()
    offer(state, row, events, world, candidate)
    state[key] = [{"boot_id": "boot-1", "level": 11, "policy_id": POLICY, "loss_count": 1}]
    assert not c._source_locator_revalidation_pending(state, POLICY)
    assert c._select_source_ranked_hunt_candidate(
        (candidate,), state, world=world, character_level=11, character_max_hp=186,
        allow_protection_recovery_fallback=True,
    ) is None


def test_throughput_exclusion_still_blocks_pending_search():
    state, row, events, world, candidate = setup()
    offer(state, row, events, world, candidate)
    state[c._SOURCE_RANKED_THROUGHPUT_LIMIT_KEY] = {"policy_id": POLICY, "level": 11}
    assert c._select_source_ranked_hunt_candidate(
        (candidate,), state, world=world, character_level=11, character_max_hp=186,
        allow_protection_recovery_fallback=True,
    ) is None


def test_other_last_target_does_not_restore_expired_search_rotation_block():
    state, row, events, world, candidate = setup()
    state["campaign_last_policy"] = "different-target"
    offer(state, row, events, world, candidate)
    assert c._select_source_ranked_hunt_candidate(
        (candidate,), state, world=world, character_level=11, character_max_hp=186,
        allow_protection_recovery_fallback=True,
    ) == candidate


def test_refreshed_source_does_not_reuse_pending_locator_permission():
    state, row, events, world, candidate = setup()
    offer(state, row, events, world, candidate)
    state[c._SOURCE_REVISION_KEY] = "new-source"
    assert not c._source_locator_revalidation_pending(state, POLICY)


@pytest.mark.parametrize("value", [True, float("inf"), float("nan")])
def test_malformed_numeric_history_is_not_locator_proof(value):
    _, row, events, _, _ = setup()
    row["start_state_json"] = json.dumps({**json.loads(row["start_state_json"]), "hp": value})
    assert proof(row, events) is None


@pytest.mark.parametrize("character_class", ["Mage", "Thief", "Warrior"])
def test_locator_revalidation_is_independent_of_character_class(character_class):
    state, row, events, world, candidate = setup()
    state["character_class"] = character_class
    offer(state, row, events, world, candidate)
    assert c._select_source_ranked_hunt_candidate(
        (candidate,), state, world=world, character_level=11, character_max_hp=186,
        allow_protection_recovery_fallback=True,
    ) == candidate


def test_event_limit_is_enforced_without_changing_default_reads(tmp_path):
    with RunStorage(tmp_path / "events.sqlite3") as store:
        run = store.create_run(scenario_name="test", scenario_path=tmp_path / "test.yaml")
        for number in range(4):
            store.record_event(run, kind="state", payload={"number": number})
        assert len(store.list_events(run)) == 4
        assert [json.loads(row["payload_json"])["number"] for row in store.list_events(run, limit=2)] == [0, 1]
        with pytest.raises(ValueError):
            store.list_events(run, limit=0)
