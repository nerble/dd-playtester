from dataclasses import replace

import pytest

from dd4tester.campaign import _catalog_primary_weapon_for_state
from dd4tester.cli import _readiness_current_gear_items
from dd4tester.equipment import GearCatalog, weapon_combat_score
from dd4tester.hunt_candidates import ObjectSource


def weapon_case():
    item = ObjectSource(3022, "sword long", "a long sword", 5, (0, 1, 6, 1), 100,
                        wear_flags=1 | (1 << 13), load_level_min=1, load_level_max=26)
    record = {"vnum": 3022, "level": 24, "name": "a long sword", "item_type": 5,
              "slot": "wield", "wear_loc": 16}
    state = {"equipment": [record], "campaign_has_weapon": True,
             "campaign_primary_weapon": "a long sword", "campaign_worn_equipment": ["a long sword"],
             "inventory": [], "campaign_empty_equipment_categories": []}
    return GearCatalog({3022: item}), state


def test_equipment_valuation_uses_observed_level_without_changing_catalog():
    catalog, state = weapon_case()
    observed = _catalog_primary_weapon_for_state(
        state, gear_catalog=catalog, character_class="warrior", subclass=None,
    )
    assert observed is not None
    assert observed.effective_level == observed.load_level_max == 24
    assert catalog.objects[3022].effective_level == 1
    assert weapon_combat_score(observed) > weapon_combat_score(catalog.objects[3022])
    assert _readiness_current_gear_items(state, catalog, character_class="warrior", subclass=None) == [observed]
    same_placement = replace(catalog.objects[3022], load_level_min=22, load_level_max=26)
    assert weapon_combat_score(same_placement) <= weapon_combat_score(observed)


@pytest.mark.parametrize("changes", [
    {"vnum": 999}, {"item_type": 9}, {"name": "another sword"},
    {"level": -1}, {"level": 101}, {"level": True}, {"level": "24"},
])
def test_conflicting_worn_identity_cannot_fall_back_to_its_name(changes):
    catalog, state = weapon_case()
    state["equipment"][0].update(changes)
    assert _readiness_current_gear_items(state, catalog, character_class="warrior", subclass=None) == []


@pytest.mark.parametrize("flag", ["campaign_has_weapon", "campaign_empty_equipment_categories"])
def test_observed_level_never_revives_a_missing_primary(flag):
    catalog, state = weapon_case()
    state[flag] = False if flag == "campaign_has_weapon" else ["wield"]
    assert _catalog_primary_weapon_for_state(
        state, gear_catalog=catalog, character_class="warrior", subclass=None,
    ) is None
    assert _readiness_current_gear_items(state, catalog, character_class="warrior", subclass=None) == []
