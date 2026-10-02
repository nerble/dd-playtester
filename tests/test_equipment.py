from pathlib import Path

import pytest

from dd4tester.equipment import (
    GearCatalog,
    ITEM_KEY,
    STANCE_COMBAT,
    STANCE_PRE_LEVEL,
    STANCE_RECOVERY,
    character_can_use_item,
    generated_weapon_damage_floor,
    is_blunt_weapon,
    item_category,
    item_command_keyword,
    item_keyword,
    is_releasable_funding_item,
    is_bow,
    is_capacity_infrastructure,
    is_digging_tool,
    is_digging_weapon,
    is_equipment_object,
    is_piercing_weapon,
    normalize_item_name,
    plan_stance_swaps,
    protects_from_sale,
    rank_executable_carrier_gear_sources,
    rank_executable_ground_gear_sources,
    rank_gear_sources,
    stance_score,
    weapon_combat_score,
    weapon_damage_score,
    weapon_preference_for_character,
)
from dd4tester.hunt_candidates import (
    ACT_AGGRESSIVE,
    ACT_SENTINEL,
    ExitSource,
    MobileSource,
    MobReset,
    ObjectSetBonus,
    ObjectSetSource,
    ObjectSource,
    RoomObjectReset,
    RoomSource,
    WEAR_WIELD,
    WorldSource,
    parse_area_file,
)


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


def test_poisoned_source_loot_is_not_treated_as_sale_funding() -> None:
    poisoned_ring = ObjectSource(
        4000,
        "ring yellow green",
        "a yellow and green ring",
        9,
        (0, 0, 16387, 0),
        50,
        extra_flags=1 << 14,
    )

    assert is_releasable_funding_item(poisoned_ring) is False


def test_rank_gear_sources_ranks_a_source_equipped_upgrade() -> None:
    current = ObjectSource(
        40,
        "small dagger",
        "a small dagger",
        5,
        (0, 1, 1, 2),
        10,
        wear_flags=1 << 13,
    )
    upgrade = ObjectSource(
        50,
        "needle dagger",
        "a needle dagger",
        5,
        (0, 3, 4, 2),
        100,
        wear_flags=1 << 13,
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "guard",
                "a quiet guard",
                5,
                ACT_SENTINEL,
                0,
                "test.are",
            )
        },
        objects={upgrade.vnum: upgrade},
        rooms={
            3001: RoomSource(
                3001,
                "recall",
                "test.are",
                exits={"south": ExitSource("south", 200, 0, -1)},
            ),
            200: RoomSource(200, "guard post", "test.are"),
        },
        mob_resets=[
            MobReset(100, 200, 1, (), equipment=((WEAR_WIELD, upgrade.vnum),)),
        ],
    )

    placements = rank_gear_sources(
        world,
        character_level=5,
        character_class="thief",
        current_items=(current,),
        include_all_areas=True,
    )

    assert len(placements) == 1
    placement = placements[0]
    assert placement.object_vnum == upgrade.vnum
    assert placement.object_keywords == "needle dagger"
    assert placement.category == "wield"
    assert placement.better_than_current is True
    assert placement.source_kind == "mob-equipped"
    assert placement.status == "caution"
    assert any(
        hazard.startswith("target equips a needle dagger")
        for hazard in placement.hazards
    )
    assert placement.route == ("south",)


@pytest.mark.parametrize("wear_bit", [1, 2, 12])
@pytest.mark.parametrize(
    ("owned_bonuses", "upgrade_bonus", "expected"),
    [
        ((3, 1), 2, True),
        ((3,), 2, True),
        ((3, 2, 1), 2, False),
        ((3, 3), 3, False),
        ((3, 1), 1, False),
    ],
)
def test_gear_acquisition_compares_the_replaceable_paired_slot(
    wear_bit: int,
    owned_bonuses: tuple[int, ...],
    upgrade_bonus: int,
    expected: bool,
) -> None:
    owned = tuple(
        _item(40 + bonus, f"paired gear {bonus}", (19, bonus), wear_bit=wear_bit)
        for bonus in owned_bonuses
    )
    upgrade = _item(50, "upgrade", (19, upgrade_bonus), wear_bit=wear_bit)
    world = WorldSource(
        objects={upgrade.vnum: upgrade},
        rooms={3001: RoomSource(3001, "recall", "test.are")},
        room_object_resets=[RoomObjectReset(upgrade.vnum, 3001)],
    )

    placements = rank_gear_sources(
        world,
        character_level=24,
        character_class="thief",
        current_items=owned,
        include_all_areas=True,
    )

    assert len(placements) == 1
    assert placements[0].better_than_current is expected


def test_rank_gear_sources_keeps_thief_primary_weapon_piercing() -> None:
    current = ObjectSource(
        40,
        "long slim dagger",
        "a long slim dagger",
        5,
        (0, 2, 5, 11),
        10,
        wear_flags=1 << 13,
    )
    sword = ObjectSource(
        41,
        "broad sword",
        "a broad sword",
        5,
        (0, 9, 20, 3),
        10,
        wear_flags=1 << 13,
    )
    dagger = ObjectSource(
        42,
        "needle dagger",
        "a needle dagger",
        5,
        (0, 3, 4, 11),
        10,
        wear_flags=1 << 13,
    )
    world = WorldSource(
        objects={sword.vnum: sword, dagger.vnum: dagger},
        rooms={
            3001: RoomSource(3001, "recall", "test.are"),
            200: RoomSource(200, "weapon room", "test.are"),
        },
        room_object_resets=[
            RoomObjectReset(sword.vnum, 200),
            RoomObjectReset(dagger.vnum, 200),
        ],
    )

    placements = rank_gear_sources(
        world,
        character_level=5,
        character_class="thief",
        current_items=(current,),
        include_all_areas=True,
    )

    by_vnum = {placement.object_vnum: placement for placement in placements}
    assert weapon_preference_for_character("thief") == "piercing"
    assert by_vnum[sword.vnum].weapon_role == "mismatch"
    assert by_vnum[sword.vnum].better_than_current is False
    assert by_vnum[dagger.vnum].weapon_role == "preferred"


def test_rank_gear_sources_audits_direct_ground_route() -> None:
    current = _item(40, "small dagger", wear_bit=13)
    upgrade = _item(50, "needle dagger", wear_bit=13)
    world = WorldSource(
        objects={upgrade.vnum: upgrade},
        rooms={
            3001: RoomSource(
                3001,
                "recall",
                "test.are",
                exits={"south": ExitSource("south", 200, 0, -1)},
            ),
            200: RoomSource(200, "equipment room", "test.are"),
        },
        room_object_resets=[RoomObjectReset(upgrade.vnum, 200)],
    )

    placements = rank_gear_sources(
        world,
        character_level=5,
        character_class="thief",
        current_items=(current,),
        include_all_areas=True,
    )

    assert len(placements) == 1
    placement = placements[0]
    assert placement.status == "promising"
    assert placement.route == ("south",)
    assert placement.route_vnums == ("3001", "200")
    assert placement.autonomy_rejections == ()


def test_rank_executable_ground_gear_sources_keeps_only_safe_current_upgrades() -> None:
    current = ObjectSource(
        40,
        "small dagger",
        "a small dagger",
        5,
        (0, 1, 1, 2),
        10,
        wear_flags=1 << 13,
    )
    upgrade = ObjectSource(
        50,
        "needle dagger",
        "a needle dagger",
        5,
        (0, 3, 4, 2),
        100,
        wear_flags=1 << 13,
        weight=1,
    )
    cursed = ObjectSource(
        51,
        "cursed dagger",
        "a cursed dagger",
        5,
        (0, 9, 20, 2),
        100,
        wear_flags=1 << 13,
        extra_flags=1 << 61,
    )
    world = WorldSource(
        objects={upgrade.vnum: upgrade, cursed.vnum: cursed},
        rooms={
            3001: RoomSource(
                3001,
                "recall",
                "test.are",
                exits={"south": ExitSource("south", 200, 0, -1)},
            ),
            200: RoomSource(200, "equipment room", "test.are"),
        },
        room_object_resets=[
            RoomObjectReset(upgrade.vnum, 200),
            RoomObjectReset(cursed.vnum, 200),
        ],
    )

    placements = rank_executable_ground_gear_sources(
        world,
        character_level=5,
        character_class="warrior",
        current_items=(current,),
        include_all_areas=True,
    )

    assert [placement.object_vnum for placement in placements] == [upgrade.vnum]
    assert placements[0].route == ("south",)


def test_rank_executable_carrier_gear_sources_keeps_exact_safe_carriers() -> None:
    current = _item(40, "small dagger", wear_bit=13)
    upgrade = ObjectSource(
        50,
        "needle dagger",
        "a needle dagger",
        5,
        (0, 3, 4, 2),
        100,
        wear_flags=1 << 13,
        weight=1,
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "guard",
                "a quiet guard",
                5,
                ACT_SENTINEL,
                0,
                "test.are",
            )
        },
        objects={upgrade.vnum: upgrade},
        rooms={
            3001: RoomSource(
                3001,
                "recall",
                "test.are",
                exits={"south": ExitSource("south", 200, 0, -1)},
            ),
            200: RoomSource(200, "guard post", "test.are"),
        },
        mob_resets=[
            MobReset(100, 200, 1, (), equipment=((WEAR_WIELD, upgrade.vnum),)),
        ],
    )

    placements = rank_executable_carrier_gear_sources(
        world,
        character_level=5,
        character_class="warrior",
        current_items=(current,),
        include_all_areas=True,
    )

    assert [placement.object_vnum for placement in placements] == [upgrade.vnum]
    assert placements[0].source_mobile_vnum == 100
    assert placements[0].route == ("south",)


def test_rank_gear_sources_rejects_hazardous_direct_ground_route() -> None:
    current = _item(40, "small dagger", wear_bit=13)
    upgrade = _item(50, "needle dagger", wear_bit=13)
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "aggressor",
                "a hostile guard",
                5,
                ACT_AGGRESSIVE,
                0,
                "test.are",
            )
        },
        objects={upgrade.vnum: upgrade},
        rooms={
            3001: RoomSource(
                3001,
                "recall",
                "test.are",
                exits={"south": ExitSource("south", 200, 0, -1)},
            ),
            200: RoomSource(200, "equipment room", "test.are"),
        },
        mob_resets=[MobReset(100, 200, 1, ())],
        room_object_resets=[RoomObjectReset(upgrade.vnum, 200)],
    )

    placements = rank_gear_sources(
        world,
        character_level=5,
        character_class="thief",
        current_items=(current,),
        include_all_areas=True,
    )

    assert len(placements) == 1
    placement = placements[0]
    assert placement.status == "reject"
    assert "stash room has an aggressive reset" in placement.autonomy_rejections


def test_consumables_marked_holdable_are_not_equipment_objects() -> None:
    potion = ObjectSource(
        1,
        "dark red potion",
        "a dark red potion",
        10,
        (9,),
        450,
        wear_flags=1 | (1 << 14),
    )
    water_skin = ObjectSource(
        2,
        "water skin",
        "a water skin",
        17,
        (25, 25, 0, 0),
        30,
        wear_flags=1 | (1 << 14),
    )
    sword = _item(3, "long sword", wear_bit=13)

    assert is_equipment_object(potion) is False
    assert is_equipment_object(water_skin) is False
    assert is_equipment_object(sword) is True


def test_keys_are_not_added_to_or_retained_by_stance_gear() -> None:
    key = ObjectSource(
        4402,
        "key hairy",
        "a hairy key",
        ITEM_KEY,
        (4422, 0, 0, 0),
        1,
        wear_flags=1 | (1 << 14),
    )

    removals, additions = plan_stance_swaps([key], [], STANCE_COMBAT)
    assert removals == []
    assert additions == []

    removals, additions = plan_stance_swaps([], [key], STANCE_COMBAT)
    assert removals == [key]
    assert additions == []


def test_item_normalization_discards_ephemeral_targetmode_selector() -> None:
    assert normalize_item_name("[#24943] a strange amulet") == "strange amulet"


def test_catalog_matches_some_prefixed_multisentence_room_object() -> None:
    gyvel = ObjectSource(
        301,
        "herbs herb gyvel",
        "a small dusk of black gyvel",
        19,
        (1, 0, 0, 0),
        25,
        room_description=(
            "Some black gyvel is lying here. It is dark green with black leaves "
            "and tiny blood-red flowers."
        ),
    )
    catalog = GearCatalog({gyvel.vnum: gyvel})

    assert catalog.match("Some black gyvel") == gyvel
    assert catalog.match("black gyvel") == gyvel


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
    assert item_category(bow) == "ranged_weapon"
    assert not is_bow(ordinary_weapon)


def test_digging_capabilities_mirror_source_item_and_weapon_types() -> None:
    shovel = ObjectSource(
        3604,
        "shovel",
        "a shovel",
        6,
        (25, 16, 39, 83),
        30,
    )
    scoop_weapon = ObjectSource(
        1,
        "scoop",
        "a scoop",
        5,
        (0, 2, 4, 5),
        100,
    )
    sword = ObjectSource(
        2,
        "sword",
        "a sword",
        5,
        (0, 2, 4, 1),
        100,
    )

    assert is_digging_tool(shovel)
    assert not is_digging_weapon(shovel)
    assert is_digging_weapon(scoop_weapon)
    assert not is_digging_weapon(sword)


def test_stance_planner_keeps_primary_weapon_with_ranged_bow() -> None:
    bow = ObjectSource(
        1,
        "bow",
        "a short bow",
        5,
        (0, 2, 4, 4),
        100,
        wear_flags=1 | (1 << 13),
        extra_flags=1 << 30,
    )
    dagger = ObjectSource(
        2,
        "dagger",
        "a dagger",
        5,
        (0, 2, 4, 11),
        100,
        wear_flags=1 | (1 << 13),
    )

    removals, additions = plan_stance_swaps(
        [],
        [dagger, bow],
        STANCE_RECOVERY,
    )

    assert dagger not in removals
    assert bow not in removals
    assert additions == []


def test_weapon_type_detection_matches_dd4_stun_and_backstab_checks() -> None:
    pounding_weapon = ObjectSource(
        4,
        "mace",
        "a mace",
        5,
        (0, 2, 5, 7),
        100,
        wear_flags=1 | (1 << 13),
    )
    piercing_weapon = ObjectSource(
        5,
        "dagger",
        "a dagger",
        5,
        (0, 2, 5, 11),
        100,
        wear_flags=1 | (1 << 13),
    )

    assert is_blunt_weapon(pounding_weapon)
    assert not is_blunt_weapon(piercing_weapon)
    assert is_piercing_weapon(piercing_weapon)
    assert not is_piercing_weapon(pounding_weapon)


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


def test_source_bear_claws_are_not_a_body_part() -> None:
    catalog = GearCatalog.from_area_directory(Path("runs/dd4-source/server/area"))
    claws = catalog.match("pair of bears claws")

    assert claws is not None
    assert claws.extra_flags & (1 << 26) == 0
    assert character_can_use_item(
        claws,
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


def test_combat_stance_orders_damage_hit_swiftness_then_critical() -> None:
    damage = _item(20, "damage helm", (19, 1))
    hit = _item(21, "hit helm", (18, 1))
    swift = _item(22, "swift helm", (51, 1))
    critical = _item(23, "critical helm", (50, 1))

    ranked = sorted(
        (critical, swift, hit, damage),
        key=lambda item: stance_score(item, STANCE_COMBAT),
        reverse=True,
    )

    assert ranked == [damage, hit, swift, critical]


def test_recovery_stance_uses_class_resource_priority() -> None:
    hitpoints = _item(24, "hitpoint helm", (13, 10))
    mana = _item(25, "mana helm", (12, 10))
    caster_priorities = ("intellectual_practices", "mana", "hitpoints")
    martial_priorities = ("physical_practices", "hitpoints", "mana")

    assert stance_score(
        mana,
        STANCE_RECOVERY,
        level_gain_priorities=caster_priorities,
    ) > stance_score(
        hitpoints,
        STANCE_RECOVERY,
        level_gain_priorities=caster_priorities,
    )
    assert stance_score(
        hitpoints,
        STANCE_RECOVERY,
        level_gain_priorities=martial_priorities,
    ) > stance_score(
        mana,
        STANCE_RECOVERY,
        level_gain_priorities=martial_priorities,
    )


def test_swiftness_and_critical_gear_are_protected_from_sale() -> None:
    assert protects_from_sale(_item(26, "swift helm", (51, 1)))
    assert protects_from_sale(_item(27, "critical helm", (50, 1)))


@pytest.mark.parametrize(
    ("level", "expected"),
    [(0, (1, 4)), (4, (1, 7)), (8, (2, 10)), (9, (2, 10)),
     (24, (6, 22)), (100, (25, 79)), (-1, None), (101, None), (True, None)],
)
def test_generated_weapon_damage_uses_two_fuzzy_minima(
    level: int, expected: tuple[int, int] | None,
) -> None:
    assert generated_weapon_damage_floor(level) == expected


def test_weapon_damage_score_uses_load_level_not_prototype_dice() -> None:
    dagger = ObjectSource(3020, "dagger", "a dagger", 5, (0, 2, 4, 11), 10, level=5)
    claws = ObjectSource(
        18000,
        "claws bears",
        "a pair of bears claws",
        5,
        (0, 6, 12, 11),
        0,
        level=15,
    )

    assert weapon_damage_score(dagger) == 8
    assert weapon_damage_score(claws) == 18
    assert weapon_damage_score(claws) > weapon_damage_score(dagger)


def test_prototype_damage_cannot_invent_a_source_weapon_upgrade() -> None:
    dagger = ObjectSource(3020, "dagger", "a dagger", 5, (0, 2, 4, 11), 10, level=1)
    club = ObjectSource(
        1521, "club large", "a large club", 5, (0, 4, 3, 7), 20000,
        level=10000, load_level_min=1, load_level_max=7,
    )
    assert weapon_damage_score(club) == weapon_damage_score(dagger) == 5


def test_weapon_score_rejects_unknown_load_level_and_body_parts() -> None:
    unknown = ObjectSource(1, "weapon", "a weapon", 5, (0, 10, 30, 7), 0, level=10000)
    body_part = ObjectSource(
        2, "claw", "a claw", 5, (0, 10, 30, 7), 0,
        level=20, extra_flags=1 << 26,
    )
    assert weapon_damage_score(unknown) == 0
    assert weapon_damage_score(body_part) == 0


def test_combat_stance_compares_generated_weapon_damage_plus_damroll() -> None:
    small_damage_weapon = ObjectSource(
        5252,
        "long dagger slim",
        "a long slim dagger",
        5,
        (0, 2, 5, 11),
        100,
        affects=((19, 1),),
        level=9,
    )
    bear_claws = ObjectSource(
        18000,
        "claws bears",
        "a pair of bears claws",
        5,
        (0, 6, 12, 11),
        0,
        affects=((18, 3),),
        level=15,
    )

    assert stance_score(bear_claws, STANCE_COMBAT) > stance_score(
        small_damage_weapon,
        STANCE_COMBAT,
    )


def test_weapon_combat_score_prefers_damroll_bonus_over_small_damage_gap() -> None:
    jewel_dagger = ObjectSource(
        3701,
        "jewel-studded dagger",
        "a jewel-studded dagger",
        5,
        (0, 2, 3, 11),
        0,
        affects=((18, 5), (19, 5)),
        wear_flags=1 | (1 << 13),
        level=5,
    )
    long_dagger = ObjectSource(
        5252,
        "long dagger slim",
        "a long slim dagger",
        5,
        (0, 2, 5, 11),
        100,
        affects=((18, 1), (19, 1)),
        wear_flags=1 | (1 << 13),
        level=9,
    )

    assert weapon_combat_score(jewel_dagger) > weapon_combat_score(long_dagger)


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


def test_combat_stance_prefers_piercing_weapon_for_backstab() -> None:
    sword = ObjectSource(
        4002,
        "rusty sword",
        "a rusty sword",
        5,
        (0, 4, 8, 3),
        100,
        wear_flags=1 | (1 << 13),
    )
    dagger = ObjectSource(
        5252,
        "long dagger slim",
        "a long slim dagger",
        5,
        (0, 2, 5, 11),
        100,
        wear_flags=1 | (1 << 13),
    )

    removals, additions = plan_stance_swaps(
        [dagger],
        [sword],
        STANCE_COMBAT,
        weapon_preference="piercing",
    )

    assert removals == [sword]
    assert additions == [dagger]


def test_required_worn_weapon_survives_combat_stance_reconciliation() -> None:
    jewel = ObjectSource(
        3701,
        "jewel-studded dagger",
        "a jewel-studded dagger",
        5,
        (0, 2, 3, 11),
        0,
        wear_flags=1 | (1 << 13),
        affects=((18, 5), (19, 5)),
    )
    long_dagger = ObjectSource(
        5252,
        "long dagger slim",
        "a long slim dagger",
        5,
        (0, 2, 5, 11),
        100,
        wear_flags=1 | (1 << 13),
        affects=((18, 1), (19, 1)),
    )

    removals, additions = plan_stance_swaps(
        [jewel],
        [long_dagger],
        STANCE_COMBAT,
        weapon_preference="piercing",
        required_worn_items=[long_dagger],
    )

    assert removals == []
    assert additions == []


def test_recovery_stance_keeps_a_thief_piercing_primary() -> None:
    sword = ObjectSource(
        4002,
        "rusty sword",
        "a rusty sword",
        5,
        (0, 4, 8, 3),
        100,
        wear_flags=1 | (1 << 13),
    )
    dagger = ObjectSource(
        5252,
        "long dagger slim",
        "a long slim dagger",
        5,
        (0, 2, 5, 11),
        100,
        wear_flags=1 | (1 << 13),
    )

    removals, additions = plan_stance_swaps(
        [sword],
        [dagger],
        STANCE_RECOVERY,
        weapon_preference="piercing",
    )

    assert removals == []
    assert additions == []


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


def test_empty_finger_slot_does_not_make_strength_penalty_ring_an_upgrade() -> None:
    penalty_ring = _item(
        4000,
        "yellow and green ring",
        (1, -2),
        (5, 1),
        wear_bit=1,
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "guard",
                "a quiet guard",
                5,
                ACT_SENTINEL,
                0,
                "test.are",
            )
        },
        objects={penalty_ring.vnum: penalty_ring},
        rooms={
            3001: RoomSource(
                3001,
                "recall",
                "test.are",
                exits={"south": ExitSource("south", 200, 0, -1)},
            ),
            200: RoomSource(200, "guard post", "test.are"),
        },
        mob_resets=[
            MobReset(
                100,
                200,
                1,
                (),
                equipment=((1, penalty_ring.vnum),),
            ),
        ],
    )

    placements = rank_gear_sources(
        world,
        character_level=11,
        character_class="thief",
        include_all_areas=True,
    )
    carrier = next(
        placement
        for placement in placements
        if placement.object_vnum == penalty_ring.vnum
    )

    assert carrier.better_than_current is False
    assert rank_executable_carrier_gear_sources(
        world,
        character_level=11,
        character_class="thief",
        include_all_areas=True,
    ) == []


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


def test_catalog_loads_object_set_thresholds_in_runtime_affect_order() -> None:
    catalog = GearCatalog.from_area_directory(
        Path("runs/dd4-source/server/area")
    )

    alliance = catalog.object_sets[2707]
    huntsmith = catalog.object_sets[2704]
    assert alliance.object_vnums == (108, 6601)
    assert alliance.bonuses == (ObjectSetBonus(2, 1, 2),)
    assert huntsmith.object_vnums == (2707, 2708, 2709)
    assert huntsmith.bonuses == (
        ObjectSetBonus(2, 19, 10),
        ObjectSetBonus(3, 51, 5),
    )


def test_combat_stance_preserves_live_strength_set_before_hitroll() -> None:
    catalog = GearCatalog.from_area_directory(
        Path("runs/dd4-source/server/area")
    )
    collar = catalog.objects[4538]
    circlet = catalog.objects[108]
    pink_ring = catalog.objects[6601]
    recovery_boots = catalog.objects[110]
    bead_necklace = catalog.objects[1509]
    combat_boots = catalog.objects[28372]

    removals, additions = plan_stance_swaps(
        [bead_necklace, combat_boots],
        [collar, circlet, pink_ring, pink_ring, recovery_boots],
        STANCE_COMBAT,
        object_sets=catalog.object_sets.values(),
        current_strength=17,
    )

    assert removals == [recovery_boots]
    assert additions == [combat_boots]


def test_combat_stance_without_set_data_retains_independent_scoring() -> None:
    catalog = GearCatalog.from_area_directory(
        Path("runs/dd4-source/server/area")
    )
    collar = catalog.objects[4538]
    circlet = catalog.objects[108]
    pink_ring = catalog.objects[6601]
    recovery_boots = catalog.objects[110]
    bead_necklace = catalog.objects[1509]
    combat_boots = catalog.objects[28372]

    removals, additions = plan_stance_swaps(
        [bead_necklace, combat_boots],
        [collar, circlet, pink_ring, pink_ring, recovery_boots],
        STANCE_COMBAT,
        current_strength=17,
    )

    assert removals == [circlet, recovery_boots]
    assert additions == [bead_necklace, combat_boots]


def test_duplicate_set_prototypes_do_not_activate_a_set_bonus() -> None:
    set_ring = _item(1, "set ring", wear_bit=1)
    damage_ring = _item(2, "damage ring", (19, 1), wear_bit=1)
    object_set = ObjectSetSource(
        10,
        "two distinct rings",
        "",
        (1, 3),
        (ObjectSetBonus(2, 19, 100),),
    )

    removals, additions = plan_stance_swaps(
        [damage_ring, damage_ring],
        [set_ring, set_ring],
        STANCE_COMBAT,
        object_sets=[object_set],
        current_strength=15,
    )

    assert removals == [set_ring, set_ring]
    assert additions == [damage_ring, damage_ring]


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


def test_item_command_keyword_disambiguates_shared_weapon_nouns() -> None:
    ordinary = ObjectSource(
        3020,
        "dagger",
        "a dagger",
        5,
        (0, 2, 4, 11),
        10,
        wear_flags=1 | (1 << 13),
    )
    long_dagger = ObjectSource(
        5252,
        "long dagger slim",
        "a long slim dagger",
        5,
        (0, 2, 5, 11),
        10,
        wear_flags=1 | (1 << 13),
    )

    assert item_command_keyword(long_dagger, [ordinary]) == "long"
    assert item_command_keyword(ordinary, [long_dagger]) == "dagger"
    assert (
        item_command_keyword(long_dagger, [ordinary], allow_ordinal=False)
        == "long"
    )


def test_item_command_keyword_uses_an_ordinal_for_ambiguous_carried_gear() -> None:
    patched = ObjectSource(
        9404,
        "jerkin leather patched",
        "a patched leather jerkin",
        9,
        (0, 0, 0, 0),
        5,
        wear_flags=1 | (1 << 3),
    )
    studded = ObjectSource(
        3066,
        "jerkin",
        "a studded leather jerkin",
        9,
        (0, 0, 0, 0),
        1,
        wear_flags=1 | (1 << 3),
    )

    assert item_command_keyword(studded, [patched, studded]) == "2.jerkin"
    assert (
        item_command_keyword(studded, [patched, studded], allow_ordinal=False)
        == "jerkin"
    )
