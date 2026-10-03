import json
from pathlib import Path

import pytest

from dd4tester.campaign import (
    _campaign_failure_state_from_run, _repair_dispatched_weapon_comparison,
)
from dd4tester.storage import RunStorage
from dd4tester.weapon_comparison import COMPARISON_KEY, weapon_comparison_request


PLAN = {
    "candidate_name": "a long, grey branch", "candidate_vnum": 6104,
    "primary_name": "a large club", "primary_vnum": 1521, "keyword": "branch",
}
FAILURE = "weapon comparison timed out during compare"
REASON = "verify the ambiguous carried weapon at the healer"


@pytest.mark.parametrize("damage", [
    None, "wrong_phase", "changed_boot", "changed_level", "changed_plan",
    "lost_xp", "wielded", "incomplete", "wrong_failure", "oversized",
    "modern_request", "missing_segment",
])
def test_legacy_terminal_repair_requires_complete_matching_read_only_visit(tmp_path, damage):
    request = {**PLAN, "level": 29, "boot_id": "boot", "stage": "dispatched"}
    if damage == "modern_request":
        request["response_parser_revision"] = 2
    start = {
        COMPARISON_KEY: request, "level": 29, "world_boot_id": "boot",
        "room_vnum": "3054", "xp": 1000, "campaign_xp_loss_total": 20,
    }
    end = {**start, "xp": 900 if damage == "lost_xp" else 1000}
    current = {
        **end, "xp": 800, "campaign_xp_loss_total": 220,
        "campaign_source_ranked_xp_loss_policies": [{"policy_id": "closed"}],
    }
    if damage == "changed_boot":
        current["world_boot_id"] = "new"
    if damage == "changed_level":
        current["level"] = 30
    if damage == "changed_plan":
        current[COMPARISON_KEY] = {**request, "keyword": "other"}
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        run = storage.create_run(scenario_name="comparison", scenario_path=Path("character.yaml"))
        commands = ["eq all", "inventory", "compare branch"]
        if damage == "wielded":
            commands.append("wield branch")
        if damage == "incomplete":
            commands.pop(0)
        for command in commands:
            storage.record_event(run, kind="decision", payload={"command": command, "reason": REASON})
        if damage == "oversized":
            for _ in range(128):
                storage.record_event(run, kind="response", payload={"text": "healer chatter"})
        storage.record_event(run, kind="state", payload={
            "state": "failed", "error": "different" if damage == "wrong_failure" else FAILURE,
            "completed_kills": [], "objective_kills": [],
        })
        storage.finish_run(run, status="failed", error=FAILURE)
        segment = {
            "phase": "hunt" if damage == "wrong_phase" else "compare-carried-weapon",
            "status": "failed", "run_id": run,
            "error": f"compare-carried-weapon segment failed: {FAILURE}",
            "start_state_json": json.dumps(start), "end_state_json": json.dumps(end),
        }
        repaired = _repair_dispatched_weapon_comparison(
            storage, current, [] if damage == "missing_segment" else [segment],
        )
        if damage is not None:
            assert repaired == current
            return
        assert repaired[COMPARISON_KEY]["stage"] == "failed"
        assert repaired[COMPARISON_KEY]["commands"] == 3
        assert repaired[COMPARISON_KEY]["terminal_audit_recovered_from_run"] == run
        assert repaired["xp"] == 800
        assert repaired["campaign_xp_loss_total"] == 220
        assert repaired["campaign_source_ranked_xp_loss_policies"] == current["campaign_source_ranked_xp_loss_policies"]
        assert current[COMPARISON_KEY]["stage"] == "dispatched"
        assert _repair_dispatched_weapon_comparison(storage, repaired, [segment]) == repaired
        retry = weapon_comparison_request(PLAN, repaired[COMPARISON_KEY], level=29, boot_id="boot")
        assert retry["prompt_repair_of"] == repaired[COMPARISON_KEY]


def test_comparison_terminal_failure_is_merged_into_campaign_checkpoint(tmp_path):
    request = {**PLAN, "level": 29, "boot_id": "boot", "stage": "dispatched"}
    audit = {**request, "stage": "failed", "failure": FAILURE, "commands": 3}
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        run = storage.create_run(scenario_name="comparison:Testwarrior", scenario_path=Path("character.yaml"))
        storage.record_event(run, kind="state", payload={
            "state": "failed", "error": FAILURE, COMPARISON_KEY: audit,
        })
        storage.finish_run(run, status="failed", error=FAILURE)
        previous = {"level": 29, "xp": 1000, "campaign_xp_loss_total": 20, COMPARISON_KEY: request}
        result = _campaign_failure_state_from_run(storage, run, previous, character_name="Testwarrior")
    assert result[COMPARISON_KEY] == audit
    assert result["xp"] == 1000
    assert result["campaign_xp_loss_total"] == 20
