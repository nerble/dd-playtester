from pathlib import Path

from dd4tester.equipment import (
    GearCatalog,
    STANCE_COMBAT,
    STANCE_PRE_LEVEL,
    STANCE_RECOVERY,
    character_can_use_item,
    item_category,
    item_keyword,
    is_bow,
    is_capacity_infrastructure,
    is_piercing_weapon,
    plan_stance_swaps,
    protects_from_sale,
    stance_score,
    weapon_damage_score,
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


def test_bow_detection_uses_dd4_item_bow_extra_flag() -> None:
    bow = ObjectSource(
        1,
        "bow",
        "a short bow",
        5,
        (0, 2, 4, 4),
        100,
        wear_flags=1 | (1 << 17),
        extra_flags=1 << 30,
    )
    ordinary_weapon = ObjectSource(
        2,
        "sword",
        "a sword",
        5,
        (0, 2, 4, 1),
        100,
        wear_flags=1 | (1 << 13),
    )

    assert is_bow(bow)
    assert not is_bow(ordinary_weapon)


def test_body_part_weapons_are_never_usable_gear_candidates() -> None:
    body_part = ObjectSource(
        3,
        "claw",
        "a severed claw",
        5,
        (0, 6, 12, 11),
        0,
        wear_flags=1 | (1 << 13),
        extra_flags=1 << 26,
    )

    assert not character_can_use_item(
        body_part,
        character_class="thief",
        subclass="ninja",
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


def test_weapon_damage_score_uses_source_dice_average() -> None:
    dagger = ObjectSource(3020, "dagger", "a dagger", 5, (0, 2, 4, 11), 10)
    claws = ObjectSource(
        18000,
        "claws bears",
        "a pair of bears claws",
        5,
        (0, 6, 12, 11),
        0,
    )

    assert weapon_damage_score(dagger) == 10
    assert weapon_damage_score(claws) == 78
    assert weapon_damage_score(claws) > weapon_damage_score(dagger)


def test_catalog_matches_source_room_description_to_object() -> None:
    armor = ObjectSource(
        4530,
        "armor hard leather",
        "hard leather armor",
        9,
        (0, 0, 0, 0),
        45,
        room_description="A piece of leather armor is here.",
    )
    catalog = GearCatalog({armor.vnum: armor})

    assert catalog.match("piece of leather armor") == armor


def test_catalog_ignores_empty_source_names_in_equipment_audits() -> None:
    malformed = ObjectSource(
        19097,
        "fangs",
        "",
        8,
        (),
        0,
    )
    catalog = GearCatalog({malformed.vnum: malformed})
    equipment = """<worn around neck>  -
<worn on finger>    -
[weapon]            -
"""

    assert catalog.match_equipment_text(equipment) == []


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


def test_all_stances_remove_strength_penalty_rings_even_if_slot_is_empty() -> None:
    penalty_ring = _item(
        4000,
        "yellow and green ring",
        (1, -2),
        (5, 1),
        wear_bit=1,
    )

    for stance in (STANCE_COMBAT, STANCE_RECOVERY, STANCE_PRE_LEVEL):
        removals, additions = plan_stance_swaps([], [penalty_ring], stance)

        assert removals == [penalty_ring]
        assert additions == []


def test_recovery_stance_keeps_basic_light_with_level_gain_priorities() -> None:
    light = ObjectSource(
        3716,
        "banner illumination",
        "banner of illumination",
        1,
        (0, 0, -1, 0),
        10,
    )

    removals, additions = plan_stance_swaps(
        [],
        [light],
        STANCE_RECOVERY,
        level_gain_priorities=("intellectual_practices", "mana", "hitpoints"),
    )

    assert removals == []
    assert additions == []


def test_combat_stance_fills_empty_slot_with_basic_gear() -> None:
    pouch = _item(3370, "small leather pouch", wear_bit=16)

    removals, additions = plan_stance_swaps(
        [pouch],
        [],
        STANCE_COMBAT,
        level_gain_priorities=("intellectual_practices", "mana", "hitpoints"),
    )

    assert removals == []
    assert additions == [pouch]


def test_stance_leaves_core_stat_penalty_gear_unequipped() -> None:
    penalty_cap = _item(4001, "burdensome cap", (4, -1))

    removals, additions = plan_stance_swaps(
        [penalty_cap],
        [],
        STANCE_RECOVERY,
    )

    assert removals == []
    assert additions == []


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


def test_school_dagger_is_source_verified_for_backstab_but_sword_is_not() -> None:
    school = parse_area_file(
        Path("runs/dd4-source/server/area/school.are"),
        include_resets=False,
        include_entities=False,
        include_objects=True,
    )

    assert is_piercing_weapon(school.objects[3701])
    assert not is_piercing_weapon(school.objects[3702])


def test_ambush_source_parser_retains_lance_flag_and_class_restriction() -> None:
    ambush = parse_area_file(
        Path("runs/dd4-source/server/area/ambush.are"),
        include_resets=False,
        include_entities=False,
        include_objects=True,
    )

    spear = ambush.objects[4521]
    assert spear.extra_flags & (1 << 27)
    assert not character_can_use_item(
        spear,
        character_class="mage",
        subclass="warlock",
    )
    assert character_can_use_item(
        spear,
        character_class="warrior",
        subclass="knight",
    )


def test_ambiguous_description_is_not_wearable_if_any_prototype_is_restricted() -> None:
    ordinary = ObjectSource(
        1,
        "spear",
        "a wooden spear",
        5,
        (0, 6, 6, 0),
        100,
        wear_flags=1 << 13,
    )
    lance = ObjectSource(
        2,
        "wooden spear",
        "a wooden spear",
        5,
        (0, 2, 2, 0),
        55,
        wear_flags=1 << 13,
        extra_flags=1 << 27,
    )
    catalog = GearCatalog({ordinary.vnum: ordinary, lance.vnum: lance})

    assert catalog.match_many_usable(
        ["a wooden spear"],
        character_class="mage",
        subclass="warlock",
    ) == []
    assert catalog.match_many_usable(
        ["a wooden spear"],
        character_class="warrior",
        subclass="knight",
    ) == [ordinary]


def test_school_banner_uses_the_light_slot_and_is_restored_after_death() -> None:
    school = parse_area_file(
        Path("runs/dd4-source/server/area/school.are"),
        include_resets=False,
        include_entities=False,
        include_objects=True,
    )
    banner = school.objects[3716]

    removals, additions = plan_stance_swaps(
        [banner],
        [],
        STANCE_COMBAT,
    )

    assert item_category(banner) == "light"
    assert item_keyword(banner) == "illumination"
    assert protects_from_sale(banner)
    assert removals == []
    assert additions == [banner]


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


def test_item_keyword_uses_the_displayed_noun_instead_of_a_shared_adjective() -> None:
    circlet = ObjectSource(
        108,
        "silver circlet",
        "a silver circlet",
        9,
        (1, 0, 0, 0),
        26,
        wear_flags=1 | (1 << 4),
    )

    assert item_keyword(circlet) == "circlet"


def test_item_keyword_avoids_abbreviations_and_requires_a_source_keyword() -> None:
    iron_cap = _item(109, "iron cap")
    velvet_cape = _item(3711, "velvet cape", wear_bit=10)
    belt = ObjectSource(
        3712,
        "belt silver leather",
        "a black belt with a silver buckle",
        9,
        (2, 0, 0, 0),
        5,
        wear_flags=1 | (1 << 11),
    )

    assert item_keyword(iron_cap) == "iron"
    assert item_keyword(velvet_cape) == "velvet"
    assert item_keyword(belt) == "belt"
