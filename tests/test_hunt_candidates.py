from dataclasses import replace
from dataclasses import replace
from pathlib import Path

import pytest

from dd4tester.fastwalks import route_named
from dd4tester.hunt_candidates import (
    ACT_AGGRESSIVE,
    ACT_DIE_IF_MASTER_GONE,
    ACT_LOSE_FAME,
    ACT_SENTINEL,
    ACT_UNDEAD,
    AFF_CONFUSION,
    BODY_HUGE,
    BODY_INORGANIC,
    BODY_NO_HEAD,
    BODY_NO_ARMS,
    BODY_NO_EYES,
    PART_MANY_ARMS,
    ITEM_FOOD,
    ITEM_MONEY,
    ITEM_SCROLL,
    ITEM_STAFF,
    ITEM_WAND,
    ExitSource,
    MobileSource,
    MobileProgram,
    MobReset,
    ObjectSource,
    RoomSource,
    RoomObjectReset,
    SourceCombatOutput,
    WorldSource,
    money_value,
    castable_spell_names,
    potion_spell_names,
    resource_activation_for_object,
    rank_resource_sources,
    source_combat_readiness,
    source_combat_output_estimate,
    _route_preflight_metadata,
    _mobile_critical_hit_damage,
    _mobile_peak_round_damage,
    mobile_expected_round_damage,
    mobile_sanctuary_critical_hit_damage,
    mobile_sanctuary_peak_round_damage,
    load_object_sources,
    load_world_source,
    parse_area_file,
    rank_hunt_candidates,
    rank_coin_stashes,
    rank_food_stashes,
    _source_mobile_identity,
    source_mobile_identities,
    source_mobile_search_rooms,
    source_route_movement_cost,
    source_route_requires_flight,
    source_route_hazard_rejections,
    source_safe_route_to_room,
    source_safe_route_to_room_with_origin,
    source_class_teacher_route,
    source_class_teacher_skill,
    source_mobile_can_join_player_fight,
    source_subclass_teacher_route,
    source_subclass_teacher_skill,
    WEAR_HOLD,
)


FIXTURE = Path(__file__).parent / "fixtures" / "hunt_area.are"


def test_required_consumable_can_rank_a_carrier_without_saleable_loot() -> None:
    potion = ObjectSource(
        50,
        "black potion",
        "a black potion",
        10,
        (15, 0, 0, 0),
        100,
        value_strings=("15", "cure critical", "", ""),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "orc",
                "a large orc",
                5,
                1 << 1,
                0,
                "test.are",
            )
        },
        objects={50: potion},
        rooms={
            3001: RoomSource(
                3001,
                "recall",
                "test.are",
                exits={"south": ExitSource("south", 200, 0, -1)},
            ),
            200: RoomSource(200, "tunnel", "test.are"),
        },
        mob_resets=[MobReset(100, 200, 1, (50,))],
    )

    assert rank_hunt_candidates(
        world,
        character_level=10,
        include_below_band=True,
        include_all_areas=True,
    ) == []

    [candidate] = rank_hunt_candidates(
        world,
        character_level=10,
        include_below_band=True,
        include_all_areas=True,
        required_loot_object_vnums={50},
    )

    assert candidate.mobile_vnum == 100
    assert candidate.loot == ("a black potion",)


def test_required_consumable_can_rank_a_mob_equipped_carrier() -> None:
    potion = ObjectSource(
        50,
        "black potion",
        "a black potion",
        10,
        (15, 0, 0, 0),
        100,
        value_strings=("15", "cure critical", "", ""),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "orc",
                "a large orc",
                5,
                0,
                0,
                "test.are",
            )
        },
        objects={50: potion},
        rooms={
            3001: RoomSource(
                3001,
                "recall",
                "test.are",
                exits={"south": ExitSource("south", 200, 0, -1)},
            ),
            200: RoomSource(200, "tunnel", "test.are"),
        },
        mob_resets=[
            MobReset(100, 200, 1, (), equipment=((WEAR_HOLD, 50),))
        ],
    )

    [candidate] = rank_hunt_candidates(
        world,
        character_level=10,
        include_below_band=True,
        include_all_areas=True,
        required_loot_object_vnums={50},
    )

    assert candidate.mobile_vnum == 100
    assert candidate.loot == ("a black potion",)


def test_resource_source_report_keeps_carrier_and_ground_paths_distinct() -> None:
    sanctuary = ObjectSource(
        50,
        "potion purple",
        "a purple potion",
        10,
        (17,),
        500,
        value_strings=("17", "cure blindness", "sanctuary", ""),
    )
    bread = ObjectSource(
        51,
        "bread",
        "a loaf of bread",
        ITEM_FOOD,
        (5, 0, 0, 0),
        2,
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "guardian",
                "a quiet guardian",
                5,
                ACT_SENTINEL,
                0,
                "test.are",
            )
        },
        objects={50: sanctuary, 51: bread},
        rooms={
            3001: RoomSource(
                3001,
                "recall",
                "test.are",
                exits={"south": ExitSource("south", 3002, 0, -1)},
            ),
            3002: RoomSource(
                3002,
                "resource room",
                "test.are",
                exits={"north": ExitSource("north", 3001, 0, -1)},
            ),
        },
        mob_resets=[MobReset(100, 3002, 1, (50,))],
        room_object_resets=[RoomObjectReset(51, 3002, 1)],
    )

    placements = rank_resource_sources(
        world,
        character_level=5,
        effect="all",
        include_all_areas=True,
    )

    assert {
        (placement.effect, placement.object_vnum, placement.source_kind)
        for placement in placements
    } == {
        ("sanctuary", 50, "mob-carried"),
        ("healing", 50, "mob-carried"),
        ("food", 51, "ground-reset"),
    }
    carried = next(placement for placement in placements if placement.object_vnum == 50)
    ground = next(placement for placement in placements if placement.object_vnum == 51)
    assert carried.room_vnum == ground.room_vnum == 3002
    assert carried.route == ground.route == ("south",)
    assert carried.source_mobile_vnum == 100
    assert carried.activation is not None
    assert carried.activation.mode == "potion"
    assert carried.activation.command == "quaff"
    assert ground.source_mobile_vnum is None


def test_resource_source_report_includes_mob_equipped_resources() -> None:
    sanctuary = ObjectSource(
        50,
        "flask holy water",
        "a flask of holy water",
        10,
        (17,),
        500,
        value_strings=("17", "sanctuary", "", ""),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "templar",
                "a grand templar",
                5,
                ACT_SENTINEL,
                0,
                "test.are",
            )
        },
        objects={50: sanctuary},
        rooms={
            3001: RoomSource(
                3001,
                "recall",
                "test.are",
                exits={"south": ExitSource("south", 3002, 0, -1)},
            ),
            3002: RoomSource(3002, "resource room", "test.are"),
        },
        mob_resets=[
            MobReset(100, 3002, 1, (), equipment=((WEAR_HOLD, 50),))
        ],
    )

    placements = rank_resource_sources(
        world,
        character_level=5,
        effect="sanctuary",
        include_all_areas=True,
    )

    assert len(placements) == 1
    assert placements[0].source_kind == "mob-equipped"
    assert placements[0].object_vnum == 50
    assert placements[0].source_mobile_vnum == 100


def test_resource_source_report_orders_live_risk_statuses() -> None:
    safe_potion = ObjectSource(
        50,
        "potion purple",
        "a purple potion",
        10,
        (17,),
        500,
        value_strings=("17", "sanctuary", "", ""),
    )
    dangerous_potion = ObjectSource(
        51,
        "potion red",
        "a red potion",
        10,
        (17,),
        500,
        value_strings=("17", "sanctuary", "", ""),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "guardian",
                "a quiet guardian",
                5,
                ACT_SENTINEL,
                0,
                "test.are",
            ),
            101: MobileSource(
                101,
                "aggressor",
                "a poisoned guardian",
                5,
                ACT_SENTINEL | ACT_LOSE_FAME,
                0,
                "test.are",
            ),
        },
        objects={50: safe_potion, 51: dangerous_potion},
        rooms={
            3001: RoomSource(
                3001,
                "recall",
                "test.are",
                exits={
                    "south": ExitSource("south", 3002, 0, -1),
                    "east": ExitSource("east", 3003, 0, -1),
                },
            ),
            3002: RoomSource(
                3002,
                "resource room",
                "test.are",
                exits={"north": ExitSource("north", 3001, 0, -1)},
            ),
            3003: RoomSource(
                3003,
                "dangerous resource room",
                "test.are",
                exits={"west": ExitSource("west", 3001, 0, -1)},
            ),
        },
        mob_resets=[
            MobReset(100, 3002, 1, (50,)),
            MobReset(101, 3003, 1, (51,)),
        ],
        mobile_specials={101: ("spec_poison",)},
    )

    placements = rank_resource_sources(
        world,
        character_level=5,
        effect="sanctuary",
        include_all_areas=True,
    )

    assert [(placement.object_vnum, placement.status) for placement in placements] == [
        (50, "promising"),
        (51, "reject"),
    ]


def test_ranker_uses_a_live_observed_remote_recall_origin() -> None:
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "target",
                "a remote target",
                5,
                ACT_SENTINEL,
                0,
                "remote.are",
            )
        },
        rooms={
            3001: RoomSource(3001, "Default recall", "midgaard.are"),
            28003: RoomSource(
                28003,
                "Draagdim recall",
                "remote.are",
                exits={"east": ExitSource("east", 28004, 0, -1)},
            ),
            28004: RoomSource(28004, "Remote hunting ground", "remote.are"),
        },
        mob_resets=[MobReset(100, 28004, 1, ())],
    )

    assert rank_hunt_candidates(
        world,
        character_level=5,
        include_xp_only=True,
        include_all_areas=True,
    ) == []

    [candidate] = rank_hunt_candidates(
        world,
        character_level=5,
        include_xp_only=True,
        include_all_areas=True,
        recall_origins={2: 28003},
    )

    assert candidate.route == ("east",)
    assert candidate.route_origin_recall_index == 2
    assert candidate.route_origin_room_vnum == 28003


def test_source_safe_quest_route_uses_a_live_observed_remote_recall_origin() -> None:
    world = WorldSource(
        rooms={
            3001: RoomSource(3001, "Default recall", "midgaard.are"),
            28003: RoomSource(
                28003,
                "Draagdim recall",
                "remote.are",
                exits={"east": ExitSource("east", 28004, 0, -1)},
            ),
            28004: RoomSource(28004, "Remote quest room", "remote.are"),
        },
    )

    assert source_safe_route_to_room(
        world,
        28004,
        character_level=25,
    ) is None

    selected = source_safe_route_to_room_with_origin(
        world,
        28004,
        character_level=25,
        recall_origins={2: 28003},
    )

    assert selected == (("east",), (28003, 28004), 0, 2, 28003)


def test_strict_source_route_rejects_reachable_moria_combat_hazards() -> None:
    world = load_world_source(
        Path("runs/dd4-source/server/area"),
        include_all_areas=True,
    )
    path = (
        4064,
        4020,
        4027,
        4026,
        4019,
        4015,
        4014,
        4013,
        4012,
        4016,
        4023,
        4022,
        4021,
        4115,
        4114,
        4109,
        4106,
        4103,
        4104,
        4152,
    )

    warrior = world.mobiles[4106]
    assert warrior.aggressive is True
    assert warrior.wanders is True
    hazards = source_route_hazard_rejections(
        world,
        path,
        character_level=19,
        require_no_combat_hazards=True,
    )

    assert any("the Warrior" in hazard for hazard in hazards)
    assert source_safe_route_to_room_with_origin(
        world,
        4152,
        character_level=19,
        require_no_combat_hazards=True,
    ) is None


def test_real_source_route_rejects_a_reachable_transit_hazard_special() -> None:
    world = load_world_source(
        Path("runs/dd4-source/server/area"),
        include_all_areas=True,
    )

    [candidate] = [
        candidate
        for candidate in rank_hunt_candidates(
            world,
            character_level=20,
            include_xp_only=True,
            include_all_areas=True,
        )
        if candidate.mobile_vnum == 18506
    ]

    assert not candidate.autonomous_safe
    assert "a non-safe special mobile can reach the route" in (
        candidate.autonomy_rejections
    )
    assert any("Fewmaster Toede" in hazard for hazard in candidate.hazards)
    assert any("rock crab" in hazard for hazard in candidate.hazards)


@pytest.mark.parametrize(
    "special",
    ("spec_cast_mage", "spec_executioner", "spec_guard"),
)
def test_source_noninitiating_special_allows_fixed_transit(
    monkeypatch,
    special: str,
) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "target",
                "the target",
                15,
                0,
                0,
                "target.are",
            ),
            200: MobileSource(
                200,
                "bystander",
                "the source bystander",
                30,
                ACT_SENTINEL,
                0,
                "target.are",
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Transit", "target.are"),
            7002: RoomSource(7002, "Target", "target.are"),
        },
        mob_resets=[
            MobReset(200, 7001, 1, ()),
            MobReset(100, 7002, 1, ()),
        ],
        mobile_specials={200: (special,)},
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)
    world.rooms[7001].exits["north"] = ExitSource("north", 7002, 0, -1)

    [candidate] = rank_hunt_candidates(
        world,
        character_level=20,
        include_xp_only=True,
    )

    assert candidate.autonomous_safe
    assert not any(
        "non-safe special mobile" in rejection
        for rejection in candidate.autonomy_rejections
    )


def test_source_assassin_special_remains_a_fixed_transit_hazard(monkeypatch) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(100, "target", "the target", 15, 0, 0, "target.are"),
            200: MobileSource(
                200,
                "assassin",
                "the source assassin",
                8,
                ACT_SENTINEL,
                0,
                "target.are",
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Transit", "target.are"),
            7002: RoomSource(7002, "Target", "target.are"),
        },
        mob_resets=[
            MobReset(200, 7001, 1, ()),
            MobReset(100, 7002, 1, ()),
        ],
        mobile_specials={200: ("spec_assassin",)},
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)
    world.rooms[7001].exits["north"] = ExitSource("north", 7002, 0, -1)

    [candidate] = rank_hunt_candidates(
        world,
        character_level=20,
        include_xp_only=True,
    )

    assert not candidate.autonomous_safe
    assert "route crosses a non-safe special mobile" in (
        candidate.autonomy_rejections
    )


def test_aggressive_gas_breath_special_remains_a_transit_hazard(monkeypatch) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(100, "target", "the target", 15, 0, 0, "target.are"),
            200: MobileSource(
                200,
                "rock crab",
                "the aggressive rock crab",
                8,
                ACT_AGGRESSIVE | ACT_SENTINEL,
                0,
                "target.are",
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Transit", "target.are"),
            7002: RoomSource(7002, "Target", "target.are"),
        },
        mob_resets=[
            MobReset(200, 7001, 1, ()),
            MobReset(100, 7002, 1, ()),
        ],
        mobile_specials={200: ("spec_breath_gas",)},
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)
    world.rooms[7001].exits["north"] = ExitSource("north", 7002, 0, -1)

    [candidate] = rank_hunt_candidates(
        world,
        character_level=20,
        include_xp_only=True,
    )

    assert not candidate.autonomous_safe
    assert "route crosses a non-safe special mobile" in (
        candidate.autonomy_rejections
    )


def test_source_route_movement_cost_follows_core_terrain_and_flight_rules() -> None:
    world = WorldSource(
        rooms={
            1: RoomSource(1, "inside", "test.are", sector_type=0),
            2: RoomSource(2, "forest", "test.are", sector_type=3),
            3: RoomSource(3, "swamp", "test.are", sector_type=9),
        }
    )

    assert source_route_movement_cost(world, (1, 2, 3)) == 17
    assert source_route_movement_cost(world, (1, 2, 3), flying=True) == 5


def test_source_route_requires_flight_uses_destination_sector_not_direction() -> None:
    world = WorldSource(
        rooms={
            1: RoomSource(
                1,
                "origin",
                "test.are",
                exits={"north": ExitSource("north", 2, 0, -1)},
            ),
            2: RoomSource(2, "air room", "test.are", sector_type=9),
        }
    )

    assert source_route_requires_flight(world, (1, 2)) is True


def test_source_route_requires_flight_detects_water_capability_gate() -> None:
    world = WorldSource(
        rooms={
            1: RoomSource(
                1,
                "shore",
                "test.are",
                exits={"east": ExitSource("east", 2, 0, -1)},
            ),
            2: RoomSource(2, "swimming water", "test.are", sector_type=6),
        }
    )

    assert source_route_requires_flight(world, (1, 2)) is True


def test_source_route_requires_flight_detects_ex_wall_exit() -> None:
    world = WorldSource(
        rooms={
            1: RoomSource(
                1,
                "origin",
                "test.are",
                exits={"east": ExitSource("east", 2, 128, -1)},
            ),
            2: RoomSource(2, "walled room", "test.are"),
        }
    )

    assert source_route_requires_flight(world, (1, 2)) is True


def test_candidate_uses_least_ambiguous_source_keyword() -> None:
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "druid Aruncus",
                "Aruncus the Druid",
                3,
                1 << 1,
                0,
                "ambush.are",
            ),
            101: MobileSource(
                101,
                "druid hedge",
                "a hedge druid",
                3,
                1 << 1,
                0,
                "ambush.are",
            ),
        },
        rooms={
            3001: RoomSource(
                3001,
                "Recall",
                "ambush.are",
                exits={"east": ExitSource("east", 3002, 0, -1)},
            ),
            3002: RoomSource(3002, "Field", "ambush.are"),
        },
        mob_resets=[MobReset(100, 3002, 1, ())],
    )

    candidates = rank_hunt_candidates(
        world,
        character_level=5,
        include_xp_only=True,
    )

    assert candidates[0].target_keyword == "aruncus"


def test_source_identity_distinguishes_same_short_name_mobile_prototypes() -> None:
    area_directory = Path("runs/dd4-source/server/area")
    world = load_world_source(area_directory, include_all_areas=True)

    male = world.mobiles[1710]
    female = world.mobiles[1711]
    assert _source_mobile_identity(
        male.room_description,
        male.short_description,
        male.keywords,
    ) == "male centaur"
    assert _source_mobile_identity(
        female.room_description,
        female.short_description,
        female.keywords,
    ) == "female centaur"

    candidates = rank_hunt_candidates(
        world,
        character_level=19,
        include_below_band=True,
        include_all_areas=True,
    )
    male_candidate = next(
        candidate
        for candidate in candidates
        if candidate.mobile_vnum == 1710 and candidate.room_vnum == 1704
    )
    assert male_candidate.target == "a centaur"
    assert male_candidate.target_identity == "male centaur"


def test_ranked_identity_matches_source_room_line_for_composite_keyword_mobile() -> None:
    world = load_world_source(
        Path("runs/dd4-source/server/area"),
        include_all_areas=True,
    )
    secretary = world.mobiles[10249]

    assert source_mobile_identities(
        secretary.room_description,
        secretary.short_description,
        secretary.keywords,
    ) == ("sergeant at arm's secretary",)

    candidate = next(
        candidate
        for candidate in rank_hunt_candidates(
            world,
            character_level=19,
            include_xp_only=True,
            include_all_areas=True,
        )
        if candidate.mobile_vnum == 10249 and candidate.room_vnum == 10273
    )
    assert candidate.target_identity == "sergeant at arm's secretary"


def test_wander_search_follows_open_locked_exits_but_not_closed_locked_doors() -> None:
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "wanderer",
                "a wandering target",
                5,
                0,
                0,
                "test.are",
            )
        },
        rooms={
            1: RoomSource(
                1,
                "Origin",
                "test.are",
                exits={
                    "east": ExitSource("east", 2, 4, -1),
                },
            ),
            2: RoomSource(
                2,
                "Open Locked Room",
                "test.are",
                exits={
                    "west": ExitSource("west", 1, 4, -1),
                    "east": ExitSource("east", 3, 6, -1),
                },
            ),
            3: RoomSource(
                3,
                "Closed Locked Room",
                "test.are",
            ),
        },
        mob_resets=[MobReset(100, 1, 1, ())],
    )

    assert source_mobile_search_rooms(world, 100) == (1, 2)


def test_source_search_models_master_bound_and_confused_mobiles() -> None:
    rooms = {
        1: RoomSource(
            1,
            "Origin",
            "first.are",
            exits={"east": ExitSource("east", 2, 0, -1)},
        ),
        2: RoomSource(
            2,
            "Confused destination",
            "second.are",
            room_flags=1 << 2,
        ),
    }
    resets = [
        MobReset(100, 1, 1, ()),
        MobReset(101, 1, 1, ()),
    ]
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "pet",
                "a master-bound pet",
                5,
                ACT_DIE_IF_MASTER_GONE,
                0,
                "first.are",
            ),
            101: MobileSource(
                101,
                "confused",
                "a confused sentinel",
                5,
                (1 << 1) | (1 << 6),
                0,
                "first.are",
                affected_flags=AFF_CONFUSION,
            ),
        },
        rooms=rooms,
        mob_resets=resets,
    )

    assert source_mobile_search_rooms(world, 100) == (1,)
    assert source_mobile_search_rooms(world, 101) == (1, 2)


def test_area_parser_connects_mob_resets_to_direct_and_contained_loot() -> None:
    area = parse_area_file(FIXTURE)

    assert area.mobiles[100].level == 3
    assert area.mobiles[100].aggressive is True
    assert area.objects[200].source_cost == 100
    assert area.objects[200].weight == 1
    assert area.rooms[3001].sector_type == 0
    assert area.rooms[3001].exits["north"].destination == 3002
    assert area.mob_resets[1].object_vnums == (200, 201)
    assert area.mob_resets[1].equipment == ((16, 200),)
    assert area.container_contents[201] == [202]
    assert (area.objects[200].load_level_min, area.objects[200].load_level_max) == (
        1,
        3,
    )
    assert (area.objects[202].load_level_min, area.objects[202].load_level_max) == (
        1,
        4,
    )


def test_area_parser_captures_mobile_program_attack_commands(tmp_path: Path) -> None:
    area_file = tmp_path / "scripted.are"
    area_file.write_text(
        """#MOBILES
#100
scripted guard~
the scripted guard~
A scripted guard is here.~
It reacts to intruders.~
0 0 0 S
5 0 0 0d0+0 0d0+0
0 0
8 8 0
>greet_prog 100~
    say Seize the intruder!
    mpforce guard mpkill $n
~
|
#0
#OBJECTS
#0
""",
        encoding="latin-1",
    )

    area = parse_area_file(area_file, include_objects=False)

    program = area.mobiles[100].programs[0]
    assert program.trigger == "greet_prog"
    assert program.condition == "100"
    assert program.commands == (
        "say Seize the intruder!",
        "mpforce guard mpkill $n",
    )
    assert area.mobiles[100].attack_programs == (program,)


def test_area_parser_captures_mobile_teaching_entries(tmp_path: Path) -> None:
    area_file = tmp_path / "teacher.are"
    area_file.write_text(
        """#MOBILES
#100
teacher guildmaster~
the teacher~
A teacher is here.~
The teacher studies a ledger.~
0 0 0 S
5 0 0 0d0+0 0d0+0
0 0
8 8 0
& 20 'teacher base'
& 30 'engineer base'
#0
#OBJECTS
#0
""",
        encoding="latin-1",
    )

    mobile = parse_area_file(area_file, include_objects=False).mobiles[100]

    assert mobile.teaching_percent("engineer base") == 30
    assert mobile.teaches("teacher base")
    assert not mobile.teaches("runesmith base")


def test_area_parser_captures_source_undead_marker(tmp_path: Path) -> None:
    area_file = tmp_path / "undead.are"
    area_file.write_text(
        """#MOBILES
#100
undead guardian~
the undead guardian~
An undead guardian stands here.~
~
32|1073741824 0 0 S
5 0 0 0d0+0 0d0+0
128|256 0
8 8 0
#0
#OBJECTS
#0
""",
        encoding="latin-1",
    )

    area = parse_area_file(area_file, include_objects=False)

    assert area.mobiles[100].act_flags & ACT_UNDEAD
    assert area.mobiles[100].undead is True
    assert area.mobiles[100].body_form_flags == BODY_HUGE | BODY_INORGANIC
    assert area.mobiles[100].huge is True
    assert area.mobiles[100].inorganic is True


def test_area_parser_captures_mobile_rank_and_ranked_hp_bound(tmp_path: Path) -> None:
    area_file = tmp_path / "ranked.are"
    area_file.write_text(
        """#MOBILES
#100
elite guardian~
the elite guardian~
An elite guardian stands here.~
~
32 0 -500 S
5 0 0 0d0+0 0d0+0
0 0
8 8 0
< reserved~ elite~
#0
#OBJECTS
#0
""",
        encoding="latin-1",
    )

    mobile = parse_area_file(area_file, include_objects=False).mobiles[100]

    assert mobile.rank == "elite"
    assert mobile.rank_hp_multiplier == 5

    common = (8, 65)
    ranked = tuple(value * mobile.rank_hp_multiplier for value in common)
    assert ranked == (40, 325)


def test_candidate_ranking_uses_mobile_rank_for_hp_estimates() -> None:
    area = parse_area_file(FIXTURE)
    area.mobiles[100] = replace(area.mobiles[100], rank="elite")
    world = WorldSource(
        mobiles=area.mobiles,
        objects=area.objects,
        rooms=area.rooms,
        mob_resets=area.mob_resets,
        room_object_resets=area.room_object_resets,
        container_contents=area.container_contents,
        mobile_specials=area.mobile_specials,
    )

    candidate = next(
        item
        for item in rank_hunt_candidates(
            world,
            character_level=7,
            include_xp_only=True,
            include_all_areas=True,
        )
        if item.mobile_vnum == 100
    )

    assert candidate.rank == "elite"
    assert candidate.estimated_base_hp_range == (40, 325)


def test_candidate_ranking_preserves_source_body_form_flags() -> None:
    area = parse_area_file(FIXTURE)
    area.mobiles[100] = replace(
        area.mobiles[100],
        body_form_flags=BODY_HUGE | BODY_INORGANIC,
    )
    world = WorldSource(
        mobiles=area.mobiles,
        objects=area.objects,
        rooms=area.rooms,
        mob_resets=area.mob_resets,
        container_contents=area.container_contents,
        mobile_specials=area.mobile_specials,
    )

    candidates = rank_hunt_candidates(
        world,
        character_level=3,
        include_all_areas=True,
        include_below_band=True,
    )

    candidate = next(item for item in candidates if item.mobile_vnum == 100)
    assert candidate.target_body_form_flags == BODY_HUGE | BODY_INORGANIC


def test_mobile_source_body_form_macros_preserve_arm_exceptions() -> None:
    no_arms = MobileSource(
        100,
        "construct",
        "a construct",
        30,
        0,
        0,
        "test.are",
        body_form_flags=BODY_NO_EYES | BODY_NO_ARMS,
    )
    many_arms = MobileSource(
        101,
        "hydra",
        "a many-armed hydra",
        30,
        0,
        0,
        "test.are",
        body_form_flags=BODY_NO_EYES | PART_MANY_ARMS,
    )

    assert no_arms.has_arms is False
    assert many_arms.has_arms is True


def test_mobile_source_body_form_properties_are_unknown_without_source_evidence() -> None:
    mobile = MobileSource(
        100,
        "unknown",
        "an unknown-bodied mobile",
        5,
        0,
        0,
        "unknown.are",
    )

    assert mobile.body_form_flags is None
    assert mobile.huge is None
    assert mobile.inorganic is None
    assert mobile.has_arms is None
    assert mobile.has_head is None
    assert mobile.has_eyes is None


def test_source_subclass_teacher_route_uses_anon_blacksmith_for_smithy() -> None:
    world = load_world_source(
        Path("runs/dd4-source/server/area"),
        include_all_areas=True,
    )

    route = source_subclass_teacher_route(
        world,
        "engineer",
        character_class="smithy",
        preferred_mobile_vnums=(31002,),
    )

    assert route is not None
    assert route.mobile_vnum == 31002
    assert route.room_vnum == 31041
    assert route.keyword == "jolob"
    assert route.steps[0][0] == "3001"
    assert route.steps[-1] == ("31040", "west", "31041")
    assert source_subclass_teacher_skill("engineer") == "engineer base"
    assert world.mobiles[30259].teaches("teacher base")
    assert not world.mobiles[30259].teaches("engineer base")
    assert world.mobiles[31002].teaches("engineer base")


@pytest.mark.parametrize(
    ("character_class", "mobile_vnum", "room_vnum", "keyword"),
    (
        ("mage", 3020, 3019, "guildmaster"),
        ("cleric", 3021, 3002, "guildmaster"),
        ("thief", 3022, 3029, "guildmaster"),
        ("warrior", 3023, 3023, "guildmaster"),
        ("psionic", 3150, 3150, "guildmaster"),
        ("brawler", 3155, 3218, "guildmaster"),
        ("shifter", 3158, 3221, "guildmaster"),
        ("ranger", 3159, 3048, "ranger"),
        ("smithy", 3161, 3050, "craftsman"),
    ),
)
def test_source_class_teacher_route_uses_midgaard_level_ten_teacher(
    character_class: str,
    mobile_vnum: int,
    room_vnum: int,
    keyword: str,
) -> None:
    world = load_world_source(
        Path("runs/dd4-source/server/area"),
        include_all_areas=True,
    )

    route = source_class_teacher_route(
        world,
        character_class,
        preferred_room_vnum=room_vnum,
    )

    assert route is not None
    assert route.mobile_vnum == mobile_vnum
    assert route.room_vnum == room_vnum
    assert route.keyword == keyword
    assert route.steps[0][0] == "3001"
    assert source_class_teacher_skill(character_class)


def test_source_mobile_attack_program_is_a_candidate_hard_gate() -> None:
    world = load_world_source(
        Path("runs/dd4-source/server/area"),
        include_all_areas=True,
    )

    candidate = next(
        candidate
        for candidate in rank_hunt_candidates(
            world,
            character_level=17,
            character_max_hp=209,
            include_xp_only=True,
            include_all_areas=True,
        )
        if candidate.mobile_vnum == 9413 and candidate.room_vnum == 9419
    )

    assert candidate.status == "reject"
    assert (
        "source mobile program can initiate an unmodeled attack"
        in candidate.autonomy_rejections
    )


def test_non_corporeal_source_mobile_is_a_candidate_hard_gate() -> None:
    world = load_world_source(
        Path("runs/dd4-source/server/area"),
        include_all_areas=True,
    )

    candidate = next(
        candidate
        for candidate in rank_hunt_candidates(
            world,
            character_level=18,
            character_max_hp=416,
            include_xp_only=True,
            include_all_areas=True,
        )
        if candidate.mobile_vnum == 20505 and candidate.room_vnum == 20508
    )

    assert candidate.status == "reject"
    assert "source mobile is non-corporeal" in candidate.hazards
    assert "source mobile is non-corporeal" in candidate.autonomy_rejections


def test_money_value_converts_all_coin_denominations() -> None:
    assert money_value((50, 45, 6, 0)) == 1_100


def test_area_parser_preserves_potion_spell_names(tmp_path: Path) -> None:
    area_file = tmp_path / "potions.are"
    area_file.write_text(
        """#OBJECTS
#4150
black potion~
a black potion~
A thick black potion is here.~
~
10 0 1
15~ cure critical~ ~ ~
1 100 35
#0
""",
        encoding="latin-1",
    )

    item = parse_area_file(area_file).objects[4150]

    assert item.value_strings == ("15", "cure critical", "", "")
    assert potion_spell_names(item) == ("cure critical",)


def test_area_parser_preserves_staff_spell_names() -> None:
    item = ObjectSource(
        5302,
        "staff serpentine",
        "a green serpentine staff",
        ITEM_STAFF,
        (20, 2, 2),
        7600,
        value_strings=("20", "2", "2", "earthquake"),
    )

    assert castable_spell_names(item) == ("earthquake",)


@pytest.mark.parametrize(
    ("item_type", "expected"),
    (
        (10, ("potion", "quaff", False, True, False, None)),
        (ITEM_SCROLL, ("scroll", "recite", True, True, False, None)),
        (ITEM_WAND, ("wand", "zap", True, False, True, "self")),
        (ITEM_STAFF, ("staff", "brandish", True, False, True, None)),
    ),
)
def test_resource_activation_matches_dd4_object_commands(
    item_type: int,
    expected: tuple[object, ...],
) -> None:
    item = ObjectSource(
        5302,
        "sanctuary object",
        "a sanctuary object",
        item_type,
        (20, 2, 2, 1),
        7600,
        value_strings=("20", "sanctuary", "", ""),
    )

    activation = resource_activation_for_object(item, effect="sanctuary")

    assert activation is not None
    assert (
        activation.mode,
        activation.command,
        activation.requires_hold,
        activation.consumes_object,
        activation.consumes_charge,
        activation.target,
    ) == expected
    assert activation.spell == "sanctuary"


def test_resource_activation_can_request_exact_spell_from_multi_spell_object() -> None:
    item = ObjectSource(
        5303,
        "wand sanctuary cure critical",
        "a sanctuary recovery wand",
        ITEM_WAND,
        (20, 2, 3, 0),
        7600,
        value_strings=("20", "sanctuary", "cure critical", ""),
    )

    activation = resource_activation_for_object(
        item,
        effect="healing",
        spell_name="cure critical",
    )

    assert activation is not None
    assert activation.spell == "cure critical"
    assert activation.command == "zap"
    assert activation.consumes_charge is True


def test_area_parser_records_direct_coin_stash_resets(tmp_path: Path) -> None:
    area_file = tmp_path / "stash.are"
    area_file.write_text(
        """#OBJECTS
#100
coins~
a pile of coins~
A pile of coins is here.~
~
20 0 1
50~ 45~ 6~ 0~
1 0 0
#0
#ROOMS
#3001
Recall~
The recall room.~
0 0 0
D0
~
~
0 -1 3002
S
#3002
Treasury~
The treasury.~
0 8 0
S
#0
#RESETS
O 1 100 10 3002
S
""",
        encoding="latin-1",
    )

    area = parse_area_file(area_file)

    assert area.room_object_resets == [RoomObjectReset(100, 3002, 1)]


def test_rank_coin_stashes_promotes_direct_ground_money() -> None:
    world = WorldSource(
        objects={
            100: ObjectSource(
                100,
                "coins",
                "a pile of coins",
                ITEM_MONEY,
                (50, 45, 6, 0),
                0,
            )
        },
        rooms={
            3001: RoomSource(
                3001,
                "Recall",
                "midgaard.are",
                exits={"north": ExitSource("north", 3002, 0, -1)},
            ),
            3002: RoomSource(3002, "Treasury", "gnome.are"),
        },
        room_object_resets=[RoomObjectReset(100, 3002)],
    )

    candidates = rank_coin_stashes(
        world,
        character_level=19,
        include_all_areas=True,
    )

    assert len(candidates) == 1
    assert candidates[0].is_coin_stash is True
    assert candidates[0].contained_coins == 1_100
    assert candidates[0].ground_loot_keywords == ("coins",)


def test_rank_coin_stashes_rejects_a_reachable_aggressive_wanderer() -> None:
    world = WorldSource(
        mobiles={
            200: MobileSource(
                200,
                "grass carnivorous",
                "the carnivorous grass",
                16,
                ACT_AGGRESSIVE,
                0,
                "plains.are",
                room_description="A tall clump of grass growls at you and attacks!?",
            )
        },
        objects={
            100: ObjectSource(
                100,
                "coins",
                "a pile of coins",
                ITEM_MONEY,
                (50, 45, 6, 0),
                0,
            )
        },
        rooms={
            3001: RoomSource(
                3001,
                "Recall",
                "midgaard.are",
                exits={"north": ExitSource("north", 3002, 0, -1)},
            ),
            3002: RoomSource(
                3002,
                "Treasury",
                "gnome.are",
                exits={"east": ExitSource("east", 3003, 0, -1)},
            ),
            3003: RoomSource(
                3003,
                "Grass reset",
                "plains.are",
                exits={"west": ExitSource("west", 3002, 0, -1)},
            ),
        },
        mob_resets=[MobReset(200, 3003, 1, ())],
        room_object_resets=[RoomObjectReset(100, 3002)],
    )

    candidates = rank_coin_stashes(
        world,
        character_level=20,
        include_all_areas=True,
    )

    assert len(candidates) == 1
    assert candidates[0].status == "reject"
    assert "reachable wanderer: the carnivorous grass L16" in candidates[0].hazards
    assert "an aggressive wanderer inside the useful XP band can reach the route" in (
        candidates[0].autonomy_rejections
    )


def test_rank_coin_stashes_rejects_a_large_below_band_route_crowd() -> None:
    world = WorldSource(
        mobiles={
            200: MobileSource(
                200,
                "soldier hobgoblin",
                "the hobgoblin soldier",
                3,
                ACT_AGGRESSIVE,
                -600,
                "gnome.are",
            )
        },
        objects={
            100: ObjectSource(
                100,
                "coins",
                "a pile of coins",
                ITEM_MONEY,
                (50, 45, 6, 0),
                0,
            )
        },
        rooms={
            3001: RoomSource(
                3001,
                "Recall",
                "midgaard.are",
                exits={"south": ExitSource("south", 3002, 0, -1)},
            ),
            3002: RoomSource(
                3002,
                "Guarded passage",
                "gnome.are",
                exits={"south": ExitSource("south", 3003, 0, -1)},
            ),
            3003: RoomSource(3003, "Treasury", "gnome.are"),
        },
        mob_resets=[MobReset(200, 3002, 8, ())],
        room_object_resets=[RoomObjectReset(100, 3003)],
    )

    candidates = rank_coin_stashes(
        world,
        character_level=15,
        include_all_areas=True,
    )

    assert len(candidates) == 1
    assert candidates[0].status == "reject"
    assert any(
        "large below-band aggressive reset" in hazard
        for hazard in candidates[0].hazards
    )
    assert (
        "route crosses a large below-band aggressive crowd"
        in candidates[0].autonomy_rejections
    )


def test_rank_food_stashes_promotes_safe_food_and_excludes_poison() -> None:
    world = WorldSource(
        objects={
            100: ObjectSource(
                100,
                "rabbit roast wabbit",
                "a rabbit roast",
                ITEM_FOOD,
                (24, 0, 0, 0),
                0,
            ),
            101: ObjectSource(
                101,
                "mushroom",
                "a mushroom",
                ITEM_FOOD,
                (40, 0, 0, 1),
                0,
            ),
        },
        rooms={
            3001: RoomSource(
                3001,
                "Recall",
                "midgaard.are",
                exits={"south": ExitSource("south", 3002, 0, -1)},
            ),
            3002: RoomSource(3002, "Hermit hut", "plains.are"),
        },
        room_object_resets=[
            RoomObjectReset(100, 3002),
            RoomObjectReset(101, 3002),
        ],
    )

    candidates = rank_food_stashes(
        world,
        character_level=24,
        include_all_areas=True,
    )

    assert len(candidates) == 1
    assert candidates[0].is_food_stash is True
    assert candidates[0].source_value == 24
    assert candidates[0].ground_loot_keywords == ("wabbit",)
    assert candidates[0].ground_loot_object_vnums == (100,)
    assert candidates[0].loot == ("a rabbit roast",)


def test_rank_food_stashes_ignores_safe_fido_route_crowd() -> None:
    world = WorldSource(
        objects={
            100: ObjectSource(
                100,
                "rabbit roast wabbit",
                "a rabbit roast",
                ITEM_FOOD,
                (24, 0, 0, 0),
                0,
            ),
        },
        mobiles={
            200: MobileSource(
                200,
                "fido dog",
                "the beastly fido",
                0,
                ACT_AGGRESSIVE,
                0,
                "target.are",
            ),
        },
        rooms={
            3001: RoomSource(
                3001,
                "Recall",
                "midgaard.are",
                exits={"north": ExitSource("north", 7001, 0, -1)},
            ),
            7001: RoomSource(
                7001,
                "Fido street",
                "target.are",
                exits={"north": ExitSource("north", 7002, 0, -1)},
            ),
            7002: RoomSource(7002, "Food room", "target.are"),
        },
        mob_resets=[MobReset(200, 7001, 15, ())],
        room_object_resets=[RoomObjectReset(100, 7002)],
        mobile_specials={200: ("spec_fido",)},
    )

    [candidate] = rank_food_stashes(
        world,
        character_level=15,
        include_all_areas=True,
    )

    assert candidate.autonomous_safe
    assert candidate.route == ("north", "north")
    assert any("noncombat route special" in hazard for hazard in candidate.hazards)
    assert "route crosses a large below-band aggressive crowd" not in (
        candidate.autonomy_rejections
    )


def test_rank_food_stashes_preflights_probabilistic_route_program() -> None:
    world = WorldSource(
        objects={
            100: ObjectSource(
                100,
                "bread loaf",
                "a bread loaf",
                ITEM_FOOD,
                (30, 0, 0, 0),
                0,
            ),
        },
        mobiles={
            200: MobileSource(
                200,
                "drunk man",
                "the drunk",
                2,
                0,
                0,
                "target.are",
                programs=(
                    MobileProgram(
                        "greet_prog",
                        "10",
                        ("mpkill $n",),
                    ),
                ),
            ),
        },
        rooms={
            3001: RoomSource(
                3001,
                "Recall",
                "midgaard.are",
                exits={"north": ExitSource("north", 7001, 0, -1)},
            ),
            7001: RoomSource(
                7001,
                "Fido street",
                "target.are",
                exits={"north": ExitSource("north", 7002, 0, -1)},
            ),
            7002: RoomSource(7002, "Food room", "target.are"),
        },
        mob_resets=[MobReset(200, 7001, 1, ())],
        room_object_resets=[RoomObjectReset(100, 7002)],
    )

    [candidate] = rank_food_stashes(
        world,
        character_level=15,
        include_all_areas=True,
    )

    assert candidate.autonomous_safe
    assert candidate.status == "caution"
    assert candidate.autonomy_rejections == ()
    assert candidate.route_preflight_room_vnum == "3001"
    assert candidate.route_preflight_command == "where drunk"
    assert candidate.route_preflight_target == "the drunk"
    assert candidate.route_preflight_hard_hazard is True
    assert candidate.route_preflight_route_room_names == (
        "recall",
        "fido street",
        "food room",
    )


def test_candidate_ranking_values_mixed_denominations_on_mobile_loot() -> None:
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "treasurer",
                "a treasurer",
                5,
                0,
                0,
                "gnome.are",
            )
        },
        objects={
            200: ObjectSource(
                200,
                "coins",
                "a pile of coins",
                ITEM_MONEY,
                (50, 45, 6, 0),
                0,
            )
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            3002: RoomSource(3002, "Treasury", "gnome.are"),
        },
        mob_resets=[MobReset(100, 3002, 1, (200,))],
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 3002, 0, -1)

    candidates = rank_hunt_candidates(world, character_level=10)

    assert len(candidates) == 1
    assert candidates[0].target == "a treasurer"
    assert candidates[0].contained_coins == 1_100


def test_object_levels_follow_school_and_daycare_mobile_resets(
    tmp_path: Path,
) -> None:
    school = tmp_path / "school.are"
    school.write_text(
        """#AREA Tester~ Mud School~
1 5 0 100
#AREA_SPECIAL
school
$
#MOBILES
#3712
gladiator~
a gladiator~
A gladiator is here.~
~
0 0 0 S
1 0 0 1d1+0 1d1+0
0 0
8 8 1
#0
#OBJECTS
#3713
copper bracer~
a copper bracer~
A copper bracer is here.~
~
9 0 3
0~ 0~ 0~ 0~
5 100 5
#3721
snowy white stone~
a snowy white stone~
A snowy white stone is here.~
~
8 0 1
0~ 0~ 0~ 0~
1 100 2000
#0
#ROOMS
#0
#RESETS
M 0 3712 1 3722
G 0 3713 0
G 0 3721 0
S
""",
        encoding="latin-1",
    )
    daycare = tmp_path / "daycare.are"
    daycare.write_text(
        """#AREA Tester~ Dwarven Daycare~
1 10 0 100
#MOBILES
#6605
doll old~
an old doll~
An old doll is here.~
~
0 0 0 S
1 0 0 1d1+0 1d1+0
0 0
8 8 0
#6606
nanny~
the nanny~
An old wrinkled nanny is here.~
~
0 0 0 S
5 0 0 1d1+0 1d1+0
0 0
8 8 2
#0
#OBJECTS
#6601
ring pink ice~
a pink ice ring~
A pink ice ring is here.~
~
9 0 3
0~ 0~ 0~ 0~
8 7000 2500
#6621
robe linen~
a linen robe~
A linen robe is here.~
~
9 0 1025
0~ 0~ 0~ 0~
5 4000 2000
#0
#ROOMS
#0
#RESETS
M 0 6605 2 6605
E 1 6601 20 1
M 0 6606 2 6602
E 1 6621 20 12
S
""",
        encoding="latin-1",
    )

    objects = load_object_sources(tmp_path)

    assert objects[3713].level == 5
    assert objects[3721].level == 2000
    assert (objects[3713].load_level_min, objects[3713].load_level_max) == (1, 1)
    assert (objects[3721].load_level_min, objects[3721].load_level_max) == (1, 1)
    assert objects[6601].level == 2500
    assert (objects[6601].load_level_min, objects[6601].load_level_max) == (1, 1)
    assert objects[6621].level == 2000
    assert (objects[6621].load_level_min, objects[6621].load_level_max) == (1, 5)


def test_area_parser_ignores_mobile_program_vnum_references(tmp_path) -> None:
    area_file = tmp_path / "scripted.are"
    area_file.write_text(
        """#MOBILES
#100
rat~
a rat~
A rat is here.~
Small but hostile.~
0 0 0 S
3 0 0 0d0+0 0d0+0
0 0
8 8 0
#200
keyword~
short~
long~
description~
not-a-mobile-header
mpecho a mobile program reference
#0
#OBJECTS
#0
""",
        encoding="latin-1",
    )

    area = parse_area_file(area_file, include_objects=False)

    assert set(area.mobiles) == {100}


def test_area_parser_accepts_spaced_legacy_exit_markers(tmp_path) -> None:
    area_file = tmp_path / "legacy-exits.are"
    area_file.write_text(
        """#ROOMS
#9400
The Foyer~
A legacy room.~
0 8 0
D 0
A guarded door.~
door north~
1 -1 9401
S
#9401
A Guard Room~
The destination.~
0 8 0
D 2
The return door.~
door south~
1 -1 9400
S
#0
""",
        encoding="latin-1",
    )

    area = parse_area_file(area_file)

    assert area.rooms[9400].exits["north"].destination == 9401
    assert area.rooms[9401].exits["south"].destination == 9400


def test_candidate_ranking_rejects_route_through_higher_level_aggressor(
    monkeypatch,
) -> None:
    area = parse_area_file(FIXTURE)
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("hunt_area.are",),
    )
    world = WorldSource(
        mobiles=area.mobiles,
        objects=area.objects,
        rooms=area.rooms,
        mob_resets=area.mob_resets,
        container_contents=area.container_contents,
        mobile_specials=area.mobile_specials,
    )

    candidates = rank_hunt_candidates(
        world,
        character_level=6,
        boot_kill_counts={"cellar rat": 2},
    )

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.status == "reject"
    assert candidate.route == ("north", "north")
    assert candidate.room_spawn_count == 1
    assert candidate.source_spawn_limit == 2
    assert candidate.boot_kills == 2
    assert candidate.loot == ("a rusty sword",)
    assert candidate.contained_coins == 50
    assert candidate.equipped_weapons == ("a rusty sword",)
    assert candidate.estimated_level_range == (1, 5)
    assert candidate.estimated_base_hp_range == (8, 65)
    assert candidate.estimated_peak_round_damage == 60
    assert "route: the dangerous guard L8 in 3002" in candidate.hazards
    assert any("NPC base damage x1.5" in hazard for hazard in candidate.hazards)
    assert not any("instance limit" in hazard for hazard in candidate.hazards)


def test_candidate_records_exact_aggressive_route_mobile_for_policy_gates() -> None:
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "target",
                "the field target",
                20,
                0,
                0,
                "target.are",
            ),
            200: MobileSource(
                200,
                "rolling rock",
                "the rolling rock",
                15,
                ACT_AGGRESSIVE,
                0,
                "target.are",
            ),
        },
        rooms={
            3001: RoomSource(
                3001,
                "Recall",
                "midgaard.are",
                exits={"north": ExitSource("north", 7001, 0, -1)},
            ),
            7001: RoomSource(
                7001,
                "Transit",
                "target.are",
                exits={"north": ExitSource("north", 7002, 0, -1)},
            ),
            7002: RoomSource(7002, "Target room", "target.are"),
        },
        mob_resets=[
            MobReset(200, 7001, 1, ()),
            MobReset(100, 7002, 1, ()),
        ],
    )

    [candidate] = rank_hunt_candidates(
        world,
        character_level=25,
        include_xp_only=True,
        include_all_areas=True,
    )

    assert not candidate.autonomous_safe
    assert (
        "route crosses an aggressive transit attacker inside the transit-risk band"
        in candidate.autonomy_rejections
    )
    assert candidate.route_hazard_mobile_vnums == (200,)
    assert candidate.route_aggressive_mobile_vnums == (200,)
    assert candidate.route_attack_program_mobile_vnums == ()
    assert candidate.route_special_mobile_vnums == ()


def test_armed_mobile_damage_keeps_ordinary_peak_separate_from_critical_burst() -> None:
    assert _mobile_peak_round_damage(
        14,
        wielding=True,
        dual_wielding=False,
    ) == 180
    assert _mobile_critical_hit_damage(14, wielding=True) == 72


def test_mobile_expected_round_damage_mirrors_npc_follow_up_chances() -> None:
    assert mobile_expected_round_damage(
        18,
        wielding=False,
        dual_wielding=False,
    ) == 36
    assert mobile_expected_round_damage(
        20,
        wielding=False,
        dual_wielding=False,
    ) == 48


def test_sanctuary_mobile_damage_halves_each_strike_before_round_totals() -> None:
    assert mobile_sanctuary_peak_round_damage(
        33,
        wielding=False,
        dual_wielding=False,
    ) == 168
    assert mobile_sanctuary_critical_hit_damage(33, wielding=False) == 56
    assert mobile_sanctuary_peak_round_damage(
        34,
        wielding=False,
        dual_wielding=False,
    ) == 174


def test_candidate_ranking_includes_aggressors_from_transit_areas(monkeypatch) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(100, "rat", "a cellar rat", 3, 0, 0, "target.are"),
            200: MobileSource(
                200,
                "wolf",
                "a large grey wolf",
                8,
                1 << 5,
                0,
                "transit.are",
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            6008: RoomSource(6008, "Forest clearing", "transit.are"),
            6009: RoomSource(6009, "Forest track", "transit.are"),
            7001: RoomSource(7001, "Rat cellar", "target.are"),
        },
        objects={
            300: ObjectSource(300, "sword", "a rusty sword", 5, (), 100),
        },
        mob_resets=[MobReset(200, 6009, 1, ()), MobReset(100, 7001, 1, (300,))],
    )
    world.rooms[3001].exits["west"] = ExitSource("west", 6008, 0, -1)
    world.rooms[6008].exits["west"] = ExitSource("west", 7001, 0, -1)
    world.rooms[6009].exits["south"] = ExitSource("south", 6008, 0, -1)

    candidates = rank_hunt_candidates(world, character_level=6)

    assert candidates[0].status == "reject"
    assert "reachable wanderer: a large grey wolf L8" in candidates[0].hazards


def test_candidate_ranking_rejects_below_band_wanderer_inside_transit_risk(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(100, "rat", "a cellar rat", 3, 0, 0, "target.are"),
            200: MobileSource(
                200,
                "wolf",
                "a large grey wolf",
                8,
                ACT_AGGRESSIVE,
                0,
                "transit.are",
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            6008: RoomSource(6008, "Forest clearing", "transit.are"),
            6009: RoomSource(6009, "Forest track", "transit.are"),
            7001: RoomSource(7001, "Rat cellar", "target.are"),
        },
        objects={
            300: ObjectSource(300, "sword", "a rusty sword", 5, (), 100),
        },
        mob_resets=[MobReset(200, 6009, 1, ()), MobReset(100, 7001, 1, (300,))],
    )
    world.rooms[3001].exits["west"] = ExitSource("west", 6008, 0, -1)
    world.rooms[6008].exits["west"] = ExitSource("west", 7001, 0, -1)
    world.rooms[6009].exits["south"] = ExitSource("south", 6008, 0, -1)

    candidates = rank_hunt_candidates(
        world,
        character_level=15,
        include_below_band=True,
    )

    assert candidates[0].status == "caution"
    assert not candidates[0].autonomous_safe
    assert (
        "an aggressive wanderer inside the transit-risk band can reach the route"
        in candidates[0].autonomy_rejections
    )


def test_candidate_ranking_can_expand_beyond_conservative_area_set(monkeypatch) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("starter.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(100, "rat", "a starter rat", 5, 0, 0, "starter.are"),
            200: MobileSource(200, "ogre", "a later ogre", 5, 0, 0, "later.are"),
        },
        objects={
            300: ObjectSource(300, "coin", "a coin", 8, (), 1),
            400: ObjectSource(400, "gem", "a gem", 8, (), 1),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Starter den", "starter.are"),
            7002: RoomSource(7002, "Later den", "later.are"),
        },
        mob_resets=[MobReset(100, 7001, 1, (300,)), MobReset(200, 7002, 1, (400,))],
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)
    world.rooms[7001].exits["east"] = ExitSource("east", 7002, 0, -1)

    conservative = rank_hunt_candidates(world, character_level=5)
    expanded = rank_hunt_candidates(
        world,
        character_level=5,
        include_all_areas=True,
    )

    assert [candidate.target for candidate in conservative] == ["a starter rat"]
    assert {candidate.target for candidate in expanded} == {
        "a starter rat",
        "a later ogre",
    }


def test_candidate_ranking_can_include_explicit_safe_level_ceiling_probe() -> None:
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "frontier target",
                "a frontier target",
                6,
                0,
                0,
                "frontier.are",
            )
        },
        rooms={
            3001: RoomSource(
                3001,
                "Recall",
                "midgaard.are",
                exits={"north": ExitSource("north", 7001, 0, -1)},
            ),
            7001: RoomSource(7001, "Frontier room", "frontier.are"),
        },
        mob_resets=[MobReset(100, 7001, 1, ())],
    )

    ordinary = rank_hunt_candidates(
        world,
        character_level=5,
        include_xp_only=True,
        include_all_areas=True,
    )
    probe = rank_hunt_candidates(
        world,
        character_level=5,
        include_xp_only=True,
        character_max_hp=100,
        include_level_ceiling_candidates=True,
        include_all_areas=True,
    )

    assert ordinary == []
    assert len(probe) == 1
    assert probe[0].estimated_level_range == (4, 8)
    assert probe[0].estimated_peak_round_damage < 100


def test_candidate_ranking_accepts_a_quest_band_ceiling_only_when_requested() -> None:
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "quest target",
                "a quest target",
                9,
                0,
                0,
                "frontier.are",
            )
        },
        rooms={
            3001: RoomSource(
                3001,
                "Recall",
                "midgaard.are",
                exits={"north": ExitSource("north", 7001, 0, -1)},
            ),
            7001: RoomSource(7001, "Quest room", "frontier.are"),
        },
        mob_resets=[MobReset(100, 7001, 1, ())],
    )

    ordinary = rank_hunt_candidates(
        world,
        character_level=5,
        include_xp_only=True,
        include_all_areas=True,
        character_max_hp=100,
        include_level_ceiling_candidates=True,
    )
    quest = rank_hunt_candidates(
        world,
        character_level=5,
        include_xp_only=True,
        include_all_areas=True,
        character_max_hp=100,
        include_level_ceiling_candidates=True,
        level_ceiling_offset=4,
    )

    assert ordinary == []
    assert [candidate.mobile_vnum for candidate in quest] == [100]


def test_candidate_ranking_marks_source_shopkeepers_as_non_xp_targets() -> None:
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "trader",
                "a trader",
                6,
                0,
                0,
                "frontier.are",
            )
        },
        rooms={
            3001: RoomSource(
                3001,
                "Recall",
                "midgaard.are",
                exits={"north": ExitSource("north", 7001, 0, -1)},
            ),
            7001: RoomSource(7001, "Frontier room", "frontier.are"),
        },
        mob_resets=[MobReset(100, 7001, 1, ())],
        shopkeepers={100},
    )

    [candidate] = rank_hunt_candidates(
        world,
        character_level=6,
        include_xp_only=True,
        include_all_areas=True,
    )

    assert candidate.status == "reject"
    assert candidate.autonomous_safe is False
    assert "source mobile is a shopkeeper" in candidate.autonomy_rejections


def test_candidate_ranking_rejects_source_fame_loss_targets() -> None:
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "helpful citizen",
                "a helpful citizen",
                6,
                1 << 15,
                0,
                "frontier.are",
            )
        },
        rooms={
            3001: RoomSource(
                3001,
                "Recall",
                "midgaard.are",
                exits={"north": ExitSource("north", 7001, 0, -1)},
            ),
            7001: RoomSource(7001, "Frontier room", "frontier.are"),
        },
        mob_resets=[MobReset(100, 7001, 1, ())],
    )

    [candidate] = rank_hunt_candidates(
        world,
        character_level=6,
        include_xp_only=True,
        include_all_areas=True,
    )

    assert candidate.status == "reject"
    assert candidate.autonomous_safe is False
    assert "source mobile costs fame when killed" in candidate.autonomy_rejections


def test_source_mobile_coin_carrier_is_ranked_for_funding() -> None:
    world = load_world_source(
        Path("runs/dd4-source/server/area"),
        include_all_areas=True,
    )

    candidate = next(
        candidate
        for candidate in rank_hunt_candidates(
            world,
            character_level=19,
            include_below_band=True,
            include_all_areas=True,
        )
        if candidate.mobile_vnum == 18007 and candidate.room_vnum == 18042
    )

    assert candidate.contained_coins == 20_000
    assert candidate.is_coin_stash is False
    assert "target has special procedure spec_breath_any" in (
        candidate.autonomy_rejections
    )


def test_source_mobile_kill_caps_are_scoped_by_mobile_vnum() -> None:
    world = load_world_source(
        Path("runs/dd4-source/server/area"),
        include_all_areas=True,
    )
    candidates = rank_hunt_candidates(
        world,
        character_level=19,
        boot_kill_counts={"Secretary": 12},
        boot_kill_counts_by_mobile_vnum={10249: 12},
        include_xp_only=True,
        include_level_ceiling_candidates=True,
        character_max_hp=264,
        include_all_areas=True,
    )

    untouched = next(
        candidate
        for candidate in candidates
        if candidate.mobile_vnum == 10248 and candidate.room_vnum == 10295
    )
    exhausted = next(
        candidate
        for candidate in candidates
        if candidate.mobile_vnum == 10249 and candidate.room_vnum == 10273
    )

    assert untouched.boot_kills == 0
    assert exhausted.boot_kills == 12


def test_route_preflight_metadata_softens_only_below_band_source_hazards() -> None:
    world = WorldSource(
        mobiles={
            1300: MobileSource(
                1300,
                "shadow guardian",
                "a shadow guardian",
                9,
                1 << 5,
                0,
                "hitower.are",
            )
        }
    )
    route = route_named("galaxy white dwarf").commands

    below_band = _route_preflight_metadata(
        world,
        route,
        character_level=19,
    )
    useful_band = _route_preflight_metadata(
        world,
        route,
        character_level=14,
    )

    assert below_band[:4] == (
        "1300",
        "where shadow guardian",
        "shadow guardian",
        (7, 11),
    )
    assert below_band[4] is False
    assert useful_band[4] is True


def test_candidate_ranking_can_include_below_band_loot_targets() -> None:
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "carrier",
                "a loot carrier",
                1,
                0,
                0,
                "ambush.are",
            )
        },
        objects={
            300: ObjectSource(300, "sword", "a saleable sword", 5, (), 100),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Carrier room", "ambush.are"),
        },
        mob_resets=[MobReset(100, 7001, 1, (300,))],
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)

    ordinary = rank_hunt_candidates(world, character_level=8)
    funding = rank_hunt_candidates(
        world,
        character_level=8,
        include_below_band=True,
    )

    assert ordinary == []
    assert len(funding) == 1
    assert funding[0].estimated_level_range == (1, 3)


def test_candidate_ranking_rejects_high_level_room_companion(monkeypatch) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(100, "doe", "a doe", 5, 0, 0, "target.are"),
            200: MobileSource(
                200,
                "hierophant",
                "the Hierophant",
                15,
                0,
                0,
                "target.are",
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Sacred grove", "target.are"),
        },
        mob_resets=[MobReset(100, 7001, 2, ()), MobReset(200, 7001, 1, ())],
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)

    candidate = rank_hunt_candidates(
        world,
        character_level=7,
        include_xp_only=True,
    )[0]

    assert candidate.status == "reject"
    assert "target reset permits up to 2 matching mobiles in the room" in candidate.hazards
    assert "room companion: the Hierophant L15 (up to 1)" in candidate.hazards


def test_candidate_ranking_rejects_same_vnum_assist_capacity(monkeypatch) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("fleshmonger.are",),
    )
    world = WorldSource(
        mobiles={
            9405: MobileSource(
                9405,
                "guard duty",
                "the on-duty guard",
                10,
                (1 << 1) | (1 << 5) | (1 << 6),
                -500,
                "fleshmonger.are",
            ),
        },
        objects={
            9400: ObjectSource(
                9400,
                "key cell",
                "a cell key",
                18,
                (9404,),
                1,
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            9406: RoomSource(9406, "A Guard Room", "fleshmonger.are"),
        },
        mob_resets=[MobReset(9405, 9406, 2, (9400,))],
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 9406, 0, -1)

    candidate = rank_hunt_candidates(
        world,
        character_level=10,
        include_xp_only=True,
    )[0]

    assert candidate.status == "reject"
    assert (
        "target reset permits up to 2 matching mobiles in the room"
        in candidate.hazards
    )


def test_candidate_ranking_keeps_an_isolated_aggressive_target_in_risk_pool(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "raider",
                "a hostile raider",
                5,
                1 << 5,
                -500,
                "target.are",
            ),
        },
        objects={
            200: ObjectSource(200, "dagger", "a rusty dagger", 5, (), 10),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Raiders' camp", "target.are"),
        },
        mob_resets=[MobReset(100, 7001, 1, (200,))],
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)

    candidate = rank_hunt_candidates(
        world,
        character_level=5,
        include_xp_only=True,
    )[0]

    assert candidate.status == "caution"
    assert candidate.autonomous_safe
    assert "target is aggressive" in candidate.hazards


def test_candidate_ranking_rejects_aggressive_target_below_useful_fuzz_floor(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "guard",
                "an aggressive guard",
                12,
                ACT_AGGRESSIVE,
                -500,
                "target.are",
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Guard post", "target.are"),
        },
        mob_resets=[MobReset(100, 7001, 1, ())],
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)

    [candidate] = rank_hunt_candidates(
        world,
        character_level=16,
        include_xp_only=True,
    )

    assert candidate.estimated_level_range == (10, 14)
    assert candidate.status == "reject"
    assert not candidate.autonomous_safe
    assert "target is aggressive" in candidate.hazards
    assert "target is aggressive" in candidate.autonomy_rejections


def test_candidate_ranking_excludes_wanderer_behind_reset_closed_door(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(100, "rat", "a cellar rat", 5, 0, 0, "target.are"),
            200: MobileSource(
                200,
                "guard",
                "a dangerous guard",
                10,
                (1 << 5) | (1 << 6),
                0,
                "target.are",
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Forest track", "target.are"),
            7002: RoomSource(7002, "Rat cellar", "target.are"),
            7003: RoomSource(7003, "Guard post", "target.are"),
        },
        objects={},
        mob_resets=[MobReset(100, 7002, 1, ()), MobReset(200, 7003, 1, ())],
    )
    world.rooms[3001].exits["west"] = ExitSource("west", 7001, 0, -1)
    world.rooms[7001].exits["west"] = ExitSource("west", 7002, 0, -1)
    world.rooms[7003].exits["north"] = ExitSource(
        "north",
        7001,
        0,
        -1,
        reset_state=1,
    )

    candidate = rank_hunt_candidates(
        world,
        character_level=7,
        include_xp_only=True,
    )[0]

    assert candidate.status == "promising"
    assert candidate.autonomous_safe
    assert not any("wanderer" in hazard for hazard in candidate.hazards)


def test_candidate_allows_source_trivial_room_companion(monkeypatch) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(100, "target", "the target", 8, 0, 0, "target.are"),
            200: MobileSource(
                200,
                "bystander",
                "a harmless bystander",
                3,
                0,
                0,
                "target.are",
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Target room", "target.are"),
        },
        mob_resets=[
            MobReset(100, 7001, 1, ()),
            MobReset(200, 7001, 1, ()),
        ],
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)

    candidate = rank_hunt_candidates(
        world,
        character_level=10,
        include_xp_only=True,
    )[0]

    assert candidate.autonomous_safe
    assert "source-backed trivial companion: a harmless bystander" in candidate.hazards
    assert "target room has a dangerous reset companion" not in candidate.autonomy_rejections


def test_fleshmonger_cook_companion_is_source_capable_assister() -> None:
    world = load_world_source(
        Path("runs/dd4-source/server/area"),
        include_all_areas=True,
    )
    boy = world.mobiles[9404]

    assert source_mobile_can_join_player_fight(
        world,
        boy,
        character_level=9,
    )

    candidate = next(
        candidate
        for candidate in rank_hunt_candidates(
            world,
            character_level=9,
            include_xp_only=True,
            include_all_areas=True,
        )
        if candidate.mobile_vnum == 9403 and candidate.room_vnum == 9403
    )

    assert not candidate.autonomous_safe
    assert (
        "source-backed companion may join player combat: the cook's boy"
        in candidate.hazards
    )
    assert (
        "target room has a source-capable assisting companion"
        in candidate.autonomy_rejections
    )
    assert "source-backed trivial companion: the cook's boy" not in candidate.hazards


def test_candidate_rejects_special_procedure_room_companion(monkeypatch) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(100, "target", "the target", 8, 0, 0, "target.are"),
            200: MobileSource(
                200,
                "bystander",
                "a poisonous bystander",
                3,
                0,
                0,
                "target.are",
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Target room", "target.are"),
        },
        mob_resets=[
            MobReset(100, 7001, 1, ()),
            MobReset(200, 7001, 1, ()),
        ],
        mobile_specials={200: ("spec_poison",)},
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)

    candidate = rank_hunt_candidates(
        world,
        character_level=7,
        include_xp_only=True,
    )[0]

    assert not candidate.autonomous_safe
    assert "target room has a dangerous reset companion" in candidate.autonomy_rejections


def test_candidate_allows_source_below_band_special_room_companion(monkeypatch) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(100, "target", "the target", 8, 0, 0, "target.are"),
            200: MobileSource(
                200,
                "bystander",
                "a poisonous bystander",
                3,
                0,
                0,
                "target.are",
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Target room", "target.are"),
        },
        mob_resets=[
            MobReset(100, 7001, 1, ()),
            MobReset(200, 7001, 1, ()),
        ],
        mobile_specials={200: ("spec_poison",)},
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)

    candidate = rank_hunt_candidates(
        world,
        character_level=10,
        include_xp_only=True,
    )[0]

    assert candidate.autonomous_safe
    assert "source-backed trivial companion: a poisonous bystander" in candidate.hazards
    assert "target room has a dangerous reset companion" not in candidate.autonomy_rejections


def test_candidate_rejects_below_band_greet_program_room_companion(monkeypatch) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(100, "target", "the target", 8, 0, 0, "target.are"),
            200: MobileSource(
                200,
                "ambusher",
                "an ambushing bystander",
                3,
                ACT_AGGRESSIVE,
                0,
                "target.are",
                programs=(
                    MobileProgram(
                        "greet_prog",
                        "100",
                        ("mpkill $n",),
                    ),
                ),
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Target room", "target.are"),
        },
        mob_resets=[
            MobReset(100, 7001, 1, ()),
            MobReset(200, 7001, 1, ()),
        ],
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)

    candidate = rank_hunt_candidates(
        world,
        character_level=10,
        include_xp_only=True,
    )[0]

    assert not candidate.autonomous_safe
    assert "target room has a program-triggered attacker" in candidate.autonomy_rejections
    assert "source-backed trivial companion: an ambushing bystander" not in candidate.hazards


def test_candidate_ranking_can_include_targets_without_known_loot(monkeypatch) -> None:
    area = parse_area_file(FIXTURE)
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("hunt_area.are",),
    )
    world = WorldSource(
        mobiles=area.mobiles,
        objects=area.objects,
        rooms=area.rooms,
        mob_resets=area.mob_resets,
        container_contents=area.container_contents,
        mobile_specials=area.mobile_specials,
    )

    loot_candidates = rank_hunt_candidates(world, character_level=9)
    xp_candidates = rank_hunt_candidates(
        world,
        character_level=9,
        include_xp_only=True,
    )

    assert [candidate.target for candidate in loot_candidates] == ["a cellar rat"]
    assert {candidate.target for candidate in xp_candidates} == {
        "a cellar rat",
        "the dangerous guard",
    }


def test_candidate_ranking_omits_resets_that_cannot_award_useful_xp(monkeypatch) -> None:
    area = parse_area_file(FIXTURE)
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("hunt_area.are",),
    )
    world = WorldSource(
        mobiles=area.mobiles,
        objects=area.objects,
        rooms=area.rooms,
        mob_resets=area.mob_resets,
        container_contents=area.container_contents,
        mobile_specials=area.mobile_specials,
    )

    candidates = rank_hunt_candidates(
        world,
        character_level=10,
        include_xp_only=True,
    )

    assert [candidate.target for candidate in candidates] == [
        "the dangerous guard"
    ]


def test_candidate_ranking_rejects_source_peak_round_above_character_hp(
    monkeypatch,
) -> None:
    area = parse_area_file(FIXTURE)
    area.mobiles[100] = replace(area.mobiles[100], alignment=100)
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("hunt_area.are",),
    )
    world = WorldSource(
        mobiles=area.mobiles,
        objects=area.objects,
        rooms=area.rooms,
        mob_resets=area.mob_resets,
        container_contents=area.container_contents,
        mobile_specials=area.mobile_specials,
    )

    candidate = rank_hunt_candidates(
        world,
        character_level=9,
        character_max_hp=50,
    )[0]

    assert candidate.status == "reject"
    assert "source peak round 60 >= character max HP 50" in candidate.hazards


def test_positive_alignment_npc_remains_an_autonomous_candidate() -> None:
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "lawful target",
                "a lawful target",
                5,
                0,
                100,
                "target.are",
            )
        },
        rooms={
            3001: RoomSource(
                3001,
                "Recall",
                "midgaard.are",
                exits={"north": ExitSource("north", 7001, 0, -1)},
            ),
            7001: RoomSource(7001, "Target room", "target.are"),
        },
        mob_resets=[MobReset(100, 7001, 1, ())],
    )

    candidate = rank_hunt_candidates(
        world,
        character_level=7,
        include_xp_only=True,
        include_all_areas=True,
    )[0]

    assert candidate.autonomous_safe
    assert candidate.status == "caution"
    assert "positive alignment target (100)" in candidate.hazards
    assert "target has positive alignment" not in candidate.autonomy_rejections


def test_high_positive_alignment_npc_is_ranked_cautiously_not_rejected() -> None:
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "lawful target",
                "a lawful target",
                18,
                0,
                1000,
                "target.are",
            )
        },
        rooms={
            3001: RoomSource(
                3001,
                "Recall",
                "midgaard.are",
                exits={"north": ExitSource("north", 7001, 0, -1)},
            ),
            7001: RoomSource(7001, "Target room", "target.are"),
        },
        mob_resets=[MobReset(100, 7001, 1, ())],
    )

    candidate = rank_hunt_candidates(
        world,
        character_level=19,
        include_xp_only=True,
        include_all_areas=True,
    )[0]

    assert candidate.autonomous_safe
    assert candidate.status == "caution"
    assert "positive alignment target (1000)" in candidate.hazards


def test_autonomous_filter_uses_route_aggressor_fuzzed_maximum(monkeypatch) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(100, "target", "the target", 29, 0, 0, "target.are"),
            200: MobileSource(
                200,
                "guard",
                "the route guard",
                25,
                1 << 5,
                0,
                "target.are",
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Guard post", "target.are"),
            7002: RoomSource(7002, "Target room", "target.are"),
        },
        mob_resets=[MobReset(200, 7001, 1, ()), MobReset(100, 7002, 1, ())],
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)
    world.rooms[7001].exits["north"] = ExitSource("north", 7002, 0, -1)

    candidate = rank_hunt_candidates(
        world,
        character_level=31,
        include_xp_only=True,
    )[0]

    assert not candidate.autonomous_safe
    assert (
        "route crosses an aggressive reset inside the useful XP band"
        in candidate.autonomy_rejections
    )


def test_autonomous_filter_rejects_a_reachable_combat_joining_guard(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "target",
                "the target",
                8,
                0,
                0,
                "target.are",
            ),
            200: MobileSource(
                200,
                "guard",
                "the source guard",
                8,
                1 << 6,
                0,
                "target.are",
            ),
        },
        rooms={
            3001: RoomSource(
                3001,
                "Recall",
                "midgaard.are",
                exits={"north": ExitSource("north", 7001, 0, -1)},
            ),
            7001: RoomSource(
                7001,
                "Target room",
                "target.are",
                exits={"east": ExitSource("east", 7002, 0, -1)},
            ),
            7002: RoomSource(
                7002,
                "Guard post",
                "target.are",
                exits={"west": ExitSource("west", 7001, 0, -1)},
            ),
        },
        mob_resets=[
            MobReset(100, 7001, 1, ()),
            MobReset(200, 7002, 1, ()),
        ],
        mobile_specials={200: ("spec_guard",)},
    )

    [candidate] = [
        candidate
        for candidate in rank_hunt_candidates(
            world,
            character_level=8,
            include_xp_only=True,
        )
        if candidate.mobile_vnum == 100
    ]

    assert not candidate.autonomous_safe
    assert "reachable combat-joining special: the source guard L8" in (
        candidate.hazards
    )
    assert (
        "a higher-level combat-joining special can reach the route"
        in candidate.autonomy_rejections
    )


def test_autonomous_filter_allows_bounded_borderline_route_aggressor(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(100, "target", "the target", 29, 0, 0, "target.are"),
            200: MobileSource(
                200,
                "guard",
                "the route guard",
                25,
                ACT_AGGRESSIVE,
                0,
                "target.are",
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Guard post", "target.are"),
            7002: RoomSource(7002, "Target room", "target.are"),
        },
        mob_resets=[MobReset(200, 7001, 1, ()), MobReset(100, 7002, 1, ())],
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)
    world.rooms[7001].exits["north"] = ExitSource("north", 7002, 0, -1)

    candidate = next(
        candidate
        for candidate in rank_hunt_candidates(
            world,
            character_level=31,
            character_max_hp=500,
            include_xp_only=True,
        )
        if candidate.mobile_vnum == 100
    )

    assert candidate.autonomous_safe
    assert any(
        "bounded borderline route aggressor" in hazard
        for hazard in candidate.hazards
    )


def test_autonomous_filter_rejects_large_below_band_route_crowd(monkeypatch) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(100, "target", "the target", 10, 0, 0, "target.are"),
            200: MobileSource(
                200,
                "soldier",
                "the route soldier",
                3,
                ACT_AGGRESSIVE,
                0,
                "target.are",
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Barracks", "target.are"),
            7002: RoomSource(7002, "Target room", "target.are"),
        },
        mob_resets=[
            MobReset(200, 7001, 8, ()),
            MobReset(100, 7002, 1, ()),
        ],
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)
    world.rooms[7001].exits["north"] = ExitSource("north", 7002, 0, -1)

    candidate = next(
        candidate
        for candidate in rank_hunt_candidates(
            world,
            character_level=15,
            include_xp_only=True,
        )
        if candidate.mobile_vnum == 100
    )

    assert not candidate.autonomous_safe
    assert (
        "route crosses a large below-band aggressive crowd"
        in candidate.autonomy_rejections
    )
    assert any(
        "up to 8 mobiles" in hazard for hazard in candidate.hazards
    )


def test_autonomous_filter_allows_large_low_level_route_crowd_above_aggro_cutoff(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(100, "target", "the target", 25, 0, 0, "target.are"),
            200: MobileSource(
                200,
                "soldier",
                "the route soldier",
                3,
                ACT_AGGRESSIVE,
                0,
                "target.are",
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Barracks", "target.are"),
            7002: RoomSource(7002, "Target room", "target.are"),
        },
        mob_resets=[
            MobReset(200, 7001, 8, ()),
            MobReset(100, 7002, 1, ()),
        ],
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)
    world.rooms[7001].exits["north"] = ExitSource("north", 7002, 0, -1)

    [candidate] = [
        candidate
        for candidate in rank_hunt_candidates(
            world,
            character_level=25,
            include_xp_only=True,
        )
        if candidate.mobile_vnum == 100
    ]

    assert candidate.autonomous_safe
    assert "route crosses a large below-band aggressive crowd" not in (
        candidate.autonomy_rejections
    )


def test_autonomous_filter_rejects_aggressive_transit_attacker_in_risk_band(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(100, "target", "the target", 25, 0, 0, "target.are"),
            200: MobileSource(
                200,
                "rolling attacker",
                "the route attacker",
                15,
                ACT_AGGRESSIVE,
                0,
                "target.are",
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Hazard passage", "target.are"),
            7002: RoomSource(7002, "Target room", "target.are"),
        },
        mob_resets=[
            MobReset(200, 7001, 1, ()),
            MobReset(100, 7002, 1, ()),
        ],
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)
    world.rooms[7001].exits["north"] = ExitSource("north", 7002, 0, -1)

    [candidate] = [
        candidate
        for candidate in rank_hunt_candidates(
            world,
            character_level=25,
            include_xp_only=True,
        )
        if candidate.mobile_vnum == 100
    ]

    assert not candidate.autonomous_safe
    assert (
        "route crosses an aggressive transit attacker inside the transit-risk band"
        in candidate.autonomy_rejections
    )


def test_autonomous_filter_keeps_route_program_hazard_above_aggro_cutoff(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(100, "target", "the target", 25, 0, 0, "target.are"),
            200: MobileSource(
                200,
                "soldier",
                "the route soldier",
                3,
                ACT_AGGRESSIVE,
                0,
                "target.are",
                programs=(
                    MobileProgram(
                        "greet_prog",
                        "100",
                        ("mpforce soldier mpkill $n",),
                    ),
                ),
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Barracks", "target.are"),
            7002: RoomSource(7002, "Target room", "target.are"),
        },
        mob_resets=[
            MobReset(200, 7001, 8, ()),
            MobReset(100, 7002, 1, ()),
        ],
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)
    world.rooms[7001].exits["north"] = ExitSource("north", 7002, 0, -1)

    [candidate] = [
        candidate
        for candidate in rank_hunt_candidates(
            world,
            character_level=25,
            include_xp_only=True,
        )
        if candidate.mobile_vnum == 100
    ]

    assert not candidate.autonomous_safe
    assert "route crosses a program-triggered attacker" in (
        candidate.autonomy_rejections
    )


def test_autonomous_filter_blocks_nonaggressive_route_program_hazard(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(100, "target", "the target", 25, 0, 0, "target.are"),
            200: MobileSource(
                200,
                "drunk",
                "the route drunk",
                3,
                0,
                0,
                "target.are",
                programs=(
                    MobileProgram(
                        "greet_prog",
                        "100",
                        ("mpkill $n",),
                    ),
                ),
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Street", "target.are"),
            7002: RoomSource(7002, "Target room", "target.are"),
        },
        mob_resets=[
            MobReset(200, 7001, 1, ()),
            MobReset(100, 7002, 1, ()),
        ],
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)
    world.rooms[7001].exits["north"] = ExitSource("north", 7002, 0, -1)

    [candidate] = [
        candidate
        for candidate in rank_hunt_candidates(
            world,
            character_level=25,
            include_xp_only=True,
        )
        if candidate.mobile_vnum == 100
    ]

    assert not candidate.autonomous_safe
    assert "route crosses a program-triggered attacker" in (
        candidate.autonomy_rejections
    )


def test_autonomous_filter_blocks_wandering_nonaggressive_program_hazard(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(100, "target", "the target", 25, 0, 0, "target.are"),
            200: MobileSource(
                200,
                "drunk",
                "the wandering drunk",
                3,
                0,
                0,
                "target.are",
                programs=(
                    MobileProgram(
                        "greet_prog",
                        "100",
                        ("mpforce drunk mpkill $n",),
                    ),
                ),
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Street", "target.are"),
            7002: RoomSource(7002, "Target room", "target.are"),
            7003: RoomSource(7003, "Inn", "target.are"),
        },
        mob_resets=[
            MobReset(200, 7003, 1, ()),
            MobReset(100, 7002, 1, ()),
        ],
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)
    world.rooms[7001].exits["north"] = ExitSource("north", 7002, 0, -1)
    world.rooms[7001].exits["east"] = ExitSource("east", 7003, 0, -1)
    world.rooms[7003].exits["west"] = ExitSource("west", 7001, 0, -1)

    [candidate] = [
        candidate
        for candidate in rank_hunt_candidates(
            world,
            character_level=25,
            include_xp_only=True,
        )
        if candidate.mobile_vnum == 100
    ]

    assert not candidate.autonomous_safe
    assert "route crosses a program-triggered attacker" in (
        candidate.autonomy_rejections
    )


def test_probabilistic_wandering_program_remains_explicit_route_risk() -> None:
    world = load_world_source(
        Path("runs/dd4-source/server/area"),
        include_all_areas=True,
    )
    candidates = rank_hunt_candidates(
        world,
        character_level=17,
        include_xp_only=True,
        include_level_ceiling_candidates=True,
        level_ceiling_offset=9,
        include_all_areas=True,
        character_max_hp=500,
        recall_origins={0: 3001},
    )

    assert any(
        "reachable program attacker: the drunk L2" in candidate.hazards
        and "a non-safe special mobile can reach the route"
        in candidate.autonomy_rejections
        for candidate in candidates
    )


def test_noncombat_special_route_crowd_does_not_block_target(monkeypatch) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(100, "target", "the target", 10, 0, 0, "target.are"),
            200: MobileSource(
                200,
                "fido",
                "the beastly fido",
                0,
                ACT_AGGRESSIVE,
                0,
                "target.are",
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Fido room", "target.are"),
            7002: RoomSource(7002, "Target room", "target.are"),
        },
        mob_resets=[
            MobReset(200, 7001, 15, ()),
            MobReset(100, 7002, 1, ()),
        ],
        mobile_specials={200: ("spec_fido",)},
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)
    world.rooms[7001].exits["north"] = ExitSource("north", 7002, 0, -1)

    [candidate] = rank_hunt_candidates(
        world,
        character_level=15,
        include_xp_only=True,
    )

    assert candidate.autonomous_safe
    assert candidate.route == ("north", "north")
    assert any(
        "noncombat route special" in hazard
        for hazard in candidate.hazards
    )
    assert not any(
        "large below-band aggressive crowd" in rejection
        for rejection in candidate.autonomy_rejections
    )


def test_noncombat_target_special_is_autonomous_safe(monkeypatch) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "secretary",
                "the secretary",
                12,
                0,
                0,
                "target.are",
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Office", "target.are"),
        },
        mob_resets=[MobReset(100, 7001, 1, ())],
        mobile_specials={100: ("spec_cast_hooker",)},
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)

    [candidate] = rank_hunt_candidates(
        world,
        character_level=16,
        include_xp_only=True,
    )

    assert candidate.autonomous_safe
    assert "target special: spec_cast_hooker" in candidate.hazards
    assert "target has special procedure spec_cast_hooker" not in (
        candidate.autonomy_rejections
    )


def test_candidate_uses_longer_route_around_large_below_band_crowd(monkeypatch) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(100, "target", "the target", 10, 0, 0, "target.are"),
            200: MobileSource(
                200,
                "soldier",
                "the route soldier",
                3,
                ACT_AGGRESSIVE,
                0,
                "target.are",
            ),
        },
        rooms={
            3001: RoomSource(
                3001,
                "Recall",
                "midgaard.are",
                exits={
                    "north": ExitSource("north", 7001, 0, -1),
                    "east": ExitSource("east", 7002, 0, -1),
                },
            ),
            7001: RoomSource(
                7001,
                "Barracks",
                "target.are",
                exits={"north": ExitSource("north", 7003, 0, -1)},
            ),
            7002: RoomSource(
                7002,
                "Side road",
                "target.are",
                exits={"east": ExitSource("east", 7004, 0, -1)},
            ),
            7003: RoomSource(7003, "Target room", "target.are"),
            7004: RoomSource(
                7004,
                "Side road",
                "target.are",
                exits={"north": ExitSource("north", 7003, 0, -1)},
            ),
        },
        mob_resets=[
            MobReset(200, 7001, 8, ()),
            MobReset(100, 7003, 1, ()),
        ],
    )

    [candidate] = rank_hunt_candidates(
        world,
        character_level=15,
        include_xp_only=True,
    )

    assert candidate.autonomous_safe
    assert candidate.route == ("east", "east", "north")
    assert not any(
        "large below-band aggressive crowd" in rejection
        for rejection in candidate.autonomy_rejections
    )


def test_held_nonweapon_does_not_count_as_a_dual_wielded_weapon(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "fanatic monk",
                "a fanatic monk",
                6,
                0,
                0,
                "target.are",
            ),
        },
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are"),
            7001: RoomSource(7001, "Reception", "target.are"),
        },
        objects={
            300: ObjectSource(300, "brochure", "a brochure", 8, (), 1),
        },
        mob_resets=[
            MobReset(100, 7001, 1, (300,), equipment=((17, 300),)),
        ],
    )
    world.rooms[3001].exits["north"] = ExitSource("north", 7001, 0, -1)

    candidate = rank_hunt_candidates(
        world,
        character_level=7,
        character_max_hp=123,
    )[0]

    assert candidate.status == "promising"
    assert candidate.equipped_weapons == ()
    assert candidate.estimated_peak_round_damage == 70
    assert candidate.autonomous_safe
    assert not any("source peak round" in hazard for hazard in candidate.hazards)


def test_candidate_ranking_rejects_a_mobile_holding_a_castable_staff(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "dd4tester.hunt_candidates.LOW_LEVEL_AREA_FILES",
        ("target.are",),
    )
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "priest",
                "the priest",
                6,
                0,
                0,
                "target.are",
            ),
        },
        objects={
            300: ObjectSource(
                300,
                "staff earthquake",
                "a staff of earthquake",
                ITEM_STAFF,
                (20, 2, 2),
                100,
                value_strings=("20", "2", "2", "earthquake"),
            ),
        },
        rooms={
            3001: RoomSource(
                3001,
                "Recall",
                "midgaard.are",
                exits={"north": ExitSource("north", 7001, 0, -1)},
            ),
            7001: RoomSource(7001, "Temple", "target.are"),
        },
        mob_resets=[
            MobReset(100, 7001, 1, (300,), equipment=((WEAR_HOLD, 300),)),
        ],
    )

    [candidate] = rank_hunt_candidates(
        world,
        character_level=7,
        character_max_hp=123,
        include_xp_only=True,
    )

    assert candidate.status == "reject"
    assert (
        "target equips a castable spell item: a staff of earthquake (earthquake)"
        in candidate.hazards
    )
    assert "target carries a source-castable spell item" in (
        candidate.autonomy_rejections
    )
    assert not candidate.autonomous_safe


def test_source_combat_readiness_is_a_soft_target_specific_hint() -> None:
    unassessed = source_combat_readiness(
        character_level=18,
        character_class="thief",
        target_level_range=(15, 19),
    )
    ready = source_combat_readiness(
        character_level=18,
        character_class="thief",
        known_skills=("Backstab", "Second Attack", "Disarm"),
        target_level_range=(15, 19),
        equipped_weapon_count=1,
    )
    unarmed_ready = source_combat_readiness(
        character_level=18,
        character_class="thief",
        known_skills=("backstab", "second attack", "disarm"),
        target_level_range=(15, 19),
    )
    level_filtered = source_combat_readiness(
        character_level=18,
        character_class="thief",
        known_skills=("backstab", "second attack", "disarm"),
        known_skill_levels={"backstab": 0},
        target_level_range=(15, 19),
    )

    assert unassessed == ("unassessed", 0)
    assert ready[0] == "direct=backstab; passive=second attack; control=disarm"
    assert ready[1] > unarmed_ready[1] > 0
    assert "backstab" not in level_filtered[0]


def test_source_combat_readiness_labels_thief_controls_without_direct_damage() -> None:
    readiness = source_combat_readiness(
        character_level=18,
        character_class="thief",
        known_skills=("dirt kick", "trip"),
        target_level_range=(15, 19),
    )

    assert readiness == ("control=dirt kick,trip", 0)


def test_source_combat_readiness_labels_shifter_form_setup_separately() -> None:
    readiness = source_combat_readiness(
        character_level=18,
        character_class="shifter",
        known_skills=("morph", "snake form"),
        target_level_range=(16, 18),
    )

    assert readiness == ("setup=morph,snake form", 0)


def test_source_combat_output_uses_the_audited_mage_formula() -> None:
    output = source_combat_output_estimate(
        character_level=18,
        character_class="Mage",
        known_skills=("burning hands", "magic missile"),
        known_skill_levels={"burning hands": 31},
    )

    assert output == SourceCombatOutput(
        action="burning hands",
        minimum_damage=14,
        expected_damage=51,
        maximum_damage=74,
        resource="mana",
        resource_cost=15,
        conservative_damage=40,
        source_reference="magic.c:spell_burning_hands",
    )


def test_source_combat_output_uses_base_psionic_agitation() -> None:
    output = source_combat_output_estimate(
        character_level=30,
        character_class="psionic",
        known_skills=("agitation",),
        known_skill_levels={"agitation": 45},
    )

    assert output == SourceCombatOutput(
        action="agitation",
        minimum_damage=15,
        expected_damage=38,
        maximum_damage=62,
        resource="mana",
        resource_cost=10,
        conservative_damage=30,
        source_reference="magic.c:spell_agitation",
    )


def test_source_combat_output_models_ranger_shoot_as_one_shot_opening() -> None:
    output = source_combat_output_estimate(
        character_level=20,
        character_class="ranger",
        known_skills=("shoot", "second shot", "third shot", "kick"),
        known_skill_levels={
            "shoot": 80,
            "second shot": 50,
            "third shot": 25,
            "kick": 80,
        },
        weapon_damage_range=None,
        ranged_weapon_damage_range=(2, 4),
        ranged_weapon_vnum=18001,
    )

    assert output == SourceCombatOutput(
        action="kick",
        minimum_damage=11,
        expected_damage=16,
        maximum_damage=30,
        resource="actions",
        resource_cost=0,
        conservative_damage=12,
        source_reference="fight.c:do_kick",
        opening_action="shoot",
        opening_min_damage=2,
        opening_expected_damage=4,
        opening_max_damage=12,
        opening_conservative_damage=3,
        opening_source_reference=(
            "fight.c:do_shoot/one_hit; object vnum 18001"
        ),
    )


def test_source_combat_output_does_not_invent_ranger_shoot_without_a_bow() -> None:
    output = source_combat_output_estimate(
        character_level=20,
        character_class="ranger",
        known_skills=("shoot", "kick"),
        known_skill_levels={"shoot": 80, "kick": 80},
    )

    assert output is not None
    assert output.opening_action is None


@pytest.mark.parametrize(
    ("character_class", "character_subclass", "skill", "expected"),
    [
        (
            "mage",
            "necromancer",
            "harm",
            SourceCombatOutput(
                action="harm",
                minimum_damage=50,
                expected_damage=75,
                maximum_damage=100,
                resource="mana",
                resource_cost=35,
                conservative_damage=60,
                source_reference="magic.c:spell_harm",
            ),
        ),
        (
            "cleric",
            "druid",
            "wither",
            SourceCombatOutput(
                action="wither",
                minimum_damage=60,
                expected_damage=165,
                maximum_damage=270,
                resource="mana",
                resource_cost=20,
                conservative_damage=132,
                source_reference="magic.c:spell_wither",
            ),
        ),
        (
            "warrior",
            "knight",
            "flamestrike",
            SourceCombatOutput(
                action="flamestrike",
                minimum_damage=90,
                expected_damage=135,
                maximum_damage=180,
                resource="mana",
                resource_cost=20,
                conservative_damage=108,
                source_reference="magic.c:spell_flamestrike",
            ),
        ),
        (
            "brawler",
            "monk",
            "agitation",
            SourceCombatOutput(
                action="agitation",
                minimum_damage=15,
                expected_damage=38,
                maximum_damage=62,
                resource="mana",
                resource_cost=10,
                conservative_damage=30,
                source_reference="magic.c:spell_agitation",
            ),
        ),
    ],
)
def test_source_combat_output_uses_source_legal_subclass_spell(
    character_class: str,
    character_subclass: str,
    skill: str,
    expected: SourceCombatOutput,
) -> None:
    output = source_combat_output_estimate(
        character_level=30,
        character_class=character_class,
        character_subclass=character_subclass,
        known_skills=(skill,),
        known_skill_levels={skill: 45},
    )

    assert output == expected


def test_source_combat_output_rejects_subclass_spell_on_wrong_subclass() -> None:
    assert source_combat_output_estimate(
        character_level=30,
        character_class="mage",
        character_subclass="warlock",
        known_skills=("harm",),
        known_skill_levels={"harm": 45},
    ) is None


def test_source_combat_output_uses_werewolf_natural_attack() -> None:
    output = source_combat_output_estimate(
        character_level=30,
        character_class="shifter",
        character_subclass="werewolf",
        known_skills=("wolfbite", "ravage"),
        known_skill_levels={"wolfbite": 50, "ravage": 45},
    )

    assert output == SourceCombatOutput(
        action="wolfbite",
        minimum_damage=90,
        expected_damage=120,
        maximum_damage=150,
        resource="actions",
        resource_cost=0,
        conservative_damage=96,
        source_reference="sft.c:do_wolfbite",
    )


def test_source_combat_output_uses_vampire_suck_and_weapon_cycle() -> None:
    output = source_combat_output_estimate(
        character_level=30,
        character_class="shifter",
        character_subclass="vampire",
        known_skills=("suck",),
        known_skill_levels={"suck": 50},
        weapon_damage_range=(5, 12),
        weapon_vnum=18002,
        player_damroll=7,
    )

    assert output == SourceCombatOutput(
        action="suck",
        minimum_damage=12,
        expected_damage=26,
        maximum_damage=47,
        resource="actions",
        resource_cost=0,
        conservative_damage=20,
        source_reference=(
            "skill.c:do_suck; fight.c:one_hit; "
            "plus fight.c:one_hit/multi_hit"
        ),
    )


def test_source_combat_output_models_vampire_lunge_as_bounded_opening() -> None:
    output = source_combat_output_estimate(
        character_level=30,
        character_class="shifter",
        character_subclass="vampire",
        known_skills=("suck", "lunge", "double lunge"),
        known_skill_levels={
            "suck": 50,
            "lunge": 60,
            "double lunge": 40,
        },
        weapon_damage_range=(5, 12),
        weapon_vnum=18002,
        player_damroll=7,
    )

    assert output == SourceCombatOutput(
        action="suck",
        minimum_damage=12,
        expected_damage=26,
        maximum_damage=47,
        resource="actions",
        resource_cost=0,
        conservative_damage=20,
        source_reference=(
            "skill.c:do_suck; fight.c:one_hit; "
            "plus fight.c:one_hit/multi_hit"
        ),
        opening_action="lunge",
        opening_min_damage=18,
        opening_expected_damage=19,
        opening_max_damage=56,
        opening_conservative_damage=15,
        opening_source_reference=(
            "fight.c:do_lunge/multi_hit/one_hit; object vnum 18002"
        ),
    )


def test_source_combat_output_rejects_lunge_on_wrong_base_class() -> None:
    assert source_combat_output_estimate(
        character_level=30,
        character_class="mage",
        character_subclass="vampire",
        known_skills=("suck", "lunge"),
        known_skill_levels={"suck": 100, "lunge": 100},
    ) is None


def test_source_combat_output_applies_vampire_rage_adjustment_when_observed() -> None:
    high_rage = source_combat_output_estimate(
        character_level=30,
        character_class="shifter",
        character_subclass="vampire",
        known_skills=("suck",),
        known_skill_levels={"suck": 100},
        weapon_damage_range=(10, 10),
        player_damroll=0,
        player_rage=80,
        player_max_rage=100,
    )
    low_rage = source_combat_output_estimate(
        character_level=30,
        character_class="shifter",
        character_subclass="vampire",
        known_skills=("suck",),
        known_skill_levels={"suck": 100},
        weapon_damage_range=(10, 10),
        player_damroll=0,
        player_rage=10,
        player_max_rage=100,
    )

    assert high_rage is not None
    assert low_rage is not None
    assert high_rage.expected_damage == 26
    assert low_rage.expected_damage == 24


def test_source_combat_output_uses_vampire_unarmed_fallback() -> None:
    output = source_combat_output_estimate(
        character_level=30,
        character_class="shifter",
        character_subclass="vampire",
        known_skills=("suck",),
        known_skill_levels={"suck": 100},
    )

    assert output == SourceCombatOutput(
        action="suck",
        minimum_damage=1,
        expected_damage=3,
        maximum_damage=6,
        resource="actions",
        resource_cost=0,
        conservative_damage=2,
        source_reference="skill.c:do_suck; fight.c:one_hit",
    )


def test_source_combat_output_rejects_werewolf_attack_on_wrong_subclass() -> None:
    assert source_combat_output_estimate(
        character_level=30,
        character_class="shifter",
        character_subclass="vampire",
        known_skills=("wolfbite",),
        known_skill_levels={"wolfbite": 50},
    ) is None


def test_source_combat_output_uses_brawler_punch_formula() -> None:
    output = source_combat_output_estimate(
        character_level=20,
        character_class="brawler",
        known_skills=("punch",),
        known_skill_levels={"punch": 45},
    )

    assert output == SourceCombatOutput(
        action="punch",
        minimum_damage=11,
        expected_damage=30,
        maximum_damage=50,
        resource="actions",
        resource_cost=0,
        conservative_damage=24,
        source_reference="skill.c:do_punch",
    )


def test_source_combat_output_includes_brawler_second_punch_when_observed() -> None:
    output = source_combat_output_estimate(
        character_level=20,
        character_class="brawler",
        known_skills=("punch", "second punch"),
        known_skill_levels={"punch": 45, "second punch": 45},
    )

    assert output == SourceCombatOutput(
        action="punch",
        minimum_damage=11,
        expected_damage=52,
        maximum_damage=110,
        resource="actions",
        resource_cost=0,
        conservative_damage=41,
        source_reference="skill.c:do_punch; plus skill.c:do_punch/second_punch",
    )


def test_source_combat_output_uses_martial_artist_atemi_formula() -> None:
    output = source_combat_output_estimate(
        character_level=30,
        character_class="brawler",
        character_subclass="martial artist",
        known_skills=("atemi",),
        known_skill_levels={"atemi": 45},
    )

    assert output == SourceCombatOutput(
        action="atemi",
        minimum_damage=45,
        expected_damage=45,
        maximum_damage=45,
        resource="actions",
        resource_cost=0,
        conservative_damage=36,
        source_reference="skill.c:do_atemi and atemi",
    )


def test_source_combat_output_rejects_atemi_on_wrong_subclass() -> None:
    assert source_combat_output_estimate(
        character_level=30,
        character_class="brawler",
        character_subclass="monk",
        known_skills=("atemi",),
        known_skill_levels={"atemi": 45},
    ) is None


def test_source_combat_output_uses_observed_weapon_and_multihit_formula() -> None:
    output = source_combat_output_estimate(
        character_level=20,
        character_class="warrior",
        known_skills=(
            "enhanced damage",
            "second attack",
            "third attack",
            "enhanced swiftness",
        ),
        known_skill_levels={
            "enhanced damage": 64,
            "second attack": 56,
            "third attack": 40,
            "enhanced swiftness": 80,
        },
        weapon_damage_range=(5, 12),
        weapon_vnum=10014,
        player_damroll=7,
        player_swiftness=5,
    )

    assert output == SourceCombatOutput(
        action="weapon strike",
        minimum_damage=15,
        expected_damage=47,
        maximum_damage=100,
        resource="actions",
        resource_cost=0,
        conservative_damage=37,
        source_reference=(
            "fight.c:one_hit/multi_hit; object vnum 10014"
        ),
    )


def test_source_combat_output_uses_counterbalance_only_for_verified_weapon() -> None:
    common = dict(
        character_level=20,
        character_class="warrior",
        known_skills=("counterbalance",),
        known_skill_levels={"counterbalance": 50},
        weapon_damage_range=(5, 12),
        weapon_vnum=10014,
        player_damroll=7,
    )

    unverified = source_combat_output_estimate(
        **common,
        weapon_counterbalanced=False,
    )
    verified = source_combat_output_estimate(
        **common,
        weapon_counterbalanced=True,
    )

    assert unverified == SourceCombatOutput(
        action="weapon strike",
        minimum_damage=12,
        expected_damage=15,
        maximum_damage=19,
        resource="actions",
        resource_cost=0,
        conservative_damage=12,
        source_reference="fight.c:one_hit/multi_hit; object vnum 10014",
    )
    assert verified == SourceCombatOutput(
        action="weapon strike",
        minimum_damage=12,
        expected_damage=23,
        maximum_damage=38,
        resource="actions",
        resource_cost=0,
        conservative_damage=18,
        source_reference=(
            "fight.c:one_hit/multi_hit; object vnum 10014; "
            "plus fight.c:counterbalance"
        ),
    )


def test_source_combat_output_does_not_invent_unobserved_weapon_skills() -> None:
    output = source_combat_output_estimate(
        character_level=20,
        character_class="warrior",
        known_skills=("second attack", "enhanced damage"),
        known_skill_levels={"enhanced damage": 64},
        weapon_damage_range=(5, 12),
        player_damroll=7,
    )

    assert output == SourceCombatOutput(
        action="weapon strike",
        minimum_damage=15,
        expected_damage=20,
        maximum_damage=25,
        resource="actions",
        resource_cost=0,
        conservative_damage=16,
        source_reference="fight.c:one_hit/multi_hit",
    )


def test_source_combat_output_models_learned_kick_as_repeatable_damage() -> None:
    output = source_combat_output_estimate(
        character_level=20,
        character_class="warrior",
        known_skills=("kick",),
        known_skill_levels={"kick": 80},
    )

    assert output == SourceCombatOutput(
        action="kick",
        minimum_damage=11,
        expected_damage=16,
        maximum_damage=30,
        resource="actions",
        resource_cost=0,
        conservative_damage=12,
        source_reference="fight.c:do_kick",
    )


@pytest.mark.parametrize("body_form_flags", [None, BODY_NO_HEAD, BODY_HUGE])
def test_source_combat_output_requires_headbutt_anatomy_evidence(
    body_form_flags,
) -> None:
    assert source_combat_output_estimate(
        character_level=20,
        character_class="warrior",
        known_skills=("headbutt",),
        known_skill_levels={"headbutt": 80},
        target_body_form_flags=body_form_flags,
    ) is None


def test_source_combat_output_models_headbutt_and_second_headbutt() -> None:
    output = source_combat_output_estimate(
        character_level=20,
        character_class="warrior",
        known_skills=("headbutt", "second headbutt"),
        known_skill_levels={"headbutt": 80, "second headbutt": 50},
        target_body_form_flags=0,
    )

    assert output == SourceCombatOutput(
        action="headbutt",
        minimum_damage=11,
        expected_damage=50,
        maximum_damage=140,
        resource="actions",
        resource_cost=0,
        conservative_damage=40,
        source_reference=(
            "fight.c:do_headbutt/one_hit; plus "
            "fight.c:do_headbutt/second_headbutt"
        ),
    )


def test_source_combat_output_models_learned_knife_toss_for_thief() -> None:
    output = source_combat_output_estimate(
        character_level=24,
        character_class="thief",
        known_skills=("knife toss",),
        known_skill_levels={"knife toss": 75},
    )

    assert output == SourceCombatOutput(
        action="knife toss",
        minimum_damage=13,
        expected_damage=18,
        maximum_damage=36,
        resource="actions",
        resource_cost=0,
        conservative_damage=14,
        source_reference="fight.c:do_knife_toss",
    )


def test_source_combat_output_models_circle_only_with_a_piercing_weapon() -> None:
    output = source_combat_output_estimate(
        character_level=20,
        character_class="thief",
        known_skills=("circle", "second circle", "enhanced damage"),
        known_skill_levels={
            "circle": 80,
            "second circle": 30,
            "enhanced damage": 64,
        },
        weapon_damage_range=(5, 12),
        weapon_vnum=10014,
        weapon_damage_type=2,
        player_damroll=7,
    )

    assert output == SourceCombatOutput(
        action="circle",
        minimum_damage=15,
        expected_damage=50,
        maximum_damage=99,
        resource="actions",
        resource_cost=0,
        conservative_damage=40,
        source_reference=(
            "fight.c:do_circle/one_hit; object vnum 10014; "
            "plus fight.c:one_hit/multi_hit"
        ),
    )
    assert source_combat_output_estimate(
        character_level=20,
        character_class="thief",
        known_skills=("circle",),
        known_skill_levels={"circle": 80},
        weapon_damage_range=(5, 12),
        weapon_damage_type=3,
    ) == SourceCombatOutput(
        action="weapon strike",
        minimum_damage=5,
        expected_damage=8,
        maximum_damage=12,
        resource="actions",
        resource_cost=0,
        conservative_damage=6,
        source_reference="fight.c:one_hit/multi_hit",
    )


def test_source_combat_output_requires_a_chained_weapon_for_smithy_hurl() -> None:
    arguments = dict(
        character_level=20,
        character_class="smithy",
        known_skills=("hurl",),
        known_skill_levels={"hurl": 50},
        weapon_damage_range=(5, 12),
        weapon_vnum=3021,
    )

    ordinary = source_combat_output_estimate(**arguments)
    assert ordinary is not None
    assert ordinary.action == "weapon strike"

    hurl = source_combat_output_estimate(
        **arguments,
        weapon_chained=True,
    )
    assert hurl == SourceCombatOutput(
        action="hurl",
        minimum_damage=5,
        expected_damage=28,
        maximum_damage=62,
        resource="actions",
        resource_cost=0,
        conservative_damage=22,
        source_reference=(
            "fight.c:do_hurl/weapon; object vnum 3021; "
            "plus fight.c:one_hit/multi_hit"
        ),
    )


def test_source_combat_output_keeps_backstab_as_a_one_shot_opening_budget() -> None:
    output = source_combat_output_estimate(
        character_level=20,
        character_class="thief",
        known_skills=("backstab", "enhanced damage"),
        known_skill_levels={"backstab": 80, "enhanced damage": 64},
        weapon_damage_range=(5, 12),
        weapon_vnum=10014,
        weapon_damage_type=2,
        player_damroll=7,
    )

    assert output == SourceCombatOutput(
        action="weapon strike",
        minimum_damage=15,
        expected_damage=20,
        maximum_damage=25,
        resource="actions",
        resource_cost=0,
        conservative_damage=16,
        source_reference=(
            "fight.c:one_hit/multi_hit; object vnum 10014"
        ),
        opening_action="backstab",
        opening_min_damage=60,
        opening_expected_damage=64,
        opening_max_damage=100,
        opening_conservative_damage=51,
        opening_source_reference=(
            "fight.c:do_backstab/one_hit; object vnum 10014"
        ),
    )


def test_source_combat_output_includes_observed_double_backstab() -> None:
    output = source_combat_output_estimate(
        character_level=20,
        character_class="thief",
        known_skills=("backstab", "double backstab", "enhanced damage"),
        known_skill_levels={
            "backstab": 80,
            "double backstab": 50,
            "enhanced damage": 64,
        },
        weapon_damage_range=(5, 12),
        weapon_vnum=10014,
        weapon_damage_type=2,
        player_damroll=7,
    )

    assert output is not None
    assert output.opening_action == "backstab"
    assert output.opening_min_damage == 60
    assert output.opening_expected_damage == 96
    assert output.opening_max_damage == 200
    assert output.opening_conservative_damage == 76
    assert output.opening_source_reference == (
        "fight.c:do_backstab/one_hit; plus "
        "fight.c:multi_hit/double_backstab; object vnum 10014"
    )


@pytest.mark.parametrize(
    ("character_class", "known_skills"),
    [
        ("warrior", ("kick", "enhanced damage")),
        ("thief", ("backstab", "disarm")),
        ("mage", ("armor", "fly")),
    ],
)
def test_source_combat_output_stays_unassessed_without_audited_spell(
    character_class: str,
    known_skills: tuple[str, ...],
) -> None:
    assert source_combat_output_estimate(
        character_level=18,
        character_class=character_class,
        known_skills=known_skills,
    ) is None


def test_candidate_ranking_records_known_class_combat_readiness() -> None:
    world = WorldSource(
        mobiles={
            100: MobileSource(
                100,
                "frontier target",
                "a frontier target",
                15,
                0,
                0,
                "frontier.are",
            )
        },
        rooms={
            3001: RoomSource(
                3001,
                "Recall",
                "midgaard.are",
                exits={"north": ExitSource("north", 7001, 0, -1)},
            ),
            7001: RoomSource(7001, "Frontier room", "frontier.are"),
        },
        mob_resets=[MobReset(100, 7001, 1, ())],
    )

    [candidate] = rank_hunt_candidates(
        world,
        character_level=18,
        character_class="thief",
        known_skills=("backstab", "second attack"),
        include_xp_only=True,
        include_all_areas=True,
    )

    assert candidate.status == "promising"
    assert candidate.combat_readiness == "direct=backstab; passive=second attack"
    assert candidate.combat_readiness_bonus > 0
    assert candidate.autonomous_safe
