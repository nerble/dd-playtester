from dataclasses import replace
from pathlib import Path

from dd4tester.fastwalks import route_named
from dd4tester.hunt_candidates import (
    ACT_AGGRESSIVE,
    ACT_DIE_IF_MASTER_GONE,
    AFF_CONFUSION,
    ITEM_FOOD,
    ITEM_MONEY,
    ITEM_STAFF,
    ExitSource,
    MobileSource,
    MobReset,
    ObjectSource,
    RoomSource,
    RoomObjectReset,
    WorldSource,
    money_value,
    castable_spell_names,
    potion_spell_names,
    _route_preflight_metadata,
    _mobile_critical_hit_damage,
    _mobile_peak_round_damage,
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


def test_armed_mobile_damage_keeps_ordinary_peak_separate_from_critical_burst() -> None:
    assert _mobile_peak_round_damage(
        14,
        wielding=True,
        dual_wielding=False,
    ) == 180
    assert _mobile_critical_hit_damage(14, wielding=True) == 72


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
