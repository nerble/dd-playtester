from __future__ import annotations

import json

from dd4tester.campaign_migrations import (
    mirror_teece_lucky_consider_revalidation_evidence,
)


POLICY_ID = "mirror-realm-plain-teece-hunt-38-40"


def _teece_evidence(name: str, *, start_name: str | None = None) -> tuple[dict, dict, dict, list[dict]]:
    boot_id = "boot-1"
    source_revision = "source-1"
    base = {
        "name": name,
        "level": 39,
        "world_boot_id": boot_id,
        "campaign_source_revision": source_revision,
        "campaign_xp_loss_total": 0,
        "xp": 1000,
        "room_vnum": "3054",
        "dead": False,
        "in_combat": False,
        "hp": 100,
        "max_hp": 100,
    }
    start = dict(base)
    if start_name is not None:
        start["name"] = start_name
    end = {
        **base,
        "campaign_fastwalk_abort_reason": (
            "the unique field target 'mr. teece' failed its live consider gate"
        ),
    }
    state = {
        **base,
        "campaign_research_results": {
            POLICY_ID: {
                "boot_id": boot_id,
                "observed": True,
                "completed_kill": False,
                "viable": False,
            }
        },
    }
    segment = {
        "id": 7,
        "phase": POLICY_ID,
        "status": "success",
        "error": None,
        "run_id": 11,
        "finished_at": "2026-10-18T00:00:00+00:00",
        "command_count": 4,
        "start_state_json": json.dumps(start),
        "end_state_json": json.dumps(end),
    }
    summary = {
        "run": {"id": 11},
        "outcomes": {
            "execution": "success",
            "objective": "not_achieved",
            "safety": "safe",
        },
        "progress": {
            "combat_starts": 0,
            "confirmed_kills": [],
            "experience": {"initial": 1000, "final": 1000, "change": 0},
            "level": {"initial": 39, "final": 39, "change": 0},
            "health": {"lowest_fraction": 1.0},
        },
    }
    events = [
        {
            "id": 1,
            "run_id": 11,
            "kind": "game_event",
            "payload_json": json.dumps(
                {"type": "room_entered", "data": {"vnum": "19166"}}
            ),
        },
        {
            "id": 2,
            "run_id": 11,
            "kind": "game_event",
            "payload_json": json.dumps(
                {
                    "type": "room_listing_observed",
                    "data": {
                        "room_vnum": "19166",
                        "targeted_lines": [{
                            "target_id": "123",
                            "description": (
                                "Mr. Teece sits here playing on his banjo."
                            ),
                        }],
                    },
                }
            ),
        },
        {
            "id": 3,
            "run_id": 11,
            "kind": "command",
            "payload_json": json.dumps({"command": "consider #123"}),
        },
        {
            "id": 4,
            "run_id": 11,
            "kind": "response",
            "payload_json": json.dumps({
                "text": (
                    "Mr. Teece says 'Do you feel lucky, punk?'\r\n"
                    "However, you are currently much healthier than he."
                )
            }),
        },
    ]
    return state, segment, summary, events


def test_teece_revalidation_is_character_independent(monkeypatch) -> None:
    monkeypatch.setattr(
        "dd4tester.mobile_loadouts.unarmed_inert_instrument_reset",
        lambda *args, **kwargs: True,
    )
    state, segment, summary, events = _teece_evidence("Aldric")

    receipt = mirror_teece_lucky_consider_revalidation_evidence(
        state,
        segment,
        summary,
        object(),
        policy_id=POLICY_ID,
        recent_events=events,
    )

    assert receipt is not None
    assert receipt["prior_run_id"] == 11
    assert receipt["level"] == 39


def test_teece_revalidation_rejects_mixed_character_identity(monkeypatch) -> None:
    monkeypatch.setattr(
        "dd4tester.mobile_loadouts.unarmed_inert_instrument_reset",
        lambda *args, **kwargs: True,
    )
    state, segment, summary, events = _teece_evidence(
        "Aldric",
        start_name="Dorrik",
    )

    assert mirror_teece_lucky_consider_revalidation_evidence(
        state,
        segment,
        summary,
        object(),
        policy_id=POLICY_ID,
        recent_events=events,
    ) is None
