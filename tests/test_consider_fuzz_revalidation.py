from __future__ import annotations

import json
import sqlite3
from types import SimpleNamespace

from dd4tester.campaign import (
    _source_ranked_consider_fuzz_revalidation_pending,
)
from dd4tester.campaign_migrations import (
    source_consider_fuzz_revalidation_evidence,
)
from dd4tester.hunt_candidates import HuntCandidate


BOOT = "Sun Sep 27 23:55:43 2026"
SOURCE_REVISION = "b88f935cae1a7f0e7b1520528a09ce35c2bde4b8"
POLICY_ID = "source-ranked-hunt-dwarven-home-20513-20532-39"
XP = 1_312_298
LOSS_TOTAL = 125_953
ROUTE = ("south", "south", "east")


def _candidate() -> HuntCandidate:
    return HuntCandidate(
        status="caution",
        score=300.5,
        area_file="dwarven_home.are",
        mobile_vnum=20513,
        target="the player",
        target_keyword="handball",
        level=43,
        room_vnum=20532,
        room_name="The Handball Room",
        route=ROUTE,
        source_spawn_limit=1,
        room_spawn_count=1,
        boot_kills=0,
        loot=(),
        source_value=0,
        contained_coins=0,
        hazards=(),
        target_identity="dwarf",
        equipped_weapons=(),
        estimated_level_range=(41, 45),
        estimated_base_hp_range=(748, 2385),
        estimated_peak_round_damage=534,
        estimated_critical_hit_damage=178,
        sentinel=True,
        stay_area=True,
    )


def _source_world(*, reset_equipment=()):
    mobile = SimpleNamespace(
        level=43,
        sentinel=True,
        aggressive=False,
        wanders=False,
        confused=False,
        fear_aura=False,
        non_corporeal=False,
        programs=(),
    )
    reset = SimpleNamespace(
        mobile_vnum=20513,
        room_vnum=20532,
        maximum_count=1,
        object_vnums=(),
        equipment=reset_equipment,
    )
    return SimpleNamespace(
        mobiles={20513: mobile},
        mob_resets=(reset,),
        mobile_specials={},
    )


def _fixture():
    candidate = _candidate()
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
    prior_candidate = {
        "policy_id": POLICY_ID,
        "source_revision": SOURCE_REVISION,
        "mobile_vnum": 20513,
        "room_vnum": 20532,
        "level": 43,
        "target_identity": "dwarf",
        "target_keyword": "handball",
        "route": list(ROUTE),
        "estimated_level_range": [41, 45],
    }
    start = {**baseline, "campaign_source_ranked_hunt_candidate": prior_candidate}
    end = {
        **baseline,
        "max_hp": 936,
        "campaign_fastwalk_abort_reason": (
            "the unique field target 'dwarf' failed its live consider gate"
        ),
    }
    state = {
        **baseline,
        "campaign_research_results": {
            POLICY_ID: {
                "boot_id": BOOT,
                "observed": True,
                "consider_viable": False,
                "completed_kill": False,
                "viable": False,
                "xp_delta": 0,
            }
        },
    }
    segment = {
        "id": 17403,
        "phase": POLICY_ID,
        "status": "success",
        "error": None,
        "run_id": 17932,
        "finished_at": "2026-10-14T06:46:09+00:00",
        "command_count": 100,
        "start_state_json": json.dumps(start),
        "end_state_json": json.dumps(end),
    }
    summary = {
        "run": {"id": 17932},
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
    events = [
        {
            "id": 10,
            "run_id": 17932,
            "timestamp": "2026-10-14T06:44:45+00:00",
            "kind": "game_event",
            "payload_json": json.dumps(
                {
                    "type": "room_entered",
                    "data": {
                        "package": "Room.Info",
                        "vnum": "20532",
                    },
                }
            ),
        },
        {
            "id": 11,
            "run_id": 17932,
            "timestamp": "2026-10-14T06:44:46+00:00",
            "kind": "response",
            "payload_json": json.dumps(
                {"text": "[#10787] A dwarf is playing handball against the wall.\n"}
            ),
        },
        {
            "id": 12,
            "run_id": 17932,
            "timestamp": "2026-10-14T06:44:47+00:00",
            "kind": "command",
            "payload_json": json.dumps({"command": "consider #10787"}),
        },
        {
            "id": 13,
            "run_id": 17932,
            "timestamp": "2026-10-14T06:44:47.5+00:00",
            "kind": "response",
            "payload_json": json.dumps(
                {
                    "text": (
                        "The player laughs at you mercilessly.\n\r"
                        "Also, he is much healthier than you.\n\r"
                    )
                }
            ),
        },
    ]
    return state, segment, summary, candidate, _source_world(), events


def test_exact_safe_source_fuzz_consider_can_arm_one_revalidation() -> None:
    state, segment, summary, candidate, world, events = _fixture()

    receipt = source_consider_fuzz_revalidation_evidence(
        state,
        segment,
        summary,
        candidate,
        world,
        policy_id=POLICY_ID,
        recent_events=events,
    )

    assert receipt is not None
    assert receipt["status"] == "pending"
    assert receipt["maximum_level_offset"] == 6
    assert receipt["prior_run_id"] == 17932
    assert receipt["target_instance_id"] == "10787"
    assert _source_ranked_consider_fuzz_revalidation_pending(
        {**state, "campaign_source_ranked_consider_fuzz_revalidation": receipt},
        candidate,
        character_level=39,
    )


def test_evidence_accepts_storage_sqlite_row() -> None:
    state, segment, summary, candidate, world, events = _fixture()
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    columns = ", ".join(f"? AS [{key}]" for key in segment)
    segment_row = connection.execute(
        f"SELECT {columns}", tuple(segment.values())
    ).fetchone()

    receipt = source_consider_fuzz_revalidation_evidence(
        state,
        segment_row,
        summary,
        candidate,
        world,
        policy_id=POLICY_ID,
        recent_events=events,
    )

    assert receipt is not None
    assert receipt["prior_segment_id"] == 17403
    connection.close()


def test_consider_fuzz_revalidation_rejects_missing_health_warning_line() -> None:
    state, segment, summary, candidate, world, events = _fixture()
    events[-1]["payload_json"] = json.dumps(
        {"text": "The player laughs at you mercilessly.\n\r"}
    )

    assert source_consider_fuzz_revalidation_evidence(
        state,
        segment,
        summary,
        candidate,
        world,
        policy_id=POLICY_ID,
        recent_events=events,
    ) is None


def test_consider_fuzz_revalidation_rejects_changed_xp_loss_or_source_loadout() -> None:
    state, segment, summary, candidate, world, events = _fixture()
    changed_state = {**state, "campaign_xp_loss_total": LOSS_TOTAL + 1}
    assert source_consider_fuzz_revalidation_evidence(
        changed_state,
        segment,
        summary,
        candidate,
        world,
        policy_id=POLICY_ID,
        recent_events=events,
    ) is None

    armed_world = _source_world(reset_equipment=((16, 1234),))
    assert source_consider_fuzz_revalidation_evidence(
        state,
        segment,
        summary,
        candidate,
        armed_world,
        policy_id=POLICY_ID,
        recent_events=events,
    ) is None
