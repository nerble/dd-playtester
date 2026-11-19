from dataclasses import replace
from pathlib import Path

import pytest

import dd4tester.campaign as campaign
from dd4tester.hunt_candidates import load_world_source, rank_hunt_candidates


SOURCE_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "runs"
    / "dd4-source"
    / "server"
    / "area"
)


@pytest.fixture(scope="module")
def source_world():
    return load_world_source(SOURCE_DIRECTORY, include_all_areas=True)


@pytest.fixture(scope="module")
def master_elf(source_world):
    candidates = rank_hunt_candidates(
        source_world,
        character_level=39,
        character_class="Warrior",
        character_subclass="Knight",
        include_below_band=True,
        character_max_hp=937,
        include_level_ceiling_candidates=True,
        level_ceiling_offset=5,
        include_all_areas=True,
    )
    return next(candidate for candidate in candidates if candidate.mobile_vnum == 9927)


def _prepared_state() -> dict[str, object]:
    return {
        "world_boot_id": "boot-1",
        "max_hp": 937,
        "hp": 937,
        "combat_pouch_potions": {"purple": 2},
        "verified_combat_pouch_potions": {"purple": 2},
    }


def test_master_elf_exception_matches_only_the_source_reset(master_elf, source_world):
    assert campaign._source_ranked_master_elf_risk_shape_allowed(
        master_elf,
        source_world,
    )
    assert campaign._source_ranked_master_elf_route_risk_allowed(
        master_elf,
        source_world,
        character_level=39,
    )

    wrong_mobile = replace(master_elf, mobile_vnum=9928)
    wrong_weapon = replace(master_elf, equipped_weapons=())
    wrong_room = replace(master_elf, room_vnum=9946)
    assert not campaign._source_ranked_master_elf_risk_shape_allowed(
        wrong_mobile,
        source_world,
    )
    assert not campaign._source_ranked_master_elf_risk_shape_allowed(
        wrong_weapon,
        source_world,
    )
    assert not campaign._source_ranked_master_elf_risk_shape_allowed(
        wrong_room,
        source_world,
    )


def test_master_elf_special_is_not_a_static_protection_gate(master_elf, source_world):
    state = _prepared_state()
    assert campaign._audited_source_special_candidate_allowed(
        master_elf,
        state=state,
        character_max_hp=937,
        source_world=source_world,
    )
    assert not campaign._source_ranked_candidate_requires_sanctuary(master_elf)
    assert campaign._source_ranked_special_candidate_in_live_level_ceiling(
        master_elf,
        character_level=39,
    )

    no_sanctuary = {
        **state,
        "combat_pouch_potions": {},
        "verified_combat_pouch_potions": {},
    }
    assert campaign._audited_source_special_candidate_allowed(
        master_elf,
        state=no_sanctuary,
        character_max_hp=937,
        source_world=source_world,
    )

    too_high = replace(master_elf, level=41)
    assert campaign._source_ranked_special_candidate_in_live_level_ceiling(
        too_high,
        character_level=39,
    )


@pytest.mark.parametrize("character_level", [43, 45])
def test_master_elf_route_closes_when_source_fuzz_can_reach_xp_floor(
    master_elf,
    source_world,
    character_level,
):
    assert not campaign._source_ranked_master_elf_route_risk_allowed(
        master_elf,
        source_world,
        character_level=character_level,
    )
    state = {**_prepared_state(), "level": character_level}
    assert campaign._source_ranked_candidate_in_current_band(
        master_elf,
        state,
        world=source_world,
        character_level=character_level,
        character_max_hp=937,
    )


def test_other_level_40_undead_casters_remain_closed(master_elf, source_world):
    other = replace(
        master_elf,
        mobile_vnum=3404,
        target="The guardian vampire",
        target_keyword="vampire",
    )
    assert not campaign._source_ranked_master_elf_risk_shape_allowed(
        other,
        source_world,
    )
    assert not campaign._audited_source_special_candidate_allowed(
        other,
        state=_prepared_state(),
        character_max_hp=937,
        source_world=source_world,
    )
