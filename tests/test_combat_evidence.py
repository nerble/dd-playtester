from __future__ import annotations

import json

from dd4tester.combat_evidence import verified_unprotected_single_kill_run


def _valid_evidence(tmp_path):
    transcript = tmp_path / "run.jsonl"
    events = [
        {
            "kind": "gmcp",
            "payload": {
                "message": 'Char.Affect [ [ { "name": "armor" } ] ]',
            },
            "run_id": 42,
        },
        {
            "kind": "gmcp",
            "payload": {
                "message": 'Char.Enemies [ [ { "isnpc": "20511", "maxhp": "1089" } ] ]',
            },
            "run_id": 42,
        },
        {
            "kind": "command",
            "payload": {"command": "consider dancer"},
            "run_id": 42,
        },
    ]
    transcript.write_text(
        "".join(json.dumps(event) + "\n" for event in events),
        encoding="utf-8",
    )
    run = {
        "id": 42,
        "boot_id": "boot-a",
        "status": "success",
        "execution_status": "success",
        "objective_outcome": "achieved",
        "safety_outcome": "safe",
    }
    summary = {
        "outcomes": {
            "execution": "success",
            "objective": "achieved",
            "safety": "safe",
        },
        "character": {
            "name": "Dorrik",
            "class": "warrior",
            "race": "dwarf",
            "subclass": "knight",
        },
        "objective": {
            "fastwalk_kill_limit": 1,
            "fastwalk_hunt_stop_boundaries": [{"route_endpoint": "20516"}],
        },
        "progress": {
            "level": {"initial": 36, "final": 36},
            "health": {"lowest_fraction": 0.49},
            "confirmed_kills": [
                {
                    "source_mobile_vnum": 20511,
                    "source_policy_id": "source-ranked-hunt-dwarven-home-20511-20516-36",
                    "xp_gained": 3242,
                }
            ],
        },
    }
    return run, summary, transcript


def _verify(evidence):
    run, summary, transcript = evidence
    return verified_unprotected_single_kill_run(
        run,
        summary,
        transcript,
        character_name="Dorrik",
        character_level=36,
        character_class="warrior",
        character_race="dwarf",
        character_subclass="knight",
        world_boot_id="boot-a",
        source_mobile_vnum=20511,
        source_policy_id="source-ranked-hunt-dwarven-home-20511-20516-36",
    )


def test_verified_unprotected_kill_returns_compact_receipt(tmp_path) -> None:
    receipt = _verify(_valid_evidence(tmp_path))

    assert receipt == {
        "run_id": 42,
        "xp_gained": 3242,
        "lowest_health_fraction": 0.49,
        "observed_target_max_hp": 1089,
        "source_policy_id": "source-ranked-hunt-dwarven-home-20511-20516-36",
        "source_mobile_vnum": 20511,
        "world_boot_id": "boot-a",
    }


def test_sanctuary_affect_disqualifies_unprotected_kill(tmp_path) -> None:
    evidence = _valid_evidence(tmp_path)
    transcript = evidence[2]
    with transcript.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({
            "kind": "gmcp",
            "payload": {"message": 'Char.Affect [ { "name": "sanctuary" } ]'},
            "run_id": 42,
        }) + "\n")

    assert _verify(evidence) is None


def test_missing_affect_observation_disqualifies_evidence(tmp_path) -> None:
    evidence = _valid_evidence(tmp_path)
    transcript = evidence[2]
    transcript.write_text(
        json.dumps({
            "kind": "command",
            "payload": {"command": "consider dancer"},
            "run_id": 42,
        }) + "\n",
        encoding="utf-8",
    )

    assert _verify(evidence) is None
