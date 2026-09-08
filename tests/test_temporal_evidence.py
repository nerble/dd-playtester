import json
from datetime import datetime, timedelta, timezone

import pytest

from dd4tester.temporal_evidence import expired_room_crowds


NOW = datetime(2026, 9, 7, 8, tzinfo=timezone.utc)
POLICY = "source-ranked-hunt-test-100-200-8"


def segment(sequence=1, *, age=600, **changes):
    start = {"level": 8, "xp": 12000, "world_boot_id": "boot-1"}
    end = {
        **start,
        "room_vnum": "3054",
        "campaign_fastwalk_abort_reason": "field room contained 2 observed mobiles",
        "campaign_fastwalk_source_present_sightings": [{"policy_id": POLICY}],
        **changes,
    }
    return {
        "id": sequence,
        "sequence": sequence,
        "run_id": sequence + 100,
        "phase": POLICY,
        "status": "success",
        "finished_at": (NOW - timedelta(seconds=age)).isoformat(),
        "start_state_json": json.dumps(start),
        "end_state_json": json.dumps(end),
    }


def expired(rows, now=NOW):
    return expired_room_crowds(rows, boot_id="boot-1", level=8, now=now)


def test_room_crowd_uses_original_observation_time_and_is_repeatable():
    row = segment(age=300)
    assert expired([row], NOW - timedelta(seconds=1)) == {}
    result = expired([row])
    assert result[POLICY]["delay_seconds"] == 300
    assert result == expired([row]) == expired([row], NOW + timedelta(seconds=60))
    assert result[POLICY]["segment_id"] == 1


@pytest.mark.parametrize("count,delay", [(1, 300), (2, 600), (3, 1200), (4, 1800), (8, 1800)])
def test_reinspection_backoff_is_derived_from_actual_segments(count, delay):
    rows = [segment(i + 1, age=4000) for i in range(count - 1)]
    rows.append(segment(count, age=delay - 1))
    assert expired(rows) == {}
    result = expired(rows, NOW + timedelta(seconds=1))
    assert result[POLICY]["delay_seconds"] == delay
    assert result[POLICY]["observation_count"] == count


@pytest.mark.parametrize("change", [
    {"xp": 11990},
    {"xp": 12010},
    {"level": 9},
    {"room_vnum": "3000"},
    {"enemy": "a fighter"},
    {"campaign_fastwalk_abort_reason": "combat assistance observed"},
    {"campaign_fastwalk_consider_outcomes": {"guard": False}},
    {"campaign_fastwalk_source_consider_outcomes": {POLICY: True}},
    {"campaign_fastwalk_source_present_sightings": []},
])
def test_non_observation_outcomes_do_not_expire(change):
    assert expired([segment(**change)]) == {}


def test_newer_failure_supersedes_old_crowd():
    failed = segment(2, age=1, xp=11990)
    failed["status"] = "failed"
    assert expired([failed, segment()]) == {}


@pytest.mark.parametrize("timestamp", [None, "bad", "2026-09-07T07:00:00"])
def test_missing_or_ambiguous_timestamp_does_not_authorize_retry(timestamp):
    row = segment()
    row["finished_at"] = timestamp
    assert expired([row]) == {}


def test_other_boot_and_malformed_history_do_not_authorize_retry():
    row = segment()
    row["end_state_json"] = "not-json"
    assert expired([row, segment(world_boot_id="old-boot")]) == {}


def test_newer_unreadable_history_supersedes_older_crowd():
    row = segment(2)
    row["end_state_json"] = "not-json"
    assert expired([segment(), row]) == {}


def test_null_sightings_do_not_authorize_retry():
    assert expired([segment(campaign_fastwalk_source_present_sightings=None)]) == {}
