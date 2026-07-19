from pathlib import Path

from dd4tester.hunt_candidates import (
    WorldSource,
    parse_area_file,
    rank_hunt_candidates,
)


FIXTURE = Path(__file__).parent / "fixtures" / "hunt_area.are"


def test_area_parser_connects_mob_resets_to_direct_and_contained_loot() -> None:
    area = parse_area_file(FIXTURE)

    assert area.mobiles[100].level == 3
    assert area.mobiles[100].aggressive is True
    assert area.objects[200].source_cost == 100
    assert area.rooms[3001].exits["north"].destination == 3002
    assert area.mob_resets[1].object_vnums == (200, 201)
    assert area.container_contents[201] == [202]


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
    assert candidate.source_instance_limit == 2
    assert candidate.boot_kills == 2
    assert candidate.loot == ("a rusty sword",)
    assert candidate.contained_coins == 50
    assert "route: the dangerous guard L8 in 3002" in candidate.hazards
    assert any("faster unoccupied reset" in hazard for hazard in candidate.hazards)
