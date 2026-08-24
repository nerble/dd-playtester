from pathlib import Path
from types import SimpleNamespace

import pytest

from dd4tester.hunt_candidates import _shortest_paths_from, load_world_source
from dd4tester.quests import (
    GOLDMOON_QUESTMASTER_ROUTE_FROM_RECALL,
    QUESTMASTER_ROUTE_FROM_RECALL,
    quest_mobile_is_source_eligible,
    quest_object_keyword,
    quest_points_required_for_advance,
    quest_points_shortfall_for_advance,
    quest_target_maximum_level_offset,
    questmaster_route_for_level,
    snapshot_quest_status,
)


def test_snapshot_quest_status_normalizes_active_kill_and_completion() -> None:
    active = snapshot_quest_status(
        {
            "active": 1,
            "complete": 0,
            "type": "kill",
            "mob_vnum": 4517,
            "room_vnum": 4514,
        }
    )
    complete = snapshot_quest_status(
        {"active": 1, "type": "kill", "mob_vnum": -1}
    )

    assert active.needs_target_run is True
    assert active.mob_vnum == 4517
    assert complete.complete is True
    assert complete.needs_target_run is False


def test_snapshot_quest_status_treats_live_retrieve_type_as_actionable() -> None:
    quest = snapshot_quest_status(
        {
            "active": 1,
            "complete": 0,
            "type": "retrieve",
            "object_vnum": 78,
            "room_vnum": 285,
        }
    )

    assert quest.kind == "retrieve"
    assert quest.needs_target_run is True


def test_questmaster_routes_cover_junior_and_post_25_bands() -> None:
    assert questmaster_route_for_level(25) == QUESTMASTER_ROUTE_FROM_RECALL
    assert questmaster_route_for_level(26) == GOLDMOON_QUESTMASTER_ROUTE_FROM_RECALL
    assert "open south" in questmaster_route_for_level(100)

    with pytest.raises(ValueError, match="levels 1 through 100"):
        questmaster_route_for_level(101)


@pytest.mark.parametrize(
    ("level", "required"),
    ((28, 0), (29, 1), (49, 200), (79, 500), (99, 1000), (100, 0)),
)
def test_quest_point_gates_match_update_source(
    level: int,
    required: int,
) -> None:
    assert quest_points_required_for_advance(level) == required


def test_quest_point_shortfall_is_never_negative() -> None:
    assert quest_points_shortfall_for_advance(29, 0) == 1
    assert quest_points_shortfall_for_advance(29, 3) == 0


@pytest.mark.parametrize(
    ("level", "maximum_offset"),
    (
        (1, 4),
        (19, 4),
        (20, 9),
        (49, 9),
        (50, 14),
        (79, 14),
        (80, 19),
        (100, 19),
    ),
)
def test_quest_target_level_offsets_match_generate_quest_bands(
    level: int,
    maximum_offset: int,
) -> None:
    assert quest_target_maximum_level_offset(level) == maximum_offset


def test_quest_mobile_source_eligibility_mirrors_generate_quest_exclusions() -> None:
    assert quest_mobile_is_source_eligible(SimpleNamespace(act_flags=0)) is True
    assert quest_mobile_is_source_eligible(SimpleNamespace(act_flags=1 << 9)) is False
    assert quest_mobile_is_source_eligible(
        SimpleNamespace(act_flags=0),
        is_shopkeeper=True,
    ) is False


def test_goldmoon_route_matches_the_checked_in_source_graph() -> None:
    world = load_world_source(
        Path("runs/dd4-source/server/area"),
        include_all_areas=True,
    )
    path = _shortest_paths_from(world.rooms, 3001)[10024]

    assert path[0] == GOLDMOON_QUESTMASTER_ROUTE_FROM_RECALL


def test_generated_quest_object_uses_a_distinct_source_keyword() -> None:
    world = SimpleNamespace(
        objects={
            75: SimpleNamespace(keywords="coin amaros"),
            76: SimpleNamespace(keywords="amulet thagg ivory"),
        }
    )

    assert quest_object_keyword(world, 75) == "amaros"
    assert quest_object_keyword(world, 76) == "thagg"
    assert quest_object_keyword(world, 9999) is None
