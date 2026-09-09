import json
from types import SimpleNamespace

import pytest

from dd4tester.campaign import _run_failed_terminal_state, _run_terminal_state
from dd4tester.storage import RunStorage


@pytest.fixture
def store(tmp_path):
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        run_id = storage.create_run(scenario_name="terminal-evidence", scenario_path="test.yaml")
        yield storage, run_id


@pytest.mark.parametrize("lookup,states", [
    (_run_terminal_state, ("completed", "runtime_cap")),
    (_run_failed_terminal_state, ("failed",)),
])
def test_lookup_preserves_latest_matching_boundary_and_full_payload(store, monkeypatch, lookup, states):
    storage, run_id = store
    storage.record_event(run_id, kind="state", payload={"state": states[0], "old": True})
    expected = {
        "state": states[-1], "objective_kills": [],
        "fastwalk_abort_reason": "observed loss", "unknown_future_field": {"retained": True},
    }
    expected_id = storage.record_event(run_id, kind="state", payload=expected)
    storage.record_event(run_id, kind="state", payload={"state": "disconnected"})
    storage.record_event(run_id, kind="response", payload={"state": states[-1]})
    other = storage.create_run(scenario_name="other", scenario_path="other.yaml")
    storage.record_event(other, kind="state", payload={"state": states[-1]})

    def forbid_transcript_load(*args, **kwargs):
        raise AssertionError("terminal reconstruction must not materialize the transcript")

    monkeypatch.setattr(storage, "list_events", forbid_transcript_load)
    assert lookup(storage, run_id) == expected
    event = storage.get_latest_run_state_event(run_id, states=states)
    assert event["id"] == expected_id
    assert event["run_id"] == run_id


@pytest.mark.parametrize("lookup", [_run_terminal_state, _run_failed_terminal_state])
@pytest.mark.parametrize("payload", [{}, {"state": None}, {"state": "running"}])
def test_missing_terminal_does_not_fall_back_to_loading_every_event(store, monkeypatch, lookup, payload):
    storage, run_id = store
    storage.record_event(run_id, kind="state", payload=payload)
    monkeypatch.setattr(storage, "list_events", lambda _: pytest.fail("unexpected transcript read"))
    assert lookup(storage, run_id) is None


@pytest.mark.parametrize("lookup,state", [
    (_run_terminal_state, "completed"), (_run_failed_terminal_state, "failed"),
])
def test_boundary_lookup_observes_new_commits_without_stale_cache(store, lookup, state):
    storage, run_id = store
    assert lookup(storage, run_id) is None
    for value in (1, 2):
        expected = {"state": state, "value": value}
        storage.record_event(run_id, kind="state", payload=expected)
        assert lookup(storage, run_id) == expected


def test_completed_and_failed_lookups_preserve_their_independent_precedence(store):
    storage, run_id = store
    for state in ("completed", "failed", "runtime_cap", "disconnected"):
        storage.record_event(run_id, kind="state", payload={"state": state})
    assert _run_terminal_state(storage, run_id) == {"state": "runtime_cap"}
    assert _run_failed_terminal_state(storage, run_id) == {"state": "failed"}


@pytest.mark.parametrize("lookup,state", [
    (_run_terminal_state, "completed"), (_run_failed_terminal_state, "failed"),
])
def test_event_list_only_replay_storage_remains_supported(lookup, state):
    expected = {"state": state, "objective_kills": []}
    storage = SimpleNamespace(list_events=lambda _: [
        {"kind": "state", "payload_json": json.dumps(expected)},
        {"kind": "state", "payload_json": '{"state":"disconnected"}'},
    ])
    assert lookup(storage, 1) == expected


def test_empty_boundary_filter_matches_nothing(store):
    storage, run_id = store
    storage.record_event(run_id, kind="state", payload={"state": "completed"})
    assert storage.get_latest_run_state_event(run_id, states=()) is None
