from dataclasses import replace
from pathlib import Path

import pytest

from dd4tester import starter
from dd4tester.character import CharacterSpec
from dd4tester.encounters import displaced_sentinel_reset_room
from dd4tester.fastwalks import Fastwalk
from dd4tester.hunt_candidates import ACT_SENTINEL, ExitSource, MobileSource, MobReset, RoomSource, WorldSource
from dd4tester.observations import GameEvent
from dd4tester.starter import BotDecision, FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


DESCRIPTION = "The lemming smithy busily hammers away at a new pickaxe."
ROOM_TEXT = (
    "The lemming cavern\n\r[Exits: north (east) west]\n\r"
    "There are more lemmings here, of all sorts.\n\r"
    "[#18435] " + DESCRIPTION + "\n\r"
)


def smithy_world():
    return WorldSource(
        mobiles={29953: MobileSource(
            29953, "Lemming smithy", "the lemming smithy", 13, ACT_SENTINEL, 250,
            "lemmings.are", room_description=DESCRIPTION,
        )},
        rooms={
            29964: RoomSource(29964, "The lemming cavern", "lemmings.are", {
                "east": ExitSource("east", 29966, 1, -1, reset_state=1),
            }),
            29966: RoomSource(29966, "The lemming smithy", "lemmings.are", {
                "west": ExitSource("west", 29964, 1, -1, reset_state=1),
            }),
        },
        mob_resets=[MobReset(29953, 29966, 1, (29951,), ((16, 29951),))],
    )


def approach():
    target = "the lemming smithy"
    policy = StarterPolicy(
        CharacterSpec.from_mapping({
            "name": "Testchar", "race": "human", "gender": "female", "class": "mage",
        }), "unused", source_world=smithy_world(),
        fastwalk_route=Fastwalk("smithy route", 1, 100, "e;open east;e"),
        fastwalk_hunt_stops=(FieldHuntStop(
            (), target, exact_target=True, source_mobile_vnum=29953,
            source_mobile_room_description=DESCRIPTION, route_vnums=("29966",),
            source_reset_room_vnum="29966", require_isolated=True,
            minimum_health_ratio=.75,
        ),),
        source_mobile_targets={DESCRIPTION.lower(): (target,)},
        source_mobile_vnums_by_target_room={target: {"29966": (29953,)}},
        source_mobile_level_ranges_by_vnum={29953: (11, 15)},
    )
    policy.in_world = policy.prompt_ready = policy.fastwalk_recall_started = True
    policy.fastwalk_targetmode_configured = True
    policy.fastwalk_outbound_index = 1
    policy.current_room = "29964"
    policy.world_boot_id = "test-boot"
    state = CharacterState(
        level=18, hp=218, max_hp=218, mana=366, max_mana=628,
        move=238, max_move=320, room_vnum="29964", position=7,
        hunger=29, thirst=47, exits={"e": "29966", "w": "29961", "n": "29965"},
    )
    policy.observe_text(ROOM_TEXT)
    policy.observe_events([GameEvent("room_updated", "gmcp", {"vnum": "29964"})], state)
    return policy, state


def test_run_12825_considers_visible_displaced_smithy_instead_of_opening_door():
    policy, state = approach()
    decision = policy._fastwalk_research_decision(state)
    assert decision.command == "consider #18435"
    assert policy.fastwalk_outbound_index == 1
    assert policy.displaced_field_target.reset_room_vnum == "29966"
    assert not policy.fastwalk_attack_started
    assert policy.fastwalk_displaced_target_outcomes == [{
        "selector": "#18435", "source_mobile_vnum": 29953, "room_vnum": "29964",
        "reset_room_vnum": "29966", "stop_index": 0,
        "evidence": "unique source room description",
    }]


def test_old_reset_restriction_reproduces_walking_past_smithy(monkeypatch):
    policy, state = approach()
    monkeypatch.setattr(policy, "_displaced_target_on_approach", lambda *args: None)
    assert policy._fastwalk_research_decision(state).command == "open east"


def test_own_fresh_consider_still_required_after_identity_binding():
    policy, state = approach()
    decision = policy._fastwalk_research_decision(state)
    policy.after_command(decision)
    assert policy._fastwalk_research_decision(state) is None
    assert not policy.fastwalk_attack_started
    policy.observe_text("The lemming smithy is no match for you.\n\r")
    decision = policy._fastwalk_research_decision(state)
    assert decision.command == "look"
    assert not policy.fastwalk_attack_started
    assert policy.consider_viable is False


@pytest.mark.parametrize("change", [
    "duplicate_description", "multiple_resets", "capacity", "not_sentinel", "random",
    "no_mob", "water", "wall", "locked", "one_way", "different_area", "wrong_reset",
])
def test_source_inference_requires_single_bounded_reciprocal_reset(change):
    world = smithy_world()
    if change == "duplicate_description":
        world.mobiles[29999] = replace(world.mobiles[29953], vnum=29999)
    elif change == "multiple_resets":
        world.mob_resets.append(replace(world.mob_resets[0], room_vnum=29965))
    elif change == "capacity":
        world.mob_resets[0] = replace(world.mob_resets[0], maximum_count=2)
    elif change == "not_sentinel":
        world.mobiles[29953] = replace(world.mobiles[29953], act_flags=0)
    elif change == "random":
        world.rooms[29964].random_exits = True
    elif change == "no_mob":
        world.rooms[29964].room_flags = 4
    elif change == "water":
        world.rooms[29964].sector_type = 6
    elif change == "wall":
        world.rooms[29964].exits["east"] = ExitSource("east", 29966, 128, -1)
    elif change == "locked":
        world.rooms[29964].exits["east"] = ExitSource("east", 29966, 1, -1, reset_state=2)
    elif change == "one_way":
        world.rooms[29966].exits.clear()
    elif change == "different_area":
        world.rooms[29964].area_file = "other.are"
    else:
        world.mob_resets[0] = replace(world.mob_resets[0], room_vnum=29965)
    assert displaced_sentinel_reset_room(
        world, 29953, room_vnum=29964, direction="east", destination=29966,
        description=DESCRIPTION.lower(),
    ) is None


@pytest.mark.parametrize("change", ["old_text", "wrong_heading", "duplicate", "missing_description", "wrong_exit", "wrong_next_command"])
def test_initial_binding_needs_fresh_exact_current_room_and_planned_exit(change):
    policy, state = approach()
    if change == "old_text":
        policy.text = ""
    elif change == "wrong_heading":
        policy.text = policy.text.replace("The lemming cavern", "A different room")
    elif change == "duplicate":
        policy.room_target_selectors["29964"]["the lemming smithy"].append("#999")
    elif change == "missing_description":
        policy.room_target_selector_descriptions["29964"].clear()
    elif change == "wrong_exit":
        state.exits["e"] = "29965"
    else:
        policy.fastwalk_route = replace(policy.fastwalk_route, notation="e;n;e")
    assert policy._displaced_target_on_approach(state, policy.fastwalk_hunt_stops[0], 0) is None


@pytest.mark.parametrize("change", ["move", "disconnect", "expiry", "level", "boot", "selector", "description", "stop", "runtime"])
def test_displaced_identity_is_connection_local_and_nontransferable(change, monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(starter.time, "monotonic", lambda: clock[0])
    policy, state = approach()
    policy._fastwalk_research_decision(state)
    stop = policy.fastwalk_hunt_stops[0]
    assert policy._displaced_field_target_matches(state, stop, stop.target)
    if change == "move":
        policy.after_command(BotDecision("east", "test movement"))
    elif change == "disconnect":
        policy.on_connection_closed()
    elif change == "expiry":
        clock[0] = 130.0
    elif change == "level":
        state.level += 1
    elif change == "boot":
        policy.world_boot_id = "another-boot"
    elif change == "selector":
        policy.room_target_selectors["29964"][stop.target] = ["#999"]
    elif change == "description":
        policy.room_target_selector_descriptions["29964"]["#18435"] = "someone else"
    elif change == "stop":
        policy.fastwalk_hunt_stop_index = 1
    else:
        policy.request_runtime_boundary(state)
    assert not policy._displaced_field_target_matches(state, stop, stop.target)


def real_source_approach():
    from dd4tester import campaign
    from test_companions import prepared

    directory = Path("runs/dd4-source/server/area")
    if not directory.is_dir():
        pytest.skip("optional DD4 source mirror is not installed")
    world = campaign.load_world_source(directory, include_all_areas=True)
    policy, state = approach()
    skills = {"summon familiar": 42, "burning hands": 31}
    snapshot = {
        **state.to_dict(), "character_class": "mage", "world_boot_id": "test-boot",
        "campaign_known_skills": list(skills), "campaign_known_skill_levels": skills,
    }
    candidates = campaign.rank_hunt_candidates(
        world, character_level=18, character_class="mage", known_skills=list(skills),
        known_skill_levels=skills, include_xp_only=True, include_level_ceiling_candidates=True,
        level_ceiling_offset=1, include_all_areas=True, character_max_hp=218,
        recall_origins={0: 3001},
    )
    target = next(t for t in candidates if t.mobile_vnum == 29953 and t.room_vnum == 29966)
    policy.source_world = world
    policy.fastwalk_hunt_stops = campaign._source_ranked_hunt_stops(
        target, world, character_level=18, state=snapshot,
    )
    policy.source_mobile_targets = starter._load_source_mobile_targets(str(directory.resolve()))
    policy.source_mobile_vnums_by_target_room = starter._load_source_mobile_vnums_by_target_room(str(directory.resolve()))
    policy.source_mobile_level_ranges_by_vnum = starter._load_source_mobile_level_ranges_by_vnum(str(directory.resolve()))
    policy.known_skills, policy.known_skill_levels = set(skills), skills
    policy.familiar_preparation = prepared()
    policy.familiar_active = True
    state.room_flags = ["dark", "indoors"]
    state.sector = "inside"
    policy.after_command(BotDecision("look", "refresh the complete room listing"))
    policy.observe_text(
        ROOM_TEXT + "[#18456] A lemming miner stands here, looking frightened.\n\r"
        "[#42] <Mount> A small pony stands here grazing.\n\r"
    )
    policy.observe_events([GameEvent("room_updated", "gmcp", {"vnum": "29964"})], state)
    return policy, state


def test_real_source_smithy_with_miner_and_confirmed_familiar_reaches_order_then_opener():
    policy, state = real_source_approach()
    decision = policy._fastwalk_research_decision(state)
    assert decision.command == "consider #18435"
    policy.after_command(decision)
    policy.observe_text("The lemming smithy looks like an easy kill.\n\r")
    decision = policy._fastwalk_research_decision(state)
    assert decision.command == "order #42 kill #18435"
    policy.after_command(decision)
    assert policy.next_decision(state) is None
    policy.observe_text("Ok.\n\r")
    decision = policy._fastwalk_research_decision(state)
    assert decision.command == "order #42 flee Fear"
    policy.after_command(decision)
    policy.observe_text("The pony has fled!\n\rOk.\n\r")
    decision = policy._fastwalk_research_decision(state)
    assert decision.command.endswith("#18435")
    assert decision.command.startswith(("kill ", "cast "))


def test_displaced_identity_does_not_ignore_dangerous_bystanders():
    policy, state = approach()
    policy.source_mobile_targets["a dangerous visitor waits here."] = ("dangerous visitor",)
    policy.after_command(BotDecision("look", "refresh the complete room listing"))
    policy.observe_text(ROOM_TEXT + "[#999] A dangerous visitor waits here.\n\r")
    policy.observe_events([GameEvent("room_updated", "gmcp", {"vnum": "29964"})], state)
    decision = policy._fastwalk_research_decision(state)
    assert decision.command == "look"
    assert policy.fastwalk_crowded
    assert not policy.fastwalk_attack_started


def test_crowded_displaced_sentinel_resumes_registered_reset_room():
    policy, state = approach()
    policy.source_mobile_targets["a dangerous visitor waits here."] = ("dangerous visitor",)
    policy.after_command(BotDecision("look", "refresh the complete room listing"))
    policy.observe_text(ROOM_TEXT + "[#999] A dangerous visitor waits here.\n\r")
    policy.observe_events([GameEvent("room_updated", "gmcp", {"vnum": "29964"})], state)

    first = policy._fastwalk_research_decision(state)

    assert first is not None and first.command == "look"
    assert policy.fastwalk_crowded
    policy.after_command(first)
    policy.observe_text(ROOM_TEXT + "[#999] A dangerous visitor waits here.\n\r")
    policy.observe_events([GameEvent("room_updated", "gmcp", {"vnum": "29964"})], state)

    resumed = policy._fastwalk_research_decision(state)

    assert resumed is not None and resumed.command == "open east"
    assert policy.fastwalk_intercept_returning is False
    assert policy.fastwalk_outbound_index == 2


def test_displaced_identity_does_not_override_low_health():
    policy, state = approach()
    state.hp = 20
    assert policy._fastwalk_research_decision(state).command == "recall"
    assert not policy.fastwalk_attack_started
