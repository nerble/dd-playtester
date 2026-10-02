import json

import pytest

from dd4tester.campaign import (
    _quest_source_preflight_issue,
    _quest_target_runner_options,
)
from dd4tester.hunt_candidates import WorldSource
from dd4tester.observations import ObservationParser
from dd4tester.quests import snapshot_quest_status
from dd4tester.state import CharacterState


HOARD_TEXT = (
    "Goldmoon intones in a voice like distant thunder, \n\r"
    "'Legends tell of a lost hoard, buried deep beneath the earth near "
    "\x1b[36mCentral Omu, Rope Bridge\x1b[0m, \n\r"
    "at the edge of the ancient realm of Omu Central.  "
    "Hie thee swiftly, brave soul, \n\r"
    "for the earth's secret will stir but for a heartbeat...'\n\r"
)


def quest_payload(**changes):
    return {
        "active": 1, "complete": 0, "type": "retrieve",
        "giver_vnum": 10001, "giver_name": "Goldmoon",
        "room_vnum": 28756, "room_name": "Central Omu, Rope Bridge",
        "area_name": "Omu Central", "object_vnum": 589,
        "target_name": "the tattered codex", "countdown": 12,
        **changes,
    }


@pytest.mark.parametrize("gmcp_first", [True, False])
@pytest.mark.parametrize("chunk_size", [1, 4096])
def test_requested_hoard_binds_fragmented_narrative_to_live_quest(
    gmcp_first, chunk_size,
):
    parser = ObservationParser()
    state = CharacterState()
    parser.quest_assignment.begin_request()
    message = "Char.Quest " + json.dumps(quest_payload())
    events = parser.feed_gmcp(message) if gmcp_first else []
    for start in range(0, len(HOARD_TEXT), chunk_size):
        events.extend(parser.feed_text(HOARD_TEXT[start:start + chunk_size]))
    if not gmcp_first:
        events.extend(parser.feed_gmcp(message))
    for event in events:
        state.apply(event)

    assert state.quest_status["type"] == "retrieve"
    assert snapshot_quest_status(state.quest_status).kind == "hoard"
    assert state.quest_status["retrieval_evidence"]["object_vnum"] == 589
    update = parser.feed_gmcp("Char.Quest " + json.dumps(quest_payload(countdown=11)))
    assert snapshot_quest_status(update[-1].data).kind == "hoard"


@pytest.mark.parametrize("changes", [
    {"giver_name": "Someone else"}, {"room_name": "Another bridge"},
    {"area_name": "Another area"}, {"room_vnum": 0}, {"object_vnum": 0},
    {"active": 0}, {"type": "kill"},
])
def test_hoard_narrative_cannot_bind_an_unmatched_quest(changes):
    parser = ObservationParser()
    parser.quest_assignment.begin_request()
    parser.feed_text(HOARD_TEXT)
    events = parser.feed_gmcp("Char.Quest " + json.dumps(quest_payload(**changes)))
    assert "retrieval_evidence" not in events[-1].data


@pytest.mark.parametrize("end_scope", ["reconnect", "new-request", "inactive", "changed-target"])
def test_hoard_evidence_does_not_leak_into_another_assignment(end_scope):
    parser = ObservationParser()
    parser.quest_assignment.begin_request()
    parser.feed_text(HOARD_TEXT)
    parser.feed_gmcp("Char.Quest " + json.dumps(quest_payload()))
    if end_scope == "reconnect":
        parser.reset_connection()
    elif end_scope == "new-request":
        parser.quest_assignment.begin_request()
    elif end_scope == "inactive":
        parser.feed_gmcp('Char.Quest {"active": 0, "type": "none"}')
    else:
        parser.feed_gmcp("Char.Quest " + json.dumps(quest_payload(object_vnum=585)))
    events = parser.feed_gmcp("Char.Quest " + json.dumps(quest_payload(countdown=11)))
    assert "retrieval_evidence" not in events[-1].data


def test_unsolicited_or_late_hoard_narrative_cannot_authorize_digging(monkeypatch):
    now = [100.0]
    monkeypatch.setattr("dd4tester.quests.time.monotonic", lambda: now[0])
    parser = ObservationParser()
    parser.feed_text(HOARD_TEXT)
    events = parser.feed_gmcp("Char.Quest " + json.dumps(quest_payload()))
    assert snapshot_quest_status(events[-1].data).kind == "retrieve"
    parser.quest_assignment.begin_request()
    now[0] += 6
    parser.feed_text(HOARD_TEXT)
    events = parser.feed_gmcp("Char.Quest " + json.dumps(quest_payload(countdown=11)))
    assert "retrieval_evidence" not in events[-1].data


def test_known_hoard_cannot_reach_the_legacy_blind_dig_loop():
    status = quest_payload(type="hoard")
    quest = snapshot_quest_status(status)
    for execution in ("quest-target-run", "quest-digging-tool"):
        assert "trap-aware hoard acquisition" in _quest_source_preflight_issue(
            WorldSource(), quest, execution=execution, character_level=29,
        )
    with pytest.raises(RuntimeError, match="trap-aware hoard acquisition"):
        _quest_target_runner_options(
            WorldSource(), {"quest_status": status},
            character_level=29, policy_id="quest-target-run",
        )


def test_saved_hoard_annotation_requires_unchanged_quest_identity():
    parser = ObservationParser()
    parser.quest_assignment.begin_request()
    parser.feed_text(HOARD_TEXT)
    events = parser.feed_gmcp("Char.Quest " + json.dumps(quest_payload()))
    annotated = events[-1].data
    for key in ("giver_vnum", "room_vnum", "object_vnum"):
        changed = {**annotated, key: annotated[key] + 1}
        assert snapshot_quest_status(changed).kind == "retrieve"
