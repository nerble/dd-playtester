import json

import json

import pytest

from dd4tester.campaign import (
    _campaign_segment_end_state,
    _carry_pounding_weapon_rearm_attempt,
    _pounding_weapon_rearm_attempted,
)
from dd4tester.campaign_migrations import (
    _repair_pounding_weapon_rearm_attempt,
    _restore_pounding_weapon_rearm_attempt,
)
from dd4tester.equipment import GearCatalog
from dd4tester.starter import _city_rearm_objective_payload


def _rearm_state() -> dict[str, object]:
    return {
        "level": 29,
        "xp": 611231,
        "world_boot_id": "Sun Sep 27 23:55:43 2026",
        "campaign_source_revision": "source-rev-1",
        "campaign_has_weapon": True,
        "campaign_primary_weapon": "enchanted hammer",
        "room_vnum": "3054",
        "dead": False,
        "in_combat": False,
        "xp_loss_observed": False,
        "xp_loss_total": 0,
        "campaign_xp_loss_total": 38526,
        "campaign_policy_revision": 338,
    }


def _failed_rearm_segment() -> dict[str, object]:
    snapshot = {
        "level": 29,
        "xp": 611231,
        "world_boot_id": "Sun Sep 27 23:55:43 2026",
        "campaign_source_revision": "source-rev-1",
        "campaign_has_weapon": True,
        "campaign_primary_weapon": "enchanted hammer",
        "room_vnum": "3054",
        "dead": False,
        "in_combat": False,
        "xp_loss_observed": False,
        "xp_loss_total": 0,
        "campaign_xp_loss_total": 38526,
    }
    return {
        "id": 15661,
        "run_id": 16139,
        "phase": "rearm-primary-weapon",
        "status": "failed",
        "execution_status": "failed",
        "safety_outcome": "safe",
        "command_count": 38,
        "error": (
            "rearm-primary-weapon segment failed: Dave's located room "
            "'end of penny lane' had no source-safe sweep within 22 commands "
            "and the observed movement budget; returned to the healer "
            "without retrying"
        ),
        "start_state_json": json.dumps(snapshot),
        "end_state_json": json.dumps(snapshot),
    }


def test_exact_safe_rearm_route_failure_is_persisted_for_this_frontier() -> None:
    migrated = _repair_pounding_weapon_rearm_attempt(
        _rearm_state(),
        [_failed_rearm_segment()],
    )

    assert _pounding_weapon_rearm_attempted(migrated)
    marker = migrated["campaign_pounding_weapon_rearm_attempt"]
    assert marker["run_id"] == 16139
    assert marker["segment_id"] == 15661


def test_completed_empty_dave_sweep_is_persisted_for_this_frontier() -> None:
    segment = _failed_rearm_segment()
    segment["error"] = (
        "rearm-primary-weapon segment failed: Dave was absent from every "
        "source room in the single bounded locator sweep; returned to the "
        "healer without retrying"
    )

    migrated = _repair_pounding_weapon_rearm_attempt(
        _rearm_state(),
        [segment],
    )

    assert _pounding_weapon_rearm_attempted(migrated)
    marker = migrated["campaign_pounding_weapon_rearm_attempt"]
    assert marker["run_id"] == 16139
    assert marker["segment_id"] == 15661


def test_unmapped_dave_location_is_persisted_for_this_frontier() -> None:
    segment = _failed_rearm_segment()
    segment["error"] = (
        "rearm-primary-weapon segment failed: Dave's located room 'park road' "
        "had no bounded source-reachable room set; returned to the healer "
        "without retrying"
    )

    migrated = _repair_pounding_weapon_rearm_attempt(
        _rearm_state(),
        [segment],
    )

    assert _pounding_weapon_rearm_attempted(migrated)
    marker = migrated["campaign_pounding_weapon_rearm_attempt"]
    assert marker["run_id"] == 16139
    assert marker["segment_id"] == 15661


@pytest.mark.parametrize(
    "segment_change",
    [{}, {"run_id": None}, {"command_count": 0}, {"safety_outcome": "unsafe"}],
)
def test_empty_dave_locator_closes_only_a_completed_safe_optional_attempt(
    segment_change: dict[str, object],
) -> None:
    segment = _failed_rearm_segment()
    segment["error"] = (
        "rearm-primary-weapon segment failed: Dave was absent from the one "
        "live locator check; returned to the healer without retrying"
    )
    segment.update(segment_change)

    migrated = _repair_pounding_weapon_rearm_attempt(_rearm_state(), [segment])

    assert _pounding_weapon_rearm_attempted(migrated) is (not segment_change)


def test_rearm_marker_survives_progress_but_expires_on_frontier_change() -> None:
    previous = _rearm_state()
    previous["campaign_pounding_weapon_rearm_attempt"] = {
        "level": 29,
        "boot_id": previous["world_boot_id"],
        "source_revision": previous["campaign_source_revision"],
        "primary_weapon": "enchanted hammer",
    }
    progressed = {**_rearm_state(), "xp": 612000}

    carried = _carry_pounding_weapon_rearm_attempt(previous, progressed)
    assert _pounding_weapon_rearm_attempted(carried)
    assert carried["campaign_pounding_weapon_rearm_attempt"] == previous[
        "campaign_pounding_weapon_rearm_attempt"
    ]

    changed = {**progressed, "world_boot_id": "new boot"}
    expired = _carry_pounding_weapon_rearm_attempt(previous, changed)
    assert not _pounding_weapon_rearm_attempted(expired)
    assert "campaign_pounding_weapon_rearm_attempt" not in expired


def test_rearm_marker_survives_unrelated_segment_checkpoint() -> None:
    previous = _rearm_state()
    previous["campaign_pounding_weapon_rearm_attempt"] = {
        "level": 29,
        "boot_id": previous["world_boot_id"],
        "source_revision": previous["campaign_source_revision"],
        "primary_weapon": "enchanted hammer",
    }
    current = _rearm_state()

    merged = _campaign_segment_end_state(
        previous,
        current,
        execution="source-ranked-hunt",
        policy_id="source-ranked-hunt-test",
    )

    assert _pounding_weapon_rearm_attempted(merged)


def test_lost_rearm_marker_is_restored_from_a_matching_recent_checkpoint() -> None:
    marker = {
        "level": 29,
        "boot_id": "Sun Sep 27 23:55:43 2026",
        "source_revision": "source-rev-1",
        "primary_weapon": "enchanted hammer",
        "run_id": 16139,
        "segment_id": 15661,
    }
    checkpoint_state = {
        **_rearm_state(),
        "campaign_pounding_weapon_rearm_attempt": marker,
    }
    current_state = {**_rearm_state(), "xp": 610941}

    restored = _restore_pounding_weapon_rearm_attempt(
        current_state,
        [{"state_json": json.dumps(checkpoint_state)}],
    )

    assert _pounding_weapon_rearm_attempted(restored)
    assert restored["campaign_pounding_weapon_rearm_attempt"] == marker


@pytest.mark.parametrize(
    "state_change",
    [
        {"world_boot_id": "new boot"},
        {"level": 30},
        {"campaign_source_revision": "new source"},
        {"campaign_primary_weapon": "different weapon"},
        {"campaign_has_weapon": False},
    ],
)
def test_checkpoint_rearm_marker_is_not_restored_after_frontier_changes(
    state_change: dict[str, object],
) -> None:
    marker = {
        "level": 29,
        "boot_id": "Sun Sep 27 23:55:43 2026",
        "source_revision": "source-rev-1",
        "primary_weapon": "enchanted hammer",
    }
    checkpoint_state = {
        **_rearm_state(),
        "campaign_pounding_weapon_rearm_attempt": marker,
    }
    current_state = {**_rearm_state(), **state_change}

    restored = _restore_pounding_weapon_rearm_attempt(
        current_state,
        [{"state_json": json.dumps(checkpoint_state)}],
    )

    assert not _pounding_weapon_rearm_attempted(restored)
    assert "campaign_pounding_weapon_rearm_attempt" not in restored


def test_pounding_rearm_objective_does_not_require_live_policy_adapter() -> None:
    objective = _city_rearm_objective_payload(
        pounding=True,
        gear_catalog=GearCatalog({}),
        policy=None,
        preserved_primary_weapon_vnum=None,
        character_class="warrior",
    )

    assert objective == {"weapon_role": "pounding"}


@pytest.mark.parametrize(
    ("state_change", "segment_change"),
    [
        ({"world_boot_id": "new boot"}, {}),
        ({"level": 30}, {}),
        ({"campaign_source_revision": "new source"}, {}),
        ({"campaign_primary_weapon": "different weapon"}, {}),
        ({"campaign_has_weapon": False}, {}),
        ({"room_vnum": "3005"}, {}),
        ({}, {"safety_outcome": "unsafe"}),
        ({}, {"end_room": "2000"}),
        ({}, {"end_xp": 610000}),
        ({}, {"end_loss": 1}),
    ],
)
def test_rearm_failure_marker_stays_closed_when_evidence_changes(
    state_change: dict[str, object],
    segment_change: dict[str, object],
) -> None:
    state = {**_rearm_state(), **state_change}
    segment = _failed_rearm_segment()
    if "safety_outcome" in segment_change:
        segment["safety_outcome"] = segment_change["safety_outcome"]
    if "end_room" in segment_change:
        snapshot = json.loads(segment["end_state_json"])
        snapshot["room_vnum"] = segment_change["end_room"]
        segment["end_state_json"] = json.dumps(snapshot)
    if "end_xp" in segment_change:
        snapshot = json.loads(segment["end_state_json"])
        snapshot["xp"] = segment_change["end_xp"]
        segment["end_state_json"] = json.dumps(snapshot)
    if "end_loss" in segment_change:
        snapshot = json.loads(segment["end_state_json"])
        snapshot["campaign_xp_loss_total"] += segment_change["end_loss"]
        segment["end_state_json"] = json.dumps(snapshot)

    migrated = _repair_pounding_weapon_rearm_attempt(state, [segment])

    assert not _pounding_weapon_rearm_attempted(migrated)
    assert "campaign_pounding_weapon_rearm_attempt" not in migrated
