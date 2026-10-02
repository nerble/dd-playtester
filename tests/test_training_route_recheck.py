import copy
import json
from types import SimpleNamespace

import pytest

from dd4tester.campaign import _reopen_route_blocked_local_training
from dd4tester.hunt_candidates import RoomSource, WorldSource
from dd4tester.starter import LocalTrainingFallback, _ClassTrainerRoute


KEY = "campaign_training_deficit_repair"


def _event(kind, **payload):
    return {"kind": kind, "payload_json": json.dumps(payload)}


@pytest.fixture
def visit(monkeypatch):
    fallback = LocalTrainingFallback(
        _ClassTrainerRoute("3023", "Yard", "guildmaster", (
            ("3001", "south", "3005"), ("3005", "east", "3023"),
        )), 3023, (("parry", 0, 28),),
    )
    world = WorldSource(rooms={vnum: RoomSource(vnum, name, "midgaard.are") for vnum, name in (
        (3001, "Temple"), (3005, "The Temple Square"),
        (3023, "Yard"), (3006, "The General Store"),
    )})
    monkeypatch.setattr("dd4tester.campaign.plan_local_training_fallback", lambda *args, **kwargs: fallback)
    state = {
        "level": 26, "world_boot_id": "boot-1", "room_vnum": "3054",
        "hp": 590, "max_hp": 594, "practice": 2,
        "campaign_training_audit": {"observed": True, "level": 26, "boot_id": "boot-1",
                                    "physical_practices": 2, "intellectual_practices": 1},
        KEY: {"level": 26, "boot_id": "boot-1", "attempted": True,
              "attempt_policy_id": "training-deficit-repair-10-100",
              "local_teacher_fallback": {**fallback.evidence(), "status": "consumed"}},
        "campaign_protection_recovery_required": {"policy_id": "failed-fight"},
    }
    segments = [
        {"run_id": 10, "status": "success", "phase": "training-deficit-repair-10-100",
         "start_state_json": json.dumps(state)},
        {"run_id": 11, "status": "success", "phase": "source-ranked-hunt-example",
         "start_state_json": json.dumps({**state, "xp": 100}),
         "end_state_json": json.dumps({**state, "xp": 200})},
    ]
    events = {
        10: [
            _event("game_event", type="training_route_fallback", data=fallback.evidence()),
            _event("game_event", type="training_deferred", data={
                "preflight": True, "route_hazards": ["trainer route hazard: under-band Midgaard drunk"],
            }),
        ],
        11: [_event("state", state="completed", objective_kills=[{"xp_gained": 100}],
                    campaign_field_city_preflight={
                        "complete": True, "blocked": False, "level": 26, "boot_id": "boot-1",
                        "stopped_before_departure": False, "locations": ["the general store"],
                    })],
    }
    storage = SimpleNamespace(list_events=lambda run_id: events[run_id])
    return state, segments, events, storage, world


def _reopen(visit):
    state, segments, _, storage, world = visit
    return _reopen_route_blocked_local_training(
        storage, state, segments, world=world, character_class="warrior", subclass=None,
    )


def test_productive_clear_sighting_reopens_one_unspent_local_visit(visit):
    state = visit[0]
    original = copy.deepcopy(state)
    repaired, changed = _reopen(visit)
    assert changed
    assert state == original
    assert repaired[KEY]["attempted"] is False
    fallback = repaired[KEY]["local_teacher_fallback"]
    assert fallback["status"] == "pending"
    assert fallback["route_clear_recheck"] == {
        "status": "pending", "blocked_run_id": 10, "observation_run_id": 11,
        "locations": ["general store"], "route_room_vnums": [3001, 3005, 3023],
    }
    assert repaired["campaign_protection_recovery_required"] == {"policy_id": "failed-fight"}
    fallback["status"] = "consumed"
    fallback["route_clear_recheck"]["status"] = "consumed"
    repaired[KEY]["attempted"] = True
    assert _reopen((repaired, *visit[1:])) == (repaired, False)


@pytest.mark.parametrize("reason", (
    "on-route", "unknown-room", "missing-live-probe", "no-kill", "no-net-xp",
    "old-boot", "low-health", "other-teacher", "lesson-attempt", "rejected-lesson",
    "not-preflight", "stale-observation", "prior-retry",
))
def test_local_training_recheck_requires_changed_live_evidence(visit, reason):
    state, segments, events, _, _ = visit
    live = json.loads(events[11][0]["payload_json"])
    probe = live["campaign_field_city_preflight"]
    if reason == "on-route":
        probe["locations"] = ["the temple square"]
    elif reason == "unknown-room":
        probe["locations"] = ["unmapped place"]
    elif reason == "missing-live-probe":
        state["campaign_field_city_preflight"] = probe
        del live["campaign_field_city_preflight"]
    elif reason == "no-kill":
        live["objective_kills"] = []
    elif reason == "no-net-xp":
        segments[-1]["end_state_json"] = segments[-1]["start_state_json"]
    elif reason == "old-boot":
        probe["boot_id"] = "boot-old"
    elif reason == "low-health":
        state["hp"] = 300
    elif reason == "other-teacher":
        events[10][0] = _event("game_event", type="training_route_fallback", data={
            "teacher_mobile_vnum": 3020, "room_vnum": "3020",
        })
    elif reason == "lesson-attempt":
        events[10].append(_event("command", command="practice parry"))
    elif reason == "rejected-lesson":
        events[10].append(_event("game_event", type="training_rejected"))
    elif reason == "not-preflight":
        events[10].pop()
    elif reason == "stale-observation":
        segments[-1]["run_id"] = 9
    else:
        state[KEY]["local_teacher_fallback"]["route_clear_recheck"] = {"status": "consumed"}
    events[11][0]["payload_json"] = json.dumps(live)
    assert _reopen(visit) == (state, False)


@pytest.fixture
def timed_visit(visit):
    state, segments, events, _, _ = visit
    state["campaign_automatic_world_time_probe"] = {"level": 26, "boot_id": "boot-1"}
    segments[0]["finished_at"] = "2026-09-28T10:00:00+00:00"
    segments[1].update({
        "phase": "world-time-probe", "started_at": "2026-09-28T10:05:00+00:00",
        "end_state_json": segments[1]["start_state_json"],
    })
    events[11] = [
        _event("command", command="time"),
        _event("state", state="completed", world_boot_id="boot-1"),
    ]
    return visit


def test_completed_time_probe_can_arm_one_local_preflight_after_cooldown(timed_visit):
    state = timed_visit[0]
    repaired, changed = _reopen(timed_visit)
    assert changed and repaired[KEY]["attempted"] is False
    recheck = repaired[KEY]["local_teacher_fallback"]["route_clear_recheck"]
    assert recheck["reason"] == "bounded-route-cooldown"
    assert recheck["cooldown_seconds"] == 300
    assert recheck["locations"] == []
    assert repaired["campaign_protection_recovery_required"] == state["campaign_protection_recovery_required"]
    assert _reopen((repaired, *timed_visit[1:])) == (repaired, False)


@pytest.mark.parametrize("missing", (
    "cooldown", "aware-time", "automatic-probe", "time-command", "boot-response",
    "same-boot", "unspent-recheck", "unspent-lesson",
))
def test_timed_training_retry_does_not_turn_reconnect_into_permission(timed_visit, missing):
    state, segments, events, _, _ = timed_visit
    if missing == "cooldown":
        segments[1]["started_at"] = "2026-09-28T10:04:59+00:00"
    elif missing == "aware-time":
        segments[0]["finished_at"] = "2026-09-28T10:00:00"
    elif missing == "automatic-probe":
        del state["campaign_automatic_world_time_probe"]
    elif missing == "time-command":
        events[11].pop(0)
    elif missing == "boot-response":
        events[11].pop()
    elif missing == "same-boot":
        events[11][-1] = _event("state", state="completed", world_boot_id="boot-old")
    elif missing == "unspent-recheck":
        state[KEY]["local_teacher_fallback"]["route_clear_recheck"] = {"status": "consumed"}
    elif missing == "unspent-lesson":
        events[10].append(_event("command", command="practice parry"))
    assert _reopen(timed_visit) == (state, False)


def test_training_recheck_fetches_only_its_missing_historical_phase(timed_visit):
    state, segments, events, storage, world = timed_visit
    blocked, latest = segments
    latest["campaign_id"] = 7
    calls = []

    def lookup(campaign_id, phase):
        calls.append((campaign_id, phase))
        return blocked

    storage.get_latest_campaign_segment_for_phase = lookup
    repaired, changed = _reopen((state, [latest], events, storage, world))
    assert changed
    assert calls == [(7, "training-deficit-repair-10-100")]
    assert repaired[KEY]["local_teacher_fallback"]["route_clear_recheck"]["blocked_run_id"] == 10
