from dataclasses import replace
from pathlib import Path

import pytest

from dd4tester.hunt_candidates import ACT_AGGRESSIVE, MobileProgram, load_world_source
from dd4tester.observations import GameEvent
from dd4tester.starter import BotDecision
from test_starter_bystanders import _encounter


def _carrier_pair(character_class="mage"):
    policy, state = _encounter(character_class)
    state.level = 18
    state.hp = state.max_hp = 218
    mobile = replace(policy.source_world.mobiles[100], level=11, act_flags=0)
    policy.source_world.mobiles = {100: mobile}
    policy.source_mobile_level_ranges_by_vnum = {100: (9, 13)}
    policy.source_mobile_can_join_by_vnum = {100: True}
    policy.room_target_counts["200"] = {"illusionist": 2}
    policy.room_target_selectors["200"] = {"illusionist": ("#5101", "#5102")}
    policy.room_target_selector_descriptions["200"] = {
        selector: mobile.room_description.casefold()
        for selector in ("#5101", "#5102")
    }
    policy.fastwalk_hunt_stops = (
        replace(
            policy.fastwalk_hunt_stops[0],
            source_mobile_room_description=mobile.room_description,
            allow_below_band_for_required_loot=True,
            required_items=("purple potion", "purple potion"),
        ),
    )
    return policy, state


@pytest.mark.parametrize("character_class", ["mage", "thief", "warrior"])
def test_source_non_assisting_carrier_pair_still_gets_exact_consider(character_class):
    policy, state = _carrier_pair(character_class)
    assert policy._source_mobile_name_is_non_assisting_bystander("illusionist", state)

    probe = policy._consider_fastwalk_target(state)

    assert probe.command == "consider #5101"
    assert not policy.fastwalk_attack_started
    policy.after_command(probe)
    policy.observe_text("You can kill the illusionist naked and weaponless.\n")
    policy.observe_events([GameEvent("prompt_seen", "gmcp", {})], state)

    target_consider = policy._consider_fastwalk_target(state)

    assert target_consider.command == "consider #5102"
    assert policy.consider_target_selector == "#5102"
    assert not policy.fastwalk_attack_started
    assert not policy.fastwalk_crowded
    assert policy.bystander_consider_attempts == 1
    assert len(policy.fastwalk_bystander_consider_outcomes) == 1


@pytest.mark.parametrize("change", [
    "duplicate_id", "missing_id", "unknown_description", "aggressive",
    "scripted", "special", "combat", "familiar", "budget",
])
def test_duplicate_carrier_probe_retains_identity_and_hazard_checks(change):
    policy, state = _carrier_pair()
    mobile = policy.source_world.mobiles[100]
    if change == "duplicate_id":
        policy.room_target_selectors["200"]["illusionist"] = ("#5101", "#5101")
    elif change == "missing_id":
        policy.room_target_selectors["200"]["illusionist"] = ("#5101",)
    elif change == "unknown_description":
        policy.room_target_selector_descriptions["200"] = {}
    elif change == "aggressive":
        policy.source_world.mobiles[100] = replace(mobile, act_flags=ACT_AGGRESSIVE)
    elif change == "scripted":
        policy.source_world.mobiles[100] = replace(
            mobile, programs=(MobileProgram("greet_prog", "100", ("kill $n",)),),
        )
    elif change == "special":
        policy.source_world.mobile_specials[100] = ("spec_poison",)
    elif change == "combat":
        state.in_combat = True
    elif change == "familiar":
        policy.familiar_active = True
    else:
        policy.bystander_consider_attempts = 3

    assert policy._start_bystander_consider(
        state, "illusionist", {"illusionist": 2},
    ) is None
    assert not policy.fastwalk_attack_started


def test_non_target_non_assisting_duplicates_do_not_spend_probe_budget():
    policy, state = _carrier_pair()

    assert policy._start_bystander_consider(
        state, "another target", {"illusionist": 2},
    ) is None
    assert policy.bystander_consider_attempts == 0


def test_same_name_probe_does_not_authorize_below_band_xp_kills():
    policy, state = _carrier_pair()
    policy.fastwalk_hunt_stops = (
        replace(policy.fastwalk_hunt_stops[0], required_items=(),
                allow_below_band_for_required_loot=False),
    )
    probe = policy._consider_fastwalk_target(state)
    assert probe.command == "consider #5101"
    policy.after_command(probe)
    policy.observe_text("You can kill the illusionist naked and weaponless.\n")
    policy.observe_events([GameEvent("prompt_seen", "gmcp", {})], state)
    target = policy._consider_fastwalk_target(state)
    assert target.command == "consider #5102"
    policy.after_command(target)
    policy.observe_text("You can kill the illusionist naked and weaponless.\n")
    policy.observe_events([GameEvent("prompt_seen", "gmcp", {})], state)

    decision = policy._consider_fastwalk_target(state)

    assert decision.command not in {"kill #5101", "kill #5102", "backstab #5102"}
    assert not policy.fastwalk_attack_started
    assert policy.consider_viable is False


def test_run_12880_visible_carriers_reach_consider_from_room_text(monkeypatch):
    # The listing is recorded; room 200 and the later reply are replay inputs.
    world = load_world_source(Path("runs/dd4-source/server/area"), include_all_areas=True)
    mobile = world.mobiles[4055]
    policy, state = _carrier_pair()
    policy.source_world.mobiles = {4055: mobile}
    policy.source_mobile_targets = {
        mobile.room_description.strip().casefold(): ("large hobgoblin",),
    }
    policy.source_mobile_vnums_by_target_room = {"large hobgoblin": {"200": (4055,)}}
    policy.source_mobile_level_ranges_by_vnum = {4055: (mobile.level - 2, mobile.level + 2)}
    policy.source_mobile_can_join_by_vnum = {4055: True}
    policy.fastwalk_hunt_stops = (
        replace(policy.fastwalk_hunt_stops[0], target="large hobgoblin",
                source_mobile_vnum=4055,
                source_mobile_room_description=mobile.room_description),
    )
    policy.fastwalk_attack_target = "large hobgoblin"
    policy.room_target_counts.clear()
    policy.room_target_selectors.clear()
    policy.room_target_selector_descriptions.clear()
    monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: 100.0)
    policy.after_command(BotDecision("look", "refresh the located carrier room"))
    policy.observe_text(
        "The large cave\n[Exits: north east west]\n"
        "[#2789] A small mushroom is here.\n"
        "[#23896] A large hobgoblin is here wondering if he should tear you apart.\n"
        "[#23920] A large hobgoblin is here wondering if he should tear you apart.\n"
    )
    policy.observe_events([GameEvent("room_updated", "gmcp", {"vnum": "200"})], state)

    first = policy._consider_fastwalk_target(state)

    assert first.command == "consider #23896"
    policy.after_command(first)
    monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: 101.0)
    policy.observe_text("You can kill the large hobgoblin naked and weaponless.\n")
    policy.observe_events([GameEvent("prompt_seen", "gmcp", {})], state)
    assert policy._consider_fastwalk_target(state).command == "consider #23920"
    assert not policy.fastwalk_attack_started
    assert not policy.fastwalk_crowded
