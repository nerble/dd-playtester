from pathlib import Path

from dd4tester.equipment import (
    GearCatalog,
    STANCE_COMBAT,
    STANCE_PRE_LEVEL,
    STANCE_RECOVERY,
    is_capacity_infrastructure,
    plan_stance_swaps,
    protects_from_sale,
    stance_score,
)
from dd4tester.hunt_candidates import ObjectSource, parse_area_file


def _item(
    vnum: int,
    name: str,
    *affects: tuple[int, int],
    wear_bit: int = 4,
) -> ObjectSource:
    return ObjectSource(
        vnum,
        name,
        f"a {name}",
        9,
        (2, 0, 0, 0),
        100,
        wear_flags=1 << wear_bit,
        affects=affects,
    )


def test_stances_prioritize_damroll_stats_and_recovery_resources() -> None:
    damage = _item(1, "damage helm", (19, 4), (18, 1))
    stats = _item(2, "training helm", (1, 2), (3, 2), (5, 1))
    recovery = _item(3, "recovery helm", (12, 20), (13, 15))

    assert stance_score(damage, STANCE_COMBAT) > stance_score(stats, STANCE_COMBAT)
    assert stance_score(stats, STANCE_PRE_LEVEL) > stance_score(
        damage, STANCE_PRE_LEVEL
    )
    assert stance_score(recovery, STANCE_RECOVERY) > stance_score(
        stats, STANCE_RECOVERY
    )


def test_pre_level_priorities_can_target_mage_practices_or_hitpoints() -> None:
    wisdom = _item(4, "wisdom helm", (3, 1))
    constitution = _item(5, "constitution helm", (5, 1))
    mage_priorities = (
        "intellectual_practices",
        "mana",
        "hitpoints",
    )
    hitpoint_priorities = (
        "hitpoints",
        "intellectual_practices",
        "mana",
    )

    assert stance_score(
        wisdom,
        STANCE_PRE_LEVEL,
        level_gain_priorities=mage_priorities,
    ) > stance_score(
        constitution,
        STANCE_PRE_LEVEL,
        level_gain_priorities=mage_priorities,
    )
    assert stance_score(
        constitution,
        STANCE_PRE_LEVEL,
        level_gain_priorities=hitpoint_priorities,
    ) > stance_score(
        wisdom,
        STANCE_PRE_LEVEL,
        level_gain_priorities=hitpoint_priorities,
    )


def test_stance_swap_removes_conflict_before_wearing_better_item() -> None:
    damage = _item(1, "damage helm", (19, 4))
    recovery = _item(2, "recovery helm", (12, 20), (13, 15))

    removals, additions = plan_stance_swaps(
        [recovery],
        [damage],
        STANCE_RECOVERY,
    )

    assert removals == [damage]
    assert additions == [recovery]


def test_capacity_items_are_protected_infrastructure() -> None:
    backpack = ObjectSource(
        31236,
        "backpack leather",
        "a leather backpack",
        15,
        (100, 1, 0, 0),
        0,
        wear_flags=1 | 8,
    )

    assert is_capacity_infrastructure(backpack)
    assert protects_from_sale(backpack)


def test_school_source_parser_retains_stat_affects_and_wear_flags() -> None:
    school = parse_area_file(
        Path("runs/dd4-source/server/area/school.are"),
        include_resets=False,
        include_entities=False,
        include_objects=True,
    )

    diploma = school.objects[3715]
    stone = school.objects[3721]
    assert diploma.affects == ((5, 1), (4, 1))
    assert diploma.wear_flags & (1 << 14)
    assert stone.affects == ((4, 2),)
    assert stone.wear_flags & (1 << 15)


def test_catalog_matches_unidentified_inventory_prefix() -> None:
    diploma = _item(3715, "Mud School diploma", (3, 1))
    catalog = GearCatalog({diploma.vnum: diploma})

    assert catalog.match("\x1b[38;5;39m[-?-]\x1b[0m a Mud School diploma") == diploma


def test_catalog_matches_set_prefix_and_protects_foundry_circlet() -> None:
    foundry = parse_area_file(
        Path("runs/dd4-source/server/area/foundry.are"),
        include_resets=False,
        include_entities=False,
        include_objects=True,
    )
    circlet = foundry.objects[108]
    catalog = GearCatalog({circlet.vnum: circlet})

    assert catalog.match("[SET] a silver circlet") == circlet
    assert circlet.affects == ((3, 1),)
    assert protects_from_sale(circlet)
