from pathlib import Path
from types import SimpleNamespace

import pytest

from dd4tester.hunt_candidates import _shortest_paths_from, load_world_source
from dd4tester.quests import (
    GOLDMOON_QUESTMASTER_ROUTE_FROM_RECALL,
    QUESTMASTER_ROUTE_FROM_RECALL,
    fame_from_state,
    recall_origins_from_state,
    recall_point_for_index,
    recall_point_for_name,
    recall_points_for_purchase,
    quest_mobile_is_source_eligible,
    quest_object_keyword,
    quest_points_required_for_advance,
    quest_points_shortfall_for_advance,
    quest_fame_recovery_status,
    quest_request_blocker,
    quest_request_fame_allowed,
    quest_target_maximum_level_offset,
    questmaster_route_for_level,
    next_recall_point_to_buy,
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


@pytest.mark.parametrize(
    ("state", "allowed", "blocker"),
    (
        ({"stats": {"fame": "0"}}, True, None),
        ({"stats": {"fame": "-12"}}, False,
         "DD4 rejects new quest requests while fame is below zero"),
        ({}, False, "live fame is unavailable; do not request a quest"),
        (
            {"stats": {"fame": "0"}, "quest_status": {"nextquest": 3}},
            True,
            "quest cooldown has 3 minute(s) remaining",
        ),
    ),
)
def test_fresh_quest_request_requires_current_nonnegative_fame(
    state: dict[str, object],
    allowed: bool,
    blocker: str | None,
) -> None:
    assert quest_request_fame_allowed(state) is allowed
    assert quest_request_blocker(state) == blocker


def test_quest_fame_status_distinguishes_kill_from_object_rewards() -> None:
    state = {"stats": {"fame": 0}}
    negative_state = {"stats": {"fame": -12}}
    kill = snapshot_quest_status(
        {"active": 1, "complete": 1, "type": "kill", "mob_vnum": -1}
    )
    active_kill = snapshot_quest_status(
        {"active": 1, "complete": 0, "type": "kill", "mob_vnum": 4517}
    )
    object_quest = snapshot_quest_status(
        {"active": 1, "complete": 1, "type": "object", "object_vnum": 78}
    )

    assert fame_from_state(state) == 0
    assert "positive fuzzy fame reward" in quest_fame_recovery_status(
        state,
        quest=kill,
    )
    assert "award no fame" in quest_fame_recovery_status(
        state,
        quest=object_quest,
    )
    assert "active kill quest can award" in quest_fame_recovery_status(
        negative_state,
        quest=active_kill,
    )


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


def test_recall_point_registry_matches_source_slots_and_destinations() -> None:
    points = recall_points_for_purchase()

    assert len(points) == 15
    assert points[0].index == 2
    assert points[0].cost == 1000
    assert points[0].room_vnum == 28003
    assert points[0].name == "Draagdim"
    assert recall_point_for_index(1) is None
    assert recall_point_for_index(14).name == "Ota'ar Dar"
    assert recall_point_for_name("Ota'ar Dar").index == 14
    assert recall_point_for_name("unknown") is None


def test_recall_origins_from_state_keeps_only_source_known_destinations() -> None:
    assert recall_origins_from_state(
        {
            "recall_points": [
                {"index": 2, "name": "Draagdim"},
                {"index": 999, "name": "unknown"},
            ],
            "current_recall": 12,
        }
    ) == {0: 3001, 2: 28003, 12: 21500}


def test_next_recall_point_to_buy_prefers_the_most_valuable_missing_point() -> None:
    point = next_recall_point_to_buy(
        [{"index": 2}, {"index": 9}],
        600,
        character_level=25,
    )

    assert point is not None
    assert point.index == 4
    assert point.cost == 500
    assert point.name == "Anon"


def test_next_recall_point_to_buy_requires_a_live_list_and_level_25() -> None:
    assert (
        next_recall_point_to_buy(None, 1000, character_level=25)
        is None
    )
    assert (
        next_recall_point_to_buy([], 1000, character_level=24)
        is None
    )


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
