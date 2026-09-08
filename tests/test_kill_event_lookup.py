import json
from types import SimpleNamespace

import pytest

from dd4tester.campaign import _run_objective_kills, _segment_objective_kills
from dd4tester.storage import RunStorage


@pytest.fixture
def store(tmp_path):
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        run_id = storage.create_run(
            scenario_name="kill-evidence", scenario_path=tmp_path / "character.yaml",
        )
        yield storage, run_id


@pytest.mark.parametrize("payload,expected", [
    ({"objective_kills": []}, []),
    ({"completed_kills": []}, []),
    ({"objective_kills": [{"mob_name": "orc", "xp_gained": 89}]},
     [{"mob_name": "orc", "xp_gained": 89}]),
    ({"completed_kills": [{"mob_name": "orc", "xp_gained": 89}]},
     [{"mob_name": "orc", "xp_gained": 89}]),
    ({"objective_kills": [], "completed_kills": [{"mob_name": "drunk"}]}, []),
    ({"objective_kills": None, "completed_kills": []}, []),
    ({"objective_kills": "invalid", "completed_kills": []}, []),
])
def test_targeted_lookup_preserves_kill_ledger_precedence(store, monkeypatch, payload, expected):
    storage, run_id = store
    storage.record_event(run_id, kind="state", payload=payload)

    def forbid_transcript_load(*args, **kwargs):
        raise AssertionError("kill reconstruction must not load every run event")

    monkeypatch.setattr(storage, "list_events", forbid_transcript_load)
    assert _run_objective_kills(storage, run_id) == expected


def test_latest_empty_ledger_supersedes_old_kill_and_ignores_other_events(store):
    storage, run_id = store
    storage.record_event(run_id, kind="state", payload={"objective_kills": [{"mob_name": "orc"}]})
    storage.record_event(run_id, kind="state", payload={"completed_kills": []})
    storage.record_event(run_id, kind="response", payload={"objective_kills": [{"mob_name": "fake"}]})
    storage.record_event(run_id, kind="state", payload={"state": "disconnected"})
    other = storage.create_run(scenario_name="other", scenario_path="other.yaml")
    storage.record_event(other, kind="state", payload={"objective_kills": [{"mob_name": "other"}]})
    event = storage.get_latest_run_kill_event(run_id)
    assert event["run_id"] == run_id
    assert json.loads(event["payload_json"]) == {"completed_kills": []}
    assert _run_objective_kills(storage, run_id) == []


@pytest.mark.parametrize("payload", [{}, {"objective_kills": None}, {"completed_kills": "invalid"}])
def test_non_list_ledger_does_not_replace_durable_mob_kill_fallback(store, monkeypatch, payload):
    storage, run_id = store
    storage.record_event(run_id, kind="state", payload=payload)
    assert storage.get_latest_run_kill_event(run_id) is None
    monkeypatch.setattr(storage, "list_mob_kills_for_run", lambda _: [{
        "objective_eligible": True, "source_policy_id": "source-ranked-hunt-one",
        "mob_name": "orc", "xp_gained": 89, "source_mobile_vnum": 4004,
    }, {
        "objective_eligible": False, "source_policy_id": "source-ranked-hunt-one",
        "mob_name": "drunk", "xp_gained": 10, "source_mobile_vnum": 3064,
    }, {
        "objective_eligible": True, "source_policy_id": "source-ranked-hunt-other",
        "mob_name": "another orc", "xp_gained": 50, "source_mobile_vnum": 4005,
    }])
    assert _run_objective_kills(storage, run_id, execution="source-ranked-hunt-one") == [{
        "mob_name": "orc", "xp_gained": 89, "source_mobile_vnum": 4004,
        "source_policy_id": "source-ranked-hunt-one",
    }]


def test_fresh_terminal_failure_still_overrides_inherited_checkpoint_kill(store):
    storage, run_id = store
    storage.record_event(run_id, kind="state", payload={"state": "failed", "objective_kills": []})
    segment = {
        "phase": "source-ranked-hunt-one", "run_id": run_id,
        "end_state_json": json.dumps({"campaign_objective_kills": [{"mob_name": "stale"}]}),
    }
    assert _segment_objective_kills(storage, segment) == []


def test_lookup_is_fresh_when_a_later_ledger_is_recorded(store):
    storage, run_id = store
    assert _run_objective_kills(storage, run_id) is None
    storage.record_event(run_id, kind="state", payload={"objective_kills": []})
    assert _run_objective_kills(storage, run_id) == []
    storage.record_event(run_id, kind="state", payload={"objective_kills": [{"mob_name": "orc"}]})
    assert _run_objective_kills(storage, run_id) == [{"mob_name": "orc"}]


def test_replay_storage_without_targeted_method_remains_supported():
    storage = SimpleNamespace(list_events=lambda _: [
        {"kind": "state", "payload_json": '{"completed_kills": [{"mob_name": "orc"}]}'},
        {"kind": "state", "payload_json": '{"objective_kills": []}'},
    ])
    assert _run_objective_kills(storage, 1) == []
