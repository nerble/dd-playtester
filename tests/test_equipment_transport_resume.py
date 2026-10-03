from pathlib import Path

import pytest

from dd4tester.campaign import (
    CampaignRunner, CampaignSpec, _equipment_evidence_run_id,
    _run_primary_weapon_slot,
)
from dd4tester.character import CharacterSpec
from dd4tester.equipment import GearCatalog
from dd4tester.hunt_candidates import ObjectSource
from dd4tester.storage import RunStorage


SILENT_LOGIN = "Starter bot exceeded connection attempt limit"


def record_run(storage, *, error=None, command=None, response=None):
    run = storage.create_run(
        scenario_name="equipment:Testwarrior", scenario_path=Path("character.yaml"),
    )
    if command is not None:
        storage.record_event(run, kind="command", payload={"command": command})
    if response is not None:
        storage.record_event(run, kind="response", payload={"text": response})
    storage.finish_run(run, status="failed" if error else "success", error=error)
    return run


def test_silent_connections_reuse_the_latest_actual_equipment_run(tmp_path):
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        observed = record_run(storage, response="You wield a long, grey branch.\n")
        silent = [record_run(storage, error=SILENT_LOGIN) for _ in range(2)]
        rows = [{"run_id": run} for run in [observed, *silent]]
        selected = _equipment_evidence_run_id(storage, silent[-1], rows)
        assert selected == observed
        assert _run_primary_weapon_slot(storage, selected) == (True, "a long, grey branch")


@pytest.mark.parametrize("command,response,error", [
    ("look", "A guardian DISARMS you!\n", SILENT_LOGIN),
    (None, "A guardian DISARMS you!\n", "unrelated runtime failure"),
    ("eq all", "[weapon] -\n", None),
])
def test_silent_connection_does_not_skip_a_later_real_weapon_loss(
    tmp_path, command, response, error,
):
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        old = record_run(storage, response="You wield a long, grey branch.\n")
        loss = record_run(storage, command=command, response=response, error=error)
        silent = record_run(storage, error=SILENT_LOGIN)
        selected = _equipment_evidence_run_id(
            storage, silent, [{"run_id": run} for run in (old, loss, silent)],
        )
        assert selected == loss
        assert _run_primary_weapon_slot(storage, selected) == (False, None)


def test_empty_tail_does_not_start_a_wider_equipment_history_scan(tmp_path):
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        record_run(storage, response="You wield a long, grey branch.\n")
        silent = record_run(storage, error=SILENT_LOGIN)
        assert _equipment_evidence_run_id(storage, silent, []) == silent
        assert _equipment_evidence_run_id(storage, None, []) is None


@pytest.mark.parametrize("observed_weapon", [True, False])
def test_campaign_resume_does_not_reclassify_an_ambiguous_worn_name(
    tmp_path, observed_weapon,
):
    character = CharacterSpec.from_mapping({
        "name": "Testwarrior", "race": "dwarf", "gender": "neuter", "class": "warrior",
    })
    config = tmp_path / "campaign.yaml"
    spec = CampaignSpec("transport equipment", tmp_path / "character.yaml", character)
    runner = CampaignRunner(spec, config)
    runner._gear_catalog = GearCatalog({
        vnum: ObjectSource(vnum, "branch", "a long, grey branch", kind, values, 0,
                           wear_flags=1 | (1 << 13))
        for vnum, kind, values in [(6103, 1, (0, 0, 25, 0)), (6104, 5, (0, 2, 5, 7))]
    })
    state = {
        "level": 29, "xp": 577856, "world_boot_id": "boot-1", "room_vnum": "3054",
        "hp": 666, "max_hp": 666, "move": 482, "max_move": 482,
        "campaign_has_weapon": False,
        "campaign_primary_weapon": "a long, grey branch",
        "campaign_empty_equipment_categories": [],
        "campaign_worn_equipment": ["a long, grey branch"],
        "equipment": [{"slot": "wield", "wear_loc": 16, "vnum": 6104,
                       "name": "a long, grey branch", "item_type": 5, "level": 15}],
    }
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        campaign_id, _ = runner._open_campaign(storage)
        observed = record_run(
            storage, command="eq all",
            response="[weapon] a long, grey branch\n" if observed_weapon else "[weapon] -\n",
        )
        silent = record_run(storage, error=SILENT_LOGIN)
        for run in (observed, silent):
            segment = storage.start_campaign_segment(campaign_id, phase="quest-cooldown", start_state=state)
            storage.finish_campaign_segment(
                segment, status="ready", run_id=run, end_state=state,
                command_count=0 if run == silent else 1, duration_seconds=1,
            )
        storage.record_campaign_checkpoint(
            campaign_id, segment_id=segment, run_id=silent, phase="quest-cooldown",
            reason="transport_unavailable_before_login", state=state,
        )
        _, resumed = runner._open_campaign(storage)
        assert resumed["campaign_has_weapon"] is observed_weapon
        assert resumed["campaign_primary_weapon"] == ("a long, grey branch" if observed_weapon else None)
        assert ("wield" in resumed["campaign_empty_equipment_categories"]) is not observed_weapon
