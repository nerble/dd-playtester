from dataclasses import replace
import json

import pytest

from dd4tester.character import CharacterSpec
from dd4tester.fastwalks import Fastwalk
from dd4tester.hunt_candidates import (
    ACT_SENTINEL, HuntCandidate, MobReset, MobileSource, RoomSource,
    WorldSource, load_world_source,
)
from dd4tester.campaign_migrations import target_inspection_revalidation_evidence
from dd4tester.starter import BotDecision, FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState
from dd4tester.target_inspection import (
    INSPECTION_REVALIDATION_KEY, TargetInspectionController, distinguishable_descriptions,
    inspection_revalidation_pending,
)


DESCRIPTIONS = {101: "She looks like an ordinary woman.",
                102: "He looks like an ordinary guy."}


def start(controller: TargetInspectionController, *, selector: str = "#123", visit: int = 0) -> bool:
    return controller.begin(room="301", selector=selector, expected=101,
                            descriptions=DESCRIPTIONS, name="a citizen", level=30,
                            boot="boot", visit=visit, now=10)


def verified(controller: TargetInspectionController, **changes) -> bool:
    context = dict(room="301", selector="#123", expected=101, descriptions=DESCRIPTIONS,
                   level=30, boot="boot", visit=0, now=12)
    return controller.verified(**(context | changes))


def absent(controller: TargetInspectionController, **changes) -> bool:
    context = dict(room="301", selector="#123", expected=101, descriptions=DESCRIPTIONS,
                   level=30, boot="boot", visit=0, now=12)
    return controller.absent(**(context | changes))


def test_look_receipt_requires_complete_fragmented_description_and_health_line() -> None:
    controller = TargetInspectionController()
    assert start(controller)
    controller.observe("She looks like an ord", now=11)
    assert not verified(controller)
    controller.observe("inary woman.\nA citizen is in perfect health.\n", now=11.5)
    assert verified(controller)
    assert controller.records[0]["actual"] == 101
    assert "descriptions" not in controller.records[0]


@pytest.mark.parametrize("changes", [
    {"selector": "#124"}, {"room": "302"}, {"level": 31}, {"boot": "another"},
    {"visit": 1}, {"now": 32}, {"descriptions": {101: "changed", 102: DESCRIPTIONS[102]}},
])
def test_inspection_never_survives_changed_instance_or_context(changes) -> None:
    controller = TargetInspectionController()
    assert start(controller)
    controller.observe(DESCRIPTIONS[101] + "\nA citizen is in perfect health.\n", now=11)
    assert not verified(controller, **changes)


def test_different_prototype_is_a_negative_identity_not_combat_permission() -> None:
    controller = TargetInspectionController()
    assert start(controller)
    controller.observe(DESCRIPTIONS[102] + "\nA citizen is in perfect health.\n", now=11)
    assert not verified(controller)
    assert controller.receipt["status"] == "different_prototype"
    assert controller.records[0]["actual"] == 102
    assert not start(controller)


def test_explicit_missing_instance_reply_is_a_context_bound_absence_receipt() -> None:
    controller = TargetInspectionController()
    assert start(controller)
    controller.observe("You do not see that here.\n", now=11)

    assert absent(controller)
    assert controller.receipt["status"] == "absent"
    assert controller.receipt["reason"] == "target instance is no longer in the room"
    assert controller.records[0]["actual"] is None
    assert not absent(controller, selector="#124")


def test_partial_missing_instance_reply_does_not_close_the_look_receipt() -> None:
    controller = TargetInspectionController()
    assert start(controller)
    controller.observe("You do not see that", now=11)

    assert controller.pending is not None
    assert controller.receipt is None


def test_timeout_does_not_accept_late_or_unacknowledged_look() -> None:
    controller = TargetInspectionController()
    assert start(controller)
    controller.observe(DESCRIPTIONS[101], now=11)
    assert controller.poll(now=15, room="301", level=30, boot="boot", in_combat=False) is False
    controller.observe(DESCRIPTIONS[101] + "\nA citizen is in perfect health.\n", now=16)
    assert not verified(controller)
    assert controller.receipt["status"] == "failed"


def test_new_combat_invalidates_pending_read_only_inspection() -> None:
    controller = TargetInspectionController()
    assert start(controller)
    assert not controller.poll(now=11, room="301", level=30, boot="boot", in_combat=True)
    assert controller.receipt["reason"] == "target look context changed"


def test_identical_missing_or_unknown_look_descriptions_do_not_identify_a_mobile() -> None:
    assert not distinguishable_descriptions({101: "same", 102: "same"}, 101)
    assert not distinguishable_descriptions({101: "known", 102: ""}, 101)
    controller = TargetInspectionController()
    assert start(controller)
    controller.observe("Someone else.\nA citizen is in perfect health.\n", now=11)
    assert controller.receipt["status"] == "failed"


def test_look_inspections_retain_a_finite_run_budget() -> None:
    controller = TargetInspectionController()
    for visit in range(8):
        assert start(controller, visit=visit)
        controller.observe(DESCRIPTIONS[102] + "\nA citizen is in perfect health.\n", now=11)
    assert not start(controller, visit=8)


def test_mobile_parser_preserves_the_source_look_description(tmp_path) -> None:
    (tmp_path / "identity.are").write_text(
        "#AREA\nidentity~\n#MOBILES\n#101\ncitizen~\na citizen~\n"
        "A citizen stands here.~\nShe looks like an ordinary woman.~\n"
        "64 0 0 S\n30 0 0 1d1+1 1d1+1\n0 0\n0 0 2\n#0\n#$\n",
        encoding="utf-8",
    )
    world = load_world_source(tmp_path, include_all_areas=True)
    assert world.mobiles[101].description == DESCRIPTIONS[101]


@pytest.mark.parametrize("target", ["a citizen", "citizen"])
def test_starter_uses_look_before_consider_for_an_isolated_source_ambiguity(monkeypatch, target: str) -> None:
    monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: 10)
    world = WorldSource(mobiles={
        101: MobileSource(101, "citizen", "a citizen", 30, 64, 0, "identity.are",
                          description=DESCRIPTIONS[101]),
        102: MobileSource(102, "citizen", "a citizen", 32, 64, 0, "identity.are",
                          description=DESCRIPTIONS[102]),
    })
    policy = StarterPolicy(
        CharacterSpec(name="Sample", password_env="TEST_PASSWORD", race="human",
                      gender="male", character_class="warrior"), "unused",
        source_world=world, fastwalk_route=Fastwalk("identity", 1, 100, "1n"),
        fastwalk_hunt_stops=(FieldHuntStop((), target, exact_target=True,
                                          source_mobile_vnum=101, source_target_armed=False),),
        source_mobile_vnums_by_target_room={"a citizen": {"301": (101, 102)}},
    )
    policy.current_room = "301"
    policy.world_boot_id = "boot"
    policy.fastwalk_attack_target = target
    policy.room_targets["301"] = [target]
    policy.room_target_selectors["301"] = {target: ("#123",)}
    state = CharacterState(level=30, room_vnum="301", hp=700, max_hp=700)
    decision = policy._consider_fastwalk_target(state)
    assert decision.command == "look #123"
    policy.observe_text(DESCRIPTIONS[101] + "\nA citizen is in perfect health.\n")
    assert policy._source_target_reachability_issue(state, policy.fastwalk_hunt_stops[0], "a citizen") is None
    world.mobiles[102] = replace(world.mobiles[102], programs=world.mobiles[101].programs,
                                 description=DESCRIPTIONS[101])
    assert policy._source_target_reachability_issue(state, policy.fastwalk_hunt_stops[0], "a citizen") is not None


def test_starter_checks_both_duplicate_exact_ids_but_keeps_the_crowd_gate(monkeypatch) -> None:
    monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: 10)
    world = WorldSource(mobiles={
        101: MobileSource(101, "citizen", "a citizen", 30, 64, 0, "identity.are",
                          description=DESCRIPTIONS[101]),
        102: MobileSource(102, "citizen", "a citizen", 32, 64, 0, "identity.are",
                          description=DESCRIPTIONS[102]),
    })
    stop = FieldHuntStop(
        (), "a citizen", exact_target=True, source_mobile_vnum=101,
    )
    policy = StarterPolicy(
        CharacterSpec(name="Sample", password_env="TEST_PASSWORD", race="human",
                      gender="male", character_class="warrior"), "unused",
        source_world=world, fastwalk_route=Fastwalk("identity", 1, 100, "1n"),
        fastwalk_hunt_stops=(stop,),
        source_mobile_vnums_by_target_room={"a citizen": {"301": (101, 102)}},
    )
    policy.current_room = "301"
    policy.world_boot_id = "boot"
    policy.fastwalk_attack_target = "a citizen"
    policy.room_targets["301"] = ["a citizen", "a citizen"]
    policy.room_target_selectors["301"] = {"a citizen": ["#123", "#124"]}
    policy.room_target_selector_descriptions["301"] = {
        "#123": "A citizen of Westreen is standing here.",
        "#124": "A citizen of Westreen is standing here.",
    }
    state = CharacterState(level=30, room_vnum="301", hp=700, max_hp=700)

    first = policy._consider_fastwalk_target(state)
    assert first.command == "look #124"
    policy.observe_text(DESCRIPTIONS[102] + "\nA citizen is in perfect health.\n")

    second = policy._consider_fastwalk_target(state)
    assert second.command == "look #123"
    policy.observe_text(DESCRIPTIONS[101] + "\nA citizen is in perfect health.\n")
    assert policy._source_target_reachability_issue(state, stop, "a citizen") is None
    assert policy._target_selector_for("a citizen", stop, state=state) == "#123"

    crowded = policy._consider_fastwalk_target(state)
    assert crowded.command == "look"
    assert "skip a crowded circuit target" in crowded.reason
    assert policy.fastwalk_attack_started is False


def stale_wandering_target_case(*, act_flags: int = 0):
    policy_id = "source-ranked-hunt-101-201-30"
    world = WorldSource(
        rooms={
            201: RoomSource(201, "hall", "identity.are"),
            202: RoomSource(202, "hall", "identity.are"),
        },
        mobiles={
            101: MobileSource(101, "clan member", "a clan member", 30, act_flags,
                              0, "identity.are", description=DESCRIPTIONS[101]),
            102: MobileSource(102, "clan member", "a clan member", 31, ACT_SENTINEL,
                              0, "identity.are", description=DESCRIPTIONS[102]),
        },
    )
    locator = FieldHuntStop(
        (), where_target="clan member", command_keyword="clan",
        actions=("where clan",), where_source_mobile_vnum=101,
        maximum_where_relocations=2,
        where_location_routes=(("hall", ("201", "202")),),
        where_relocation_routes=(("201", "hall", ("202",)),),
        preserve_where_route_waypoints=True,
    )
    target = FieldHuntStop(
        (), "a clan member", route_vnums=("201",), exact_target=True,
        require_isolated=True, source_mobile_vnum=101,
        source_policy_id=policy_id, source_target_armed=False,
    )
    policy = StarterPolicy(
        CharacterSpec(name="Sample", password_env="TEST_PASSWORD", race="human",
                      gender="male", character_class="warrior"), "unused",
        source_world=world, fastwalk_route=Fastwalk("identity", 1, 100, "1n"),
        fastwalk_hunt_stops=(locator, target), fastwalk_kill_limit=2,
        source_mobile_vnums_by_target_room={
            "a clan member": {"201": (101, 102)},
        },
    )
    policy.fastwalk_hunt_stop_index = 1
    policy.current_room = "201"
    policy.world_boot_id = "boot"
    policy.fastwalk_attack_target = target.target
    policy.fastwalk_target_present_observed = True
    policy.fastwalk_locator_target_present_observed = True
    inspection = policy._travel_session.target_inspection
    assert inspection.begin(
        room="201", selector="#123", expected=101, descriptions=DESCRIPTIONS,
        name="a clan member", level=30, boot="boot", visit=1, now=10,
    )
    inspection.observe("You do not see that here.\n", now=11)
    return policy, target


def test_stale_wandering_instance_refreshes_only_through_registered_where(monkeypatch) -> None:
    monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: 12)
    policy, _target = stale_wandering_target_case()

    decision = policy._consider_fastwalk_target(
        CharacterState(level=30, room_vnum="201", hp=700, max_hp=700),
    )

    assert decision == BotDecision(
        "where clan",
        "refresh the registered locator after the exact wandering instance left",
    )
    assert policy.fastwalk_where_relocation_attempts == 1
    assert policy.fastwalk_where_relocation_query_active is True
    assert policy.fastwalk_attack_target is None
    assert policy._travel_session.target_inspection.records[0]["status"] == "absent"


def test_stale_sentinel_instance_is_skipped_without_locator_or_combat(monkeypatch) -> None:
    monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: 12)
    policy, _target = stale_wandering_target_case(act_flags=ACT_SENTINEL)

    decision = policy._consider_fastwalk_target(
        CharacterState(level=30, room_vnum="201", hp=700, max_hp=700),
    )

    assert decision is not None and decision.command == "look"
    assert policy.fastwalk_where_relocation_attempts == 0
    assert policy.fastwalk_where_relocation_query_active is False
    assert policy.fastwalk_hunt_stop_skipped is True
    assert policy.fastwalk_attack_target is None


def revalidation_fixture():
    candidate = HuntCandidate(
        "reject", 1, "identity.are", 101, "a citizen", "citizen", 30, 301, "street",
        ("north",), 4, 1, 0, (), 0, 0, (),
    )
    policy_id = "source-ranked-hunt-identity-101-301-30"
    issue = "live identity 'citizen' is source-ambiguous in room 301: mobile VNUMs 101, 102 can reach it (expected 101)"
    result = {"boot_id": "boot", "observed": False, "viable": False, "route_hazard": issue}
    state = {
        "level": 30, "world_boot_id": "boot", "campaign_source_revision": "revision",
        "xp": 1000, "campaign_xp_loss_total": 0, "room_vnum": "3054",
        "dead": False, "in_combat": False, "enemies": [], "hp": 700, "max_hp": 700,
        "campaign_research_results": {policy_id: result},
    }
    start = state | {"campaign_source_ranked_hunt_candidate": {
        "policy_id": policy_id, "mobile_vnum": 101, "room_vnum": 301, "route": ["north"],
    }}
    end = state | {"campaign_fastwalk_abort_reason": issue}
    segment = {
        "phase": policy_id, "status": "success", "run_id": 5, "finished_at": "finished",
        "command_count": 30, "error": None,
        "start_state_json": json.dumps(start), "end_state_json": json.dumps(end),
    }
    summary = {
        "run": {"id": 5},
        "outcomes": {"execution": "success", "objective": "not_achieved", "safety": "safe"},
        "progress": {"combat_starts": 0, "confirmed_kills": []},
    }
    world = WorldSource(
        rooms={301: RoomSource(301, "street", "identity.are")},
        mobiles={v: MobileSource(v, "citizen", "a citizen", 30 if v == 101 else 32,
                                 64, 0, "identity.are", description=d)
                 for v, d in DESCRIPTIONS.items()},
        mob_resets=[MobReset(101, 301, 4, ()), MobReset(102, 301, 4, ())],
    )
    return state, segment, summary, candidate, world, policy_id


def test_revalidation_preserves_prior_failure_and_is_consumed_once() -> None:
    state, segment, summary, candidate, world, policy_id = revalidation_fixture()
    receipt = target_inspection_revalidation_evidence(state, segment, summary, candidate, world, policy_id=policy_id)
    assert receipt is not None and receipt["prior_run_id"] == 5
    state[INSPECTION_REVALIDATION_KEY] = receipt
    assert inspection_revalidation_pending(state, candidate, policy_id)
    assert state["campaign_research_results"][policy_id] == receipt["prior_result"]
    assert target_inspection_revalidation_evidence(state, segment, summary, candidate, world, policy_id=policy_id) is None
    state[INSPECTION_REVALIDATION_KEY] = receipt | {"status": "attempted"}
    assert not inspection_revalidation_pending(state, candidate, policy_id)


@pytest.mark.parametrize("change", ["loss", "combat", "wrong_run", "crowd", "same_description", "new_revision", "new_route"])
def test_identity_revalidation_does_not_reopen_changed_or_combat_failures(change: str) -> None:
    state, segment, summary, candidate, world, policy_id = revalidation_fixture()
    if change == "loss":
        state["campaign_xp_loss_total"] = 1
    elif change == "combat":
        summary["progress"]["combat_starts"] = 1
    elif change == "wrong_run":
        summary["run"]["id"] = 6
    elif change == "crowd":
        state["campaign_research_results"][policy_id]["crowded"] = True
    elif change == "same_description":
        world.mobiles[102] = replace(world.mobiles[102], description=DESCRIPTIONS[101])
    elif change == "new_revision":
        state["campaign_source_revision"] = "other"
    elif change == "new_route":
        candidate = replace(candidate, route=("south",))
    assert target_inspection_revalidation_evidence(state, segment, summary, candidate, world, policy_id=policy_id) is None


def parser_revalidation_fixture():
    state, segment, summary, candidate, world, policy_id = revalidation_fixture()
    first = target_inspection_revalidation_evidence(state, segment, summary, candidate, world, policy_id=policy_id)
    state[INSPECTION_REVALIDATION_KEY] = json.loads(json.dumps(first | {"status": "attempted"}))
    start = json.loads(segment["start_state_json"]) | {INSPECTION_REVALIDATION_KEY: state[INSPECTION_REVALIDATION_KEY]}
    issue = "look description did not identify one source mobile"
    state["campaign_research_results"][policy_id] = {
        "boot_id": "boot", "observed": False, "viable": False, "route_hazard": issue,
    }
    end = state | {
        "campaign_fastwalk_abort_reason": issue,
        "campaign_fastwalk_target_inspections": [{
            "status": "failed", "reason": issue, "expected": 101, "actual": None,
            "room": "301", "level": 30, "boot": "boot", "selector": "#123", "visit": 0,
        }],
    }
    segment = segment | {"run_id": 6, "start_state_json": json.dumps(start), "end_state_json": json.dumps(end)}
    summary["run"]["id"] = 6
    events = [
        {"id": 10, "run_id": 6, "timestamp": "2026-10-10T00:00:00+00:00", "kind": "command",
         "payload_json": json.dumps({"command": "look #123"})},
        {"id": 11, "run_id": 6, "timestamp": "2026-10-10T00:00:00.100000+00:00", "kind": "response",
         "payload_json": json.dumps({"text": "She looks like an ordinary woman.\nA citizen is in perfect health.\n"})},
    ]
    return state, segment, summary, candidate, world, policy_id, events


def test_article_prefix_parser_repair_requires_its_complete_canonical_reply() -> None:
    state, segment, summary, candidate, world, policy_id, events = parser_revalidation_fixture()
    receipt = target_inspection_revalidation_evidence(
        state, segment, summary, candidate, world, policy_id=policy_id, recent_events=events,
    )
    assert receipt is not None and receipt["revision"] == 2
    assert receipt["matched_response_event_id"] == 11
    assert receipt["prompt_repair_of"] == state[INSPECTION_REVALIDATION_KEY]
    assert receipt["prior_run_id"] == 6
    state[INSPECTION_REVALIDATION_KEY] = receipt | {"status": "attempted"}
    assert target_inspection_revalidation_evidence(
        state, segment, summary, candidate, world, policy_id=policy_id, recent_events=events,
    ) is None


@pytest.mark.parametrize("change", ["late", "different", "intervening_command", "wrong_run", "wrong_selector", "unbounded", "source_changed"])
def test_parser_repair_never_accepts_unproven_or_changed_look_evidence(change: str) -> None:
    state, segment, summary, candidate, world, policy_id, events = parser_revalidation_fixture()
    if change == "late":
        events[1]["timestamp"] = "2026-10-10T00:00:05+00:00"
    elif change == "different":
        events[1]["payload_json"] = json.dumps({"text": "He looks like an ordinary guy.\nA citizen is in perfect health.\n"})
    elif change == "intervening_command":
        events.insert(1, events[0] | {"payload_json": json.dumps({"command": "recall"})})
    elif change == "wrong_run":
        events[1]["run_id"] = 7
    elif change == "wrong_selector":
        events[0]["payload_json"] = json.dumps({"command": "look #124"})
    elif change == "unbounded":
        events += [events[1]] * 511
    elif change == "source_changed":
        world.mobiles[101] = replace(world.mobiles[101], description="A different description.")
    assert target_inspection_revalidation_evidence(
        state, segment, summary, candidate, world, policy_id=policy_id, recent_events=events,
    ) is None
