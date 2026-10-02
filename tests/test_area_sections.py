from dd4tester.hunt_candidates import _section_ranges, parse_area_file


def test_ascii_maps_do_not_end_mobile_or_room_sections(tmp_path):
    source = tmp_path / "mapped.are"
    source.write_text(
        """#AREA Tester~ Mapped Rooms~
20 60 0 100
#MOBILES
#10
guard~
a guard~
A guard stands here.~
The guard carries a map:
   #################
   #*/----\\*| room #
   #################
~
1 0 -1000 S
20 0 2 0d0+0 0d0+0
0 0
8 8 1
#0
#ROOMS
#20
Map Chamber~
A chamber with a map.~
0 8192 1
E
map~
   #################
   #***************#
   #HHHHHHH*/----\\*#
   #################
~
D3
A corridor.~
door~
2 50 21
S
#21
Next Chamber~
A second room.~
0 0 1
D1
~
door~
2 50 20
S
#0
#RESETS
M 0 10 1 21
D 0 20 3 2
S
#SHOPS
0
#SPECIALS
S
#$
""",
        encoding="ascii",
    )
    area = parse_area_file(source)
    assert set(area.mobiles) == {10}
    assert set(area.rooms) == {20, 21}
    assert area.rooms[20].no_recall
    door = area.rooms[20].exits["west"]
    assert door.destination == 21
    assert door.closed and door.locked and door.key_vnum == 50
    assert area.mob_resets[0].mobile_vnum == 10
    assert area.mob_resets[0].room_vnum == 21


def test_server_sections_bound_each_other_but_map_art_does_not():
    lines = [
        "#AREA Author~ Area~", "0 100 0 100", "#ROOMS", "#20",
        "#************#", "  #######", "#0", "#ROOMS_AMBIENT",
        "S", "#EXITS_SFX", "S", "#RESETS", "S", "#$",
    ]
    sections = _section_ranges(lines)
    assert sections["#ROOMS"] == (3, 7)
    assert sections["#ROOMS_AMBIENT"] == (8, 9)
    assert sections["#RESETS"] == (12, 13)
    assert "#20" not in sections
    assert "#######" not in sections


def test_quest_route_diagnosis_distinguishes_locked_access_without_opening_it():
    from dd4tester.campaign import _quest_unavailable_route_reason
    from dd4tester.hunt_candidates import ExitSource, RoomSource, WorldSource, _shortest_paths_from

    world = WorldSource()
    world.rooms = {
        3001: RoomSource(3001, "Recall", "example.are",
                         {"east": ExitSource("east", 20, 7, 50)}),
        20: RoomSource(20, "Target", "example.are"),
        21: RoomSource(21, "Disconnected", "example.are"),
    }
    reason = _quest_unavailable_route_reason(world, 20)
    assert reason.startswith("source route safety gates require registered locked-door access")
    assert "key VNUMs 50" in reason
    assert 20 not in _shortest_paths_from(world.rooms, 3001)
    assert _quest_unavailable_route_reason(world, 21) == (
        "the source graph has no route from recall to quest room 21"
    )
