import pytest

from dd4tester.character import CharacterSpec
from dd4tester.fastwalks import route_named
from dd4tester.hunt_candidates import ACT_SENTINEL, MobileSource, WorldSource
from dd4tester.starter import FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


DESCRIPTION = "A deer stands here rubbing his antlers against a tree."


def _encounter():
    world = WorldSource(mobiles={19039: MobileSource(
        19039, "deer buck", "the buck", 28, ACT_SENTINEL, 0, "test.are",
        room_description=DESCRIPTION,
    )})
    spec = CharacterSpec.from_mapping({
        "name": "AliasTest", "race": "human", "gender": "male", "class": "warrior",
    })
    stop = FieldHuntStop(
        (), "deer", source_mobile_vnum=19039, source_reset_room_vnum="19132",
        source_mobile_room_description=DESCRIPTION,
        source_policy_id="source-ranked-hunt-mirror-realm-19039-19132-31",
    )
    policy = StarterPolicy(spec, "test-password", fastwalk_route=route_named("moria"),
                           fastwalk_hunt_stops=(stop,), source_world=world)
    policy.current_room = "19132"
    policy.enemy_snapshot_room = "19132"
    policy.world_boot_id = "boot"
    policy.fastwalk_attack_started = True
    policy.fastwalk_attack_target = "deer"
    policy.active_target = "deer"
    policy.unapproved_field_attacker = "The buck"
    policy.room_targets["19132"] = ["deer"]
    policy.room_target_counts["19132"] = {"deer": 1}
    policy.room_target_selectors["19132"] = {"deer": ["#25032"]}
    policy.room_target_selector_descriptions["19132"] = {"#25032": DESCRIPTION}
    state = CharacterState(level=31, room_vnum="19132", enemies=[[{
        "name": "the buck", "isnpc": "19039", "long_desc": DESCRIPTION,
        "hp": "687", "maxhp": "784",
    }]])
    return policy, state


def test_current_primary_display_name_is_not_an_extra_attacker() -> None:
    policy, state = _encounter()
    assert policy._reconcile_source_primary_attacker(state)
    assert policy.unapproved_field_attacker is None
    assert policy.active_target == "the buck"
    assert policy.active_target_selector == "#25032"
    assert policy.active_target_mobile_vnum == 19039
    assert len(policy._combat_session.source_attacker_aliases) == 1
    assert policy.fastwalk_attack_started
    assert not policy.fastwalk_objective_budget_complete


def test_selected_primary_enemy_is_bound_before_alias_reconciliation() -> None:
    policy, state = _encounter()
    policy.active_target = None
    policy.active_target_selector = None
    policy.active_target_mobile_vnum = None
    policy.fastwalk_attack_target = None
    policy.unapproved_field_attacker = None

    policy._reconcile_live_enemy_state(policy._current_room_enemy_records(state))

    assert policy.unapproved_field_attacker is None
    assert policy.active_target == "the buck"
    assert policy.active_target_mobile_vnum == 19039


@pytest.mark.parametrize("failure", (
    "wrong_mobile", "wrong_room", "wrong_description", "wrong_name", "other_attacker",
    "extra_enemy", "duplicate_enemy", "stale", "selector_conflict", "not_opened",
    "completed", "two_room_targets", "no_source", "unbound_snapshot", "budget_spent",
))
def test_alias_reconciliation_cannot_hide_changed_or_crowded_encounter(failure: str) -> None:
    policy, state = _encounter()
    enemy = state.enemies[0][0]
    if failure == "wrong_mobile":
        enemy["isnpc"] = "19040"
    elif failure == "wrong_room":
        state.room_vnum = "19133"
    elif failure == "wrong_description":
        enemy["long_desc"] = "A different deer is here."
    elif failure == "wrong_name":
        enemy["name"] = "another deer"
    elif failure == "other_attacker":
        policy.unapproved_field_attacker = "The moose"
    elif failure == "extra_enemy":
        state.enemies[0].append({"name": "a moose", "isnpc": "19048"})
    elif failure == "duplicate_enemy":
        state.enemies[0].append(dict(enemy))
    elif failure == "stale":
        policy.enemy_snapshot_stale = True
    elif failure == "selector_conflict":
        policy.active_target_selector = "#25033"
    elif failure == "not_opened":
        policy.fastwalk_attack_started = False
    elif failure == "completed":
        policy.fastwalk_objective_budget_complete = True
    elif failure == "two_room_targets":
        policy.room_target_counts["19132"]["deer"] = 2
    elif failure == "no_source":
        policy.source_world = None
    elif failure == "unbound_snapshot":
        policy.enemy_snapshot_room = None
    else:
        policy._combat_session.source_attacker_aliases = [{}] * 8
    assert not policy._reconcile_source_primary_attacker(state)
    assert policy.unapproved_field_attacker is not None
