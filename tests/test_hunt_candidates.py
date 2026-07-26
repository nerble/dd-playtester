from dataclasses import replace
from pathlib import Path

from dd4tester.hunt_candidates import (
    ExitSource,
    MobileSource,
    MobReset,
    ObjectSource,
    RoomSource,
    WorldSource,
    load_object_sources,
    parse_area_file,
    rank_hunt_candidates,
)


FIXTURE = Path(__file__).parent / "fixtures" / "hunt_area.are"


def test_area_parser_connects_mob_resets_to_direct_and_contained_loot() -> None:
    area = parse_area_file(FIXTURE)

    assert area.mobiles[100].level == 3
    assert area.mobiles[100].aggressive is True
    assert area.objects[200].source_cost == 100
    assert area.objects[200].weight == 1
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
    assert not any("wanderer" in hazard for hazard in candidate.hazards)


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

    loot_candidates = rank_hunt_candidates(world, character_level=10)
    xp_candidates = rank_hunt_candidates(
        world,
        character_level=10,
        include_xp_only=True,
    )

    assert [candidate.target for candidate in loot_candidates] == ["a cellar rat"]
    assert {candidate.target for candidate in xp_candidates} == {
        "a cellar rat",
        "the dangerous guard",
    }


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
        character_level=10,
        character_max_hp=50,
    )[0]

    assert candidate.status == "reject"
    assert "source peak round 60 >= character max HP 50" in candidate.hazards


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
    assert not any("source peak round" in hazard for hazard in candidate.hazards)
