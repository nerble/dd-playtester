from copy import deepcopy

import pytest

from dd4tester.campaign import CampaignRunner, CampaignSpec, _state_has_source_weapon_role
from dd4tester.character import CharacterSpec
from dd4tester.equipment import GearCatalog, is_blunt_weapon, is_piercing_weapon
from dd4tester.hunt_candidates import ObjectSource, WorldSource


def branch_case():
    objects = {
        vnum: ObjectSource(
            vnum, "branch", "a long, grey branch", item_type, values, 0,
            wear_flags=1 | (1 << 13),
        )
        for vnum, item_type, values in (
            (6103, 1, (0, 0, 25, 0)),
            (6104, 5, (0, 2, 5, 7)),
            (6105, 13, (0, 0, 0, 0)),
        )
    }
    state = {
        "campaign_has_weapon": True,
        "campaign_primary_weapon": "a long, grey branch",
        "campaign_worn_equipment": ["a long, grey branch"],
        "campaign_empty_equipment_categories": [],
        "inventory": [],
        "equipment": [{
            "slot": "wield", "wear_loc": 16, "vnum": 6104,
            "name": "a long, grey branch", "item_type": 5, "level": 15,
        }],
    }
    return GearCatalog(objects), state


def has_role(catalog, state, *, worn_only=False, predicate=is_blunt_weapon):
    return _state_has_source_weapon_role(
        state, gear_catalog=catalog, character_class="warrior", subclass=None,
        predicate=predicate, worn_only=worn_only,
    )


@pytest.mark.parametrize("worn_only", [False, True])
def test_exact_equipment_vnum_resolves_duplicate_branch_names(worn_only):
    catalog, state = branch_case()
    assert catalog.match(state["campaign_primary_weapon"]).vnum == 6103
    assert has_role(catalog, state, worn_only=worn_only)
    assert not has_role(catalog, state, predicate=is_piercing_weapon)


@pytest.mark.parametrize("changes", [
    {"vnum": 6103}, {"vnum": 6105}, {"vnum": 999999},
    {"item_type": 1}, {"name": "a renamed branch"},
])
def test_conflicting_equipment_identity_cannot_fall_back_to_its_name(changes):
    catalog, state = branch_case()
    state["equipment"][0].update(changes)
    assert not has_role(catalog, state)
    assert not has_role(catalog, state, worn_only=True)


@pytest.mark.parametrize("changes", [
    {"campaign_has_weapon": False},
    {"campaign_empty_equipment_categories": ["wield"]},
    {"campaign_primary_weapon": None},
    {"campaign_primary_weapon": "another weapon"},
])
def test_stale_equipment_does_not_override_current_weapon_loss(changes):
    catalog, state = branch_case()
    state.update(changes)
    assert not has_role(catalog, state)
    assert not has_role(catalog, state, worn_only=True)


def test_exact_equipment_still_requires_class_compatibility(monkeypatch):
    catalog, state = branch_case()
    monkeypatch.setattr("dd4tester.campaign.character_can_use_item", lambda *a, **k: False)
    assert not has_role(catalog, state)


def test_a_carried_distinct_weapon_can_supply_the_other_role():
    catalog, state = branch_case()
    dagger = ObjectSource(
        8000, "dagger", "a steel dagger", 5, (0, 2, 5, 11), 0,
        wear_flags=1 | (1 << 13),
    )
    catalog = GearCatalog({**catalog.objects, dagger.vnum: dagger})
    state["inventory"] = [[{"short_desc": dagger.short_description}]]
    assert has_role(catalog, state, predicate=is_piercing_weapon)
    assert not has_role(catalog, state, predicate=is_piercing_weapon, worn_only=True)


def test_legacy_unique_worn_names_remain_usable_without_structured_identity():
    catalog, state = branch_case()
    state = deepcopy(state)
    state.pop("equipment")
    assert not has_role(catalog, state)
    unique = GearCatalog({6104: catalog.objects[6104]})
    assert has_role(unique, state)


def warrior_runner(tmp_path, catalog):
    character = CharacterSpec.from_mapping({
        "name": "Testwarrior", "race": "dwarf", "gender": "neuter", "class": "warrior",
    })
    runner = CampaignRunner(
        CampaignSpec("weapon role", tmp_path / "character.yaml", character),
        tmp_path / "campaign.yaml",
    )
    runner._gear_catalog = catalog
    runner._source_world = WorldSource(objects=catalog.objects)
    return runner


def test_warrior_with_exact_branch_does_not_request_another_stun_weapon(tmp_path):
    catalog, state = branch_case()
    state.update(level=29, campaign_known_skill_levels={"stun": 62})
    runner = warrior_runner(tmp_path, catalog)
    assert not runner._needs_pounding_weapon(state)
    state.pop("equipment")
    assert runner._needs_pounding_weapon(state)


def test_gear_ranking_receives_the_weapon_not_its_same_named_light(tmp_path, monkeypatch):
    catalog, state = branch_case()
    runner = warrior_runner(tmp_path, catalog)
    state.update(level=29, room_vnum="3054", hp=100, max_hp=100, move=100, max_move=100)
    state["inventory"] = [[{"short_desc": "a buffalo water skin"}]]
    monkeypatch.setattr("dd4tester.campaign._has_campaign_food", lambda *a, **k: True)
    monkeypatch.setattr("dd4tester.campaign._campaign_needs_healer_recovery", lambda *a: False)
    captured = []

    def capture_items(*args, **kwargs):
        captured.extend(kwargs["current_items"])
        raise RuntimeError("captured ranking input")

    monkeypatch.setattr("dd4tester.campaign.rank_executable_ground_gear_sources", capture_items)
    with pytest.raises(RuntimeError, match="captured ranking input"):
        runner._select_source_gear_placement(state)
    assert [item.vnum for item in captured] == [6104]
