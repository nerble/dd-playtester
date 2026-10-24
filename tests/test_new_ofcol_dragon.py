from dataclasses import replace
from pathlib import Path

import dd4tester.campaign as campaign_module
from dd4tester.hunt_candidates import load_world_source, rank_hunt_candidates


SOURCE = Path("runs/dd4-source/server/area")


def _dragon_candidate_and_world():
    world = load_world_source(SOURCE, include_all_areas=True)
    candidates = rank_hunt_candidates(
        world,
        character_level=39,
        character_class="warrior",
        character_subclass="knight",
        character_alignment=-7,
        character_max_hp=937,
        include_xp_only=True,
        include_level_ceiling_candidates=True,
        level_ceiling_offset=5,
        include_all_areas=True,
        recall_origins={0: 3001},
    )
    candidate = next(
        item
        for item in candidates
        if item.mobile_vnum == 631 and item.room_vnum == 693
    )
    return candidate, world


def _state():
    return {
        "world_boot_id": "test-boot",
        "character_class": "Warrior",
        "character_subclass": "Knight",
        "character_alignment": -7,
        "combat_pouch_potions": {"purple": 1},
        "verified_combat_pouch_potions": {"purple": 1},
    }


def test_exact_gold_dragon_shape_is_admitted_with_sanctuary():
    candidate, world = _dragon_candidate_and_world()
    state = _state()

    assert campaign_module._source_ancient_gold_dragon_breath_shape_allowed(
        candidate,
        world,
    )
    assert campaign_module._audited_source_special_candidate_allowed(
        candidate,
        state=state,
        character_max_hp=937,
        source_world=world,
    )
    selected = campaign_module._select_source_ranked_hunt_candidate(
        (candidate,),
        state,
        world=world,
        character_level=39,
        character_max_hp=937,
    )
    assert selected == candidate


def test_breath_exception_does_not_generalize_to_another_room():
    candidate, world = _dragon_candidate_and_world()
    altered = replace(candidate, room_vnum=692)

    assert not campaign_module._source_ancient_gold_dragon_breath_shape_allowed(
        altered,
        world,
    )
    assert not campaign_module._audited_source_special_candidate_allowed(
        altered,
        state=_state(),
        character_max_hp=937,
        source_world=world,
    )
