from __future__ import annotations

import json
from dataclasses import replace
from types import SimpleNamespace

from dd4tester.campaign import (
    CampaignRunner,
    _MIRROR_TEECE_LUCKY_CONSIDER_REVALIDATION_KEY,
    _MIRROR_REALM_PLAIN_HUNT_POLICY,
    _MIRROR_REALM_TEECE_HUNT_POLICY,
    _MIRROR_REALM_WAITER_HUNT_POLICY,
)
from dd4tester.campaign_migrations import (
    mirror_teece_lucky_consider_revalidation_evidence,
)
from dd4tester.hunt_candidates import MobReset, MobileSource, ObjectSource


BOOT = "Wed Oct 14 09:25:18 2026"
SOURCE_REVISION = "b88f935cae1a7f0e7b1520528a09ce35c2bde4b8"
POLICY_ID = "mirror-realm-plain-teece-hunt-38-40"
XP = 1_326_256
LOSS_TOTAL = 132_003
RUN_ID = 17957
SEGMENT_ID = 17428


def _fixture():
    baseline = {
        "name": "Dorrik",
        "level": 39,
        "world_boot_id": BOOT,
        "campaign_source_revision": SOURCE_REVISION,
        "xp": XP,
        "campaign_xp_loss_total": LOSS_TOTAL,
        "room_vnum": "3054",
        "hp": 936,
        "max_hp": 936,
        "dead": False,
        "in_combat": False,
    }
    state = {
        **baseline,
        "campaign_research_results": {
            POLICY_ID: {
                "boot_id": BOOT,
                "observed": True,
                "completed_kill": False,
                "viable": False,
            }
        },
    }
    end = {
        **baseline,
        "campaign_fastwalk_abort_reason": (
            "the unique field target 'mr. teece' failed its live consider gate"
        ),
    }
    segment = {
        "id": SEGMENT_ID,
        "phase": POLICY_ID,
        "status": "success",
        "error": None,
        "run_id": RUN_ID,
        "finished_at": "2026-10-14T12:05:37+00:00",
        "command_count": 103,
        "start_state_json": json.dumps(baseline),
        "end_state_json": json.dumps(end),
    }
    summary = {
        "run": {"id": RUN_ID},
        "outcomes": {
            "execution": "success",
            "objective": "not_achieved",
            "safety": "safe",
        },
        "progress": {
            "combat_starts": 0,
            "confirmed_kills": [],
            "experience": {"change": 0, "initial": XP, "final": XP},
            "level": {"change": 0, "initial": 39, "final": 39},
            "health": {"lowest_fraction": 1.0},
        },
    }
    rows = [
        {
            "id": 10,
            "run_id": RUN_ID,
            "kind": "game_event",
            "payload_json": json.dumps({
                "type": "room_entered", "data": {"vnum": "19166"},
            }),
        },
        {
            "id": 11,
            "run_id": RUN_ID,
            "kind": "game_event",
            "payload_json": json.dumps({
                "type": "room_listing_observed",
                "data": {
                    "room_vnum": "19166",
                    "targeted_lines": [{
                        "target_id": "10240",
                        "description": (
                            "(Translucent) Mr. Teece sits here playing on his banjo."
                        ),
                    }],
                },
            }),
        },
        {
            "id": 12,
            "run_id": RUN_ID,
            "kind": "command",
            "payload_json": json.dumps({"command": "consider #10240"}),
        },
        {
            "id": 13,
            "run_id": RUN_ID,
            "kind": "response",
            "payload_json": json.dumps({
                "text": (
                    "Mr. Teece says 'Do you feel lucky, punk?'.\n\r"
                    "However, you are currently much healthier than he.\n\r"
                ),
            }),
        },
    ]
    mobile = MobileSource(
        19069, "mr teece", "Mr. Teece", 40, 1 << 1, 0, "mirror_realm.are",
    )
    instrument = ObjectSource(
        19156, "banjo", "a banjo", 36, (0, 0, 0, 0), 0,
        wear_flags=1 | (1 << 14), extra_flags=1 << 1,
    )
    world = SimpleNamespace(
        mobiles={19069: mobile},
        objects={19156: instrument},
        mob_resets=[MobReset(19069, 19166, 1, (19156,), ((17, 19156),))],
    )
    return state, segment, summary, world, rows


def _receipt(state, segment, summary, world, rows):
    return mirror_teece_lucky_consider_revalidation_evidence(
        state,
        segment,
        summary,
        world,
        policy_id=POLICY_ID,
        recent_events=rows,
    )


def test_exact_safe_no_combat_lucky_consider_yields_one_bounded_receipt() -> None:
    state, segment, summary, world, rows = _fixture()

    receipt = _receipt(state, segment, summary, world, rows)

    assert receipt is not None
    assert receipt["status"] == "pending"
    assert receipt["mobile_vnum"] == 19069
    assert receipt["room_vnum"] == 19166
    assert receipt["maximum_level_offset"] == 5
    assert receipt["prior_run_id"] == RUN_ID
    assert receipt["matched_consider_command_event_id"] == 12
    assert receipt["matched_consider_response_event_id"] == 13


def test_teece_receipt_rejects_changed_target_combat_or_inert_loadout() -> None:
    state, segment, summary, world, rows = _fixture()

    changed_rows = [dict(row) for row in rows]
    changed_rows[-1] = {
        **changed_rows[-1],
        "payload_json": json.dumps({"text": "Do you feel lucky, punk?"}),
    }
    assert _receipt(state, segment, summary, world, changed_rows) is None

    combat_summary = json.loads(json.dumps(summary))
    combat_summary["progress"]["combat_starts"] = 1
    assert _receipt(state, segment, combat_summary, world, rows) is None

    world.objects[19156] = replace(world.objects[19156], affects=((19, 1),))
    assert _receipt(state, segment, summary, world, rows) is None


def test_teece_revalidation_is_consumed_once_before_policy_dispatch(monkeypatch) -> None:
    state, segment, summary, world, rows = _fixture()

    class PriorVisitStorage:
        def get_latest_campaign_segment_for_phase(
            self, _campaign_id, phase, *, search_limit,
        ):
            assert search_limit == 256
            return segment if phase == POLICY_ID else None

        def get_run_summary(self, run_id):
            return summary if run_id == RUN_ID else None

        def list_recent_events(self, run_id, *, limit):
            assert run_id == RUN_ID and limit == 512
            return rows

    state["campaign_registered_research_xp_loss_policies"] = [{
        "boot_id": BOOT,
        "level": 39,
        "loss_count": 1,
        "policy_id": "mirror-realm-plain-hunt-38-40",
    }]
    state["campaign_source_ranked_xp_loss_policies"] = []
    runner = object.__new__(CampaignRunner)
    runner._source_world = world
    runner._campaign_policy_storage = PriorVisitStorage()
    runner._campaign_policy_campaign_id = 7
    runner._emit_progress = lambda _message: None
    monkeypatch.setattr(
        "dd4tester.campaign._mirror_realm_plain_hunt_source_available",
        lambda _world, *, source_mobile_vnums=None, **_kwargs: (
            source_mobile_vnums == (19069,)
        ),
    )

    selected = runner._mirror_realm_plain_hunt_policy(state)

    assert selected is not None
    assert selected.policy_id == POLICY_ID
    marker = state[_MIRROR_TEECE_LUCKY_CONSIDER_REVALIDATION_KEY]
    assert marker["status"] == "attempted"
    assert marker["prior_run_id"] == RUN_ID

    assert runner._mirror_realm_plain_hunt_policy(state) is None


def test_teece_loss_does_not_hide_independently_audited_waiter(monkeypatch) -> None:
    state = {
        "level": 39,
        "world_boot_id": BOOT,
        "campaign_research_results": {
            _MIRROR_REALM_PLAIN_HUNT_POLICY.policy_id: {
                "boot_id": BOOT,
                "completed_kill": True,
                "viable": False,
            },
            _MIRROR_REALM_WAITER_HUNT_POLICY.policy_id: {
                "boot_id": "previous-boot",
                "completed_kill": False,
            },
        },
        "campaign_source_ranked_xp_loss_policies": [{
            "boot_id": BOOT,
            "level": 39,
            "loss_count": 1,
            "policy_id": "source-ranked-hunt-mirror-realm-19069-19166-39",
        }],
    }
    runner = object.__new__(CampaignRunner)
    runner._source_world = object()
    runner._emit_progress = lambda _message: None
    monkeypatch.setattr(
        "dd4tester.campaign._mirror_realm_plain_hunt_source_available",
        lambda _world, *, source_mobile_vnums=None, **_kwargs:
            source_mobile_vnums == (19027,),
    )

    selected = runner._mirror_realm_plain_hunt_policy(state)

    assert selected is not None
    assert selected.policy_id == _MIRROR_REALM_WAITER_HUNT_POLICY.policy_id
    assert selected.source_mobile_vnums == (19027,)
    assert selected.segment_kill_limit == 1

    state["campaign_research_results"][selected.policy_id] = {
        "boot_id": BOOT,
        "completed_kill": False,
    }
    assert runner._mirror_realm_plain_hunt_policy(state) is None
