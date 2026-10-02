from dataclasses import replace

import pytest

from dd4tester.hunt_candidates import ObjectSource
from dd4tester.character import CharacterSpec
from dd4tester.equipment import GearCatalog
from dd4tester.fastwalks import Fastwalk
from dd4tester.hunt_candidates import WorldSource
from dd4tester.starter import FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState
from dd4tester.weapon_inspection import (
    WeaponInspection, identify_mana_reserve, source_weapon_damage, weapon_record,
)


ROW = {"slot": "wield", "vnum": 3020, "level": 5, "instance_id": "0", "name": "a dagger"}
IDENTIFY = ("You determine that a dagger is a weapon.\n"
            "It weighs 1 lbs, is worth 52 copper coins and is level 5.\n"
            "This weapon does between 3 and 8 base points of damage.\n")


def identifying() -> WeaponInspection:
    check = WeaponInspection(dict(ROW), "dagger")
    assert check.next_command(now=0, equipment=[ROW]) == "remove dagger"
    check.observe("You stop using a dagger.\n")
    assert check.next_command(now=1, equipment=[]) == "cast 'identify' dagger"
    return check


def test_live_identification_requires_rearming_and_fresh_equipment_listing() -> None:
    check = identifying()
    check.observe(IDENTIFY[:70])
    assert check.next_command(now=2, equipment=[]) is None
    check.observe(IDENTIFY[70:])
    assert check.next_command(now=3, equipment=[]) == "wield dagger"
    assert check.damage_for([ROW]) is None
    check.observe("You wield a dagger.\n")
    assert check.next_command(now=4, equipment=[ROW]) == "eq all"
    assert check.next_command(now=4.5, equipment=[ROW]) is None
    check.observe("[weapon]            a dagger\n")
    assert check.next_command(now=5, equipment=[ROW]) is None
    assert check.stage == "complete"
    assert check.damage_for([ROW]) == (3, 8)
    assert check.damage_for([]) is None
    assert check.damage_for([ROW]) is None


@pytest.mark.parametrize("response", [
    IDENTIFY.replace("a dagger", "a sword"),
    IDENTIFY.replace("level 5", "level 6"),
    IDENTIFY.replace("3 and 8", "9 and 8"),
    IDENTIFY.replace("3 and 8", "0 and 8"),
])
def test_bad_identification_still_rearms_without_damage_permission(response: str) -> None:
    check = identifying()
    check.observe(response)
    assert check.next_command(now=2, equipment=[]) == "wield dagger"
    assert check.damage is None
    assert check.failure is not None


def test_identification_timeout_has_one_rearm_and_finite_failure() -> None:
    check = identifying()
    assert check.next_command(now=6, equipment=[]) == "wield dagger"
    assert check.next_command(now=11, equipment=[]) is None
    assert check.stage == "failed"
    assert check.history.count("wield dagger") == 1
    assert check.damage_for([ROW]) is None


def test_removal_timeout_cannot_cast_or_start_another_attempt() -> None:
    check = WeaponInspection(dict(ROW), "dagger")
    check.next_command(now=0, equipment=[ROW])
    check.observe("You cannot let go of it.\n")
    assert check.next_command(now=5, equipment=[ROW]) == "wield dagger"
    check.next_command(now=10, equipment=[ROW])
    assert check.stage == "failed"
    assert all(not command.startswith("cast") for command in check.history)


def test_armour_swap_preserves_weapon_reading_but_disarm_revokes_it() -> None:
    check = WeaponInspection(dict(ROW), "dagger", stage="complete", damage=(3, 8), valid=True)
    check.observe("You stop using a war dog collar.\n")
    assert check.damage_for([ROW]) == (3, 8)
    check.observe("The warrior disarms you!\n")
    assert check.damage_for([ROW]) is None


@pytest.mark.parametrize("percent,expected", [(99, 12), (1, 59), (0, None), (-1, None), (101, None), (True, None)])
def test_identify_needs_positive_observed_practice(percent: int, expected: int | None) -> None:
    assert identify_mana_reserve({"identify": percent}) == expected


def test_generated_output_uses_live_level_not_prototype_values() -> None:
    dagger = ObjectSource(3020, "dagger", "a dagger", 5, (0, 2, 4, 11), 10, level=1)
    assert source_weapon_damage(dagger, ROW) == (1, 7)
    assert source_weapon_damage(replace(dagger, values=(0, 0, 0, 11)), ROW) == (1, 7)
    assert source_weapon_damage(dagger, None) == (1, 4)
    assert source_weapon_damage(replace(dagger, extra_flags=1 << 26), ROW) is None


def test_structured_weapon_requires_one_exact_slot() -> None:
    assert weapon_record([ROW]) == ROW
    assert weapon_record([ROW, ROW]) is None
    assert weapon_record([dict(ROW, slot="head")]) is None
    assert weapon_record([dict(ROW, level="unknown")]) is None


def prepared_policy() -> tuple[StarterPolicy, CharacterState]:
    dagger = ObjectSource(3020, "dagger", "a dagger", 5, (0, 2, 4, 11), 10, level=1)
    spec = CharacterSpec.from_mapping({"name": "Example", "race": "human", "gender": "female", "class": "mage"})
    policy = StarterPolicy(
        spec, "unused", source_world=WorldSource(objects={3020: dagger}),
        gear_catalog=GearCatalog({3020: dagger}), known_skills=("identify",),
        known_skill_levels={"identify": 99},
        fastwalk_route=Fastwalk("example", 1, 100, "s"),
        fastwalk_hunt_stops=(FieldHuntStop((), "target"),),
    )
    policy.gear_worn = [dagger]
    state = CharacterState(room_vnum="3054", position=7, mana=100, equipment=[dict(ROW)], inventory=[])
    return policy, state


def test_healer_preparation_starts_one_bounded_inspection() -> None:
    policy, state = prepared_policy()
    handled, decision = policy._weapon_inspection_decision(state)
    assert handled and decision.command == "remove dagger"
    assert policy.weapon_inspection.stage == "removing"


@pytest.mark.parametrize("change", [
    {"room_vnum": "3009"}, {"position": 4}, {"in_combat": True},
    {"mana": 12}, {"inventory": [{"short_desc": "a dagger", "quan": "1"}]},
])
def test_ineligible_preparation_cannot_remove_weapon(change: dict) -> None:
    policy, state = prepared_policy()
    for key, value in change.items():
        setattr(state, key, value)
    assert policy._weapon_inspection_decision(state) == (False, None)
    assert policy.weapon_inspection is None


def test_reconnect_revokes_live_damage_and_stops_interrupted_inspection() -> None:
    policy, state = prepared_policy()
    policy._weapon_inspection_decision(state)
    policy.on_connection_closed()
    assert policy.weapon_inspection.stage == "failed"
    assert policy.weapon_inspection.valid is False
    assert policy.return_home is True


def test_campaign_uses_generated_floor_not_zero_prototype_or_saved_live_reading(monkeypatch) -> None:
    from dd4tester import campaign

    dagger = ObjectSource(3020, "dagger", "a dagger", 5, (0, 0, 0, 11), 10, level=1)
    state = {
        "character_class": "mage", "equipment": [ROW],
        "campaign_known_skills": ["magic missile"],
        "campaign_known_skill_levels": {"magic missile": 50},
        "campaign_weapon_damage_audit": {"damage": [30, 80], "valid_in_connection": True},
    }
    monkeypatch.setattr(campaign, "source_combat_output_estimate", lambda **kwargs: kwargs)
    output = campaign._source_ranked_caster_output_for_state(
        state, character_level=11, source_world=WorldSource(objects={3020: dagger}),
    )
    assert output["weapon_vnum"] == 3020
    assert output["weapon_damage_range"] == (1, 7)
