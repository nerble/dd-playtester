import json
from copy import deepcopy

import pytest

from dd4tester.campaign import (
    _campaign_segment_end_state,
    _repair_campaign_xp_loss_total,
)


def _reconnect_states():
    return (
        {
            "name": "Example",
            "level": 24,
            "xp": 333_643,
            "progress_source": "gmcp",
            "campaign_xp_loss_total": 1_640,
            "campaign_research_results": {"previous-hunt": {"viable": False}},
        },
        {
            "name": "Example",
            "level": 24,
            "xp": 333_258,
            "progress_source": "gmcp",
            "xp_loss_observed": False,
            "xp_loss_total": 0,
            "dead": False,
        },
    )


@pytest.mark.parametrize("source", ["gmcp", "text"])
def test_reconnect_net_loss_sets_floor_without_fabricating_events(source):
    previous, current = _reconnect_states()
    current["progress_source"] = source
    original = deepcopy((previous, current))

    result = _campaign_segment_end_state(previous, current, execution="return-home")

    assert result["xp"] == 333_258
    assert result["campaign_xp_loss_total"] == 2_025
    assert result["xp_loss_total"] == 0
    assert result["xp_loss_observed"] is False
    assert result["dead"] is False
    assert result["campaign_research_results"] == previous["campaign_research_results"]
    assert (previous, current) == original
    assert _campaign_segment_end_state(
        previous, result, execution="return-home"
    )["campaign_xp_loss_total"] == 2_025
    assert _campaign_segment_end_state(
        result, current, execution="return-home"
    )["campaign_xp_loss_total"] == 2_025


@pytest.mark.parametrize("explicit_loss, expected", [(100, 2_025), (385, 2_025), (500, 2_140)])
def test_reconnect_floor_does_not_double_count_explicit_penalties(explicit_loss, expected):
    previous, current = _reconnect_states()
    current.update(xp_loss_observed=True, xp_loss_total=explicit_loss)

    result = _campaign_segment_end_state(previous, current, execution="return-home")

    assert result["campaign_xp_loss_total"] == expected


@pytest.mark.parametrize(
    "changed",
    [
        {"progress_source": None},
        {"progress_source": "checkpoint"},
        {"level": 25, "xp": 0},
        {"level": 23},
        {"level": True},
        {"xp": None},
        {"xp": True},
        {"xp": -1},
        {"xp": "333258"},
        {"xp": 333_258.5},
        {"xp": 334_000},
        {"max_xp": 100},
        {"name": "AnotherCharacter"},
    ],
)
def test_reconnect_floor_rejects_unsupported_comparisons(changed):
    previous, current = _reconnect_states()
    current.update(changed)

    result = _campaign_segment_end_state(previous, current, execution="return-home")

    assert result["campaign_xp_loss_total"] == 1_640


def test_reconnect_floor_requires_valid_starting_progress():
    previous, current = _reconnect_states()
    previous["xp"] = -1

    result = _campaign_segment_end_state(previous, current, execution="return-home")

    assert result["campaign_xp_loss_total"] == 1_640


def test_reconnect_loss_history_repair_is_idempotent_and_keeps_other_evidence():
    previous, current = _reconnect_states()
    current["campaign_xp_loss_total"] = 1_640
    history = [{"start_state_json": json.dumps(previous), "end_state_json": json.dumps(current)}]
    original = deepcopy((previous, current, history))

    repaired = _repair_campaign_xp_loss_total(current, history)

    assert repaired["campaign_xp_loss_total"] == 2_025
    assert repaired["xp_loss_total"] == 0
    assert repaired["xp_loss_observed"] is False
    assert _repair_campaign_xp_loss_total(repaired, history + history) == repaired
    assert _repair_campaign_xp_loss_total(repaired, []) == repaired
    assert (previous, current, history) == original


def test_reconnect_loss_history_preserves_higher_durable_counter():
    previous, current = _reconnect_states()
    current["campaign_xp_loss_total"] = 3_000
    history = [{"start_state_json": json.dumps(previous), "end_state_json": json.dumps(current)}]

    assert _repair_campaign_xp_loss_total({}, history)["campaign_xp_loss_total"] == 3_000


def test_reconnect_loss_history_ignores_missing_or_invalid_endpoints():
    previous, current = _reconnect_states()
    current.pop("progress_source")
    history = [
        {"start_state_json": json.dumps(previous), "end_state_json": json.dumps(current)},
        {"start_state_json": "{", "end_state_json": "[]"},
        {"end_state_json": json.dumps(_reconnect_states()[1])},
    ]

    assert _repair_campaign_xp_loss_total(previous, history) == previous
