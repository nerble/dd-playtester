from dataclasses import replace

import pytest

from dd4tester.character import CharacterSpec
from dd4tester.equipment import (
    APPLY_HIT, APPLY_HITROLL, APPLY_MANA, GearCatalog, STANCE_COMBAT,
    STANCE_RECOVERY, normalize_item_name, plan_stance_swaps,
)
from dd4tester.hunt_candidates import ObjectSetBonus, ObjectSetSource, ObjectSource
from dd4tester.observations import GameEvent
from dd4tester.starter import StarterPolicy
from dd4tester.state import CharacterState


def equipment_case():
    branch = ObjectSource(
        6104, "branch", "a long, grey branch", 5, (0, 2, 5, 7), 60,
        wear_flags=8193, level=15, affects=((APPLY_HITROLL, -2),),
    )
    club = ObjectSource(
        1521, "club large", "a large club", 5, (0, 4, 3, 7), 20000,
        wear_flags=8193, level=3,
    )
    light = replace(branch, vnum=6103, item_type=1, wear_flags=16385, affects=())
    return branch, club, light


def test_recovery_does_not_trade_primary_damage_for_a_combat_tiebreaker():
    branch, club, _ = equipment_case()
    object_set = ObjectSetSource(
        900, "combat bonus", "", (6104, 1521),
        (ObjectSetBonus(1, APPLY_HITROLL, 3),),
    )
    removals, additions = plan_stance_swaps(
        [club], [branch], STANCE_RECOVERY, object_sets=(object_set,),
    )
    assert removals == additions == []


@pytest.mark.parametrize("location", [APPLY_HIT, APPLY_MANA, 5])
def test_real_recovery_or_stat_gain_can_still_replace_primary(location):
    branch, club, _ = equipment_case()
    club = replace(club, affects=((location, 20),))
    removals, additions = plan_stance_swaps([club], [branch], STANCE_RECOVERY)
    assert removals == [branch]
    assert additions == [club]


def test_recovery_weapon_set_bonus_is_not_discarded():
    branch, club, _ = equipment_case()
    object_set = ObjectSetSource(
        900, "recovery bonus", "", (1521,), (ObjectSetBonus(1, APPLY_HIT, 40),),
    )
    removals, additions = plan_stance_swaps(
        [club], [branch], STANCE_RECOVERY, object_sets=(object_set,),
    )
    assert removals == [branch]
    assert additions == [club]


def test_combat_still_restores_the_stronger_weapon():
    branch, club, _ = equipment_case()
    removals, additions = plan_stance_swaps([branch], [club], STANCE_COMBAT)
    assert removals == [club]
    assert additions == [branch]


def policy_case():
    branch, club, light = equipment_case()
    catalog = GearCatalog({item.vnum: item for item in (branch, club, light)})
    spec = CharacterSpec.from_mapping({
        "name": "Testwarrior", "race": "dwarf", "gender": "neuter", "class": "warrior",
    })
    policy = StarterPolicy(spec, "test-password", gear_catalog=catalog)
    policy.gear_worn = [branch]
    policy.gear_wielded_vnum = branch.vnum
    policy.primary_weapon_observed = True
    return policy, branch, club, light


def test_remove_text_retains_exact_weapon_before_worn_snapshot(monkeypatch):
    policy, branch, _, _ = policy_case()
    monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: 100.0)
    policy.observe_text("You stop using a long, grey branch.\n")
    assert policy.gear_worn == []
    assert policy.primary_weapon_lost
    assert policy.gear_inventory_source_hints[normalize_item_name(branch.short_description)] == 6104

    state = CharacterState(inventory=[[{"short_desc": branch.short_description}]])
    monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: 100.01)
    policy.observe_events([
        GameEvent("equipment_changed", "gmcp", {"package": "Char.Worn", "value": []}),
    ], state)
    carried, _ = policy._gear_inventory_sources(state)
    assert carried == [branch]
    policy.observe_text("You wield a long, grey branch.\n")
    assert policy.gear_wielded_vnum == 6104


def test_removing_known_nonweapon_does_not_clear_the_primary():
    policy, branch, _, light = policy_case()
    light = replace(light, short_description="a lantern", keywords="lantern")
    policy.gear_worn.append(light)
    policy.observe_text("You stop using a lantern.\n")
    assert branch in policy.gear_worn
    assert policy.gear_wielded_vnum == 6104
    assert policy.primary_weapon_observed
    assert not policy.primary_weapon_lost


def test_unknown_removal_does_not_invent_carried_identity():
    policy, _, _, _ = policy_case()
    policy.observe_text("You stop using an unknown weapon.\n")
    assert policy.gear_inventory_source_hints == {}
    assert policy.primary_weapon_lost


def test_absent_removed_weapon_drops_its_carried_hint():
    policy, _, _, _ = policy_case()
    policy.observe_text("You stop using a long, grey branch.\n")
    carried, _ = policy._gear_inventory_sources(CharacterState(inventory=[]))
    assert carried == []
    assert policy.gear_inventory_source_hints == {}
