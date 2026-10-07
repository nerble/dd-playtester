from __future__ import annotations

import json

import pytest

from dd4tester.campaign import _carry_sanctuary_resource_attempts
from dd4tester.campaign_migrations import restore_checkpointed_sanctuary_attempts


POLICY_ID = "source-ranked-sanctuary-recovery-2-100"
BOOT_ID = "Sun Sep 27 23:55:43 2026"


def _state() -> dict[str, object]:
    return {
        "level": 29,
        "world_boot_id": BOOT_ID,
        "campaign_research_results": {},
    }


def _checkpoint_attempt(count: int = 2, **fields: object) -> dict[str, object]:
    return {
        "boot_id": BOOT_ID,
        "level": 29,
        "count": count,
        **fields,
    }


def test_unrelated_segment_carries_same_frontier_sanctuary_attempts() -> None:
    previous = {
        **_state(),
        "campaign_sanctuary_resource_attempts": {
            POLICY_ID: _checkpoint_attempt(),
        },
    }

    carried = _carry_sanctuary_resource_attempts(
        previous,
        _state(),
        policy_id="source-ranked-hunt-test",
    )

    assert carried["campaign_sanctuary_resource_attempts"][POLICY_ID][
        "count"
    ] == 2


@pytest.mark.parametrize(
    "state_change",
    [
        {"level": 30},
        {"world_boot_id": "new boot"},
    ],
)
def test_unrelated_segment_does_not_carry_attempts_to_a_new_frontier(
    state_change: dict[str, object],
) -> None:
    previous = {
        **_state(),
        "campaign_sanctuary_resource_attempts": {
            POLICY_ID: _checkpoint_attempt(),
        },
    }

    carried = _carry_sanctuary_resource_attempts(
        previous,
        {**_state(), **state_change},
        policy_id="source-ranked-hunt-test",
    )

    assert "campaign_sanctuary_resource_attempts" not in carried


def test_unrelated_segment_does_not_consume_area_reset_recheck() -> None:
    previous = {
        **_state(),
        "campaign_sanctuary_resource_attempts": {
            POLICY_ID: _checkpoint_attempt(),
        },
    }
    current = {
        **_state(),
        "campaign_sanctuary_area_reset_recheck": {
            "boot_id": BOOT_ID,
            "level": 29,
            "status": "pending",
            "policy_ids": [POLICY_ID],
        },
    }

    carried = _carry_sanctuary_resource_attempts(
        previous,
        current,
        policy_id="source-ranked-hunt-test",
    )

    assert "campaign_sanctuary_resource_attempts" not in carried


def test_lost_attempt_limit_is_restored_from_matching_checkpoint_tail() -> None:
    previous_checkpoint = {
        **_state(),
        "campaign_sanctuary_resource_attempts": {
            POLICY_ID: _checkpoint_attempt(),
        },
    }
    current = {
        **_state(),
        "campaign_sanctuary_resource_attempts": {
            POLICY_ID: _checkpoint_attempt(count=1),
        },
    }

    restored = restore_checkpointed_sanctuary_attempts(
        current,
        [{"state_json": json.dumps(previous_checkpoint)}],
    )

    assert restored["campaign_sanctuary_resource_attempts"][POLICY_ID][
        "count"
    ] == 2


@pytest.mark.parametrize(
    "state_change",
    [
        {"level": 30},
        {"world_boot_id": "new boot"},
        {
            "campaign_sanctuary_area_reset_recheck": {
                "boot_id": BOOT_ID,
                "level": 29,
                "status": "pending",
                "policy_ids": [POLICY_ID],
            },
        },
        {
            "campaign_research_results": {
                POLICY_ID: {
                    "boot_id": BOOT_ID,
                    "required_object_acquired": True,
                },
            },
        },
    ],
)
def test_checkpoint_attempt_repair_respects_reset_and_success_boundaries(
    state_change: dict[str, object],
) -> None:
    checkpoint_state = {
        **_state(),
        "campaign_sanctuary_resource_attempts": {
            POLICY_ID: _checkpoint_attempt(),
        },
    }

    restored = restore_checkpointed_sanctuary_attempts(
        {**_state(), **state_change},
        [{"state_json": json.dumps(checkpoint_state)}],
    )

    attempts = restored.get("campaign_sanctuary_resource_attempts", {})
    assert POLICY_ID not in attempts


def test_checkpoint_attempt_repair_preserves_area_reset_cycle_evidence() -> None:
    checkpoint_state = {
        **_state(),
        "campaign_sanctuary_area_reset_recheck": {
            "boot_id": BOOT_ID,
            "level": 29,
            "status": "pending",
            "policy_ids": [POLICY_ID],
        },
        "campaign_sanctuary_resource_attempts": {
            POLICY_ID: _checkpoint_attempt(
                count=0,
                area_reset_cycle=1,
            ),
        },
    }
    current = {
        **_state(),
        "campaign_sanctuary_resource_attempts": {
            POLICY_ID: _checkpoint_attempt(count=2),
        },
        "campaign_sanctuary_area_reset_recheck": checkpoint_state[
            "campaign_sanctuary_area_reset_recheck"
        ],
    }

    restored = restore_checkpointed_sanctuary_attempts(
        current,
        [{"state_json": json.dumps(checkpoint_state)}],
    )

    assert (
        restored["campaign_sanctuary_resource_attempts"][POLICY_ID][
            "area_reset_cycle"
        ]
        == 1
    )
    assert restored["campaign_sanctuary_resource_attempts"][POLICY_ID][
        "count"
    ] == 0


def test_same_reset_cycle_attempt_survives_an_unrelated_segment() -> None:
    reset_record = _checkpoint_attempt(
        count=1,
        area_reset_cycle=1,
        area_reset_after_segment_id=120,
    )
    previous = {
        **_state(),
        "campaign_sanctuary_resource_attempts": {POLICY_ID: reset_record},
    }
    current = {
        **_state(),
        "campaign_sanctuary_area_reset_recheck": {
            "boot_id": BOOT_ID,
            "level": 29,
            "status": "attempted",
            "dispatch_started": True,
            "after_segment_id": 120,
            "policy_ids": [POLICY_ID],
        },
    }

    carried = _carry_sanctuary_resource_attempts(
        previous,
        current,
        policy_id="source-ranked-hunt-test",
    )

    assert carried["campaign_sanctuary_resource_attempts"][POLICY_ID] == reset_record


def test_checkpoint_attempt_repair_does_not_copy_a_stale_lower_count() -> None:
    current = {
        **_state(),
        "campaign_sanctuary_resource_attempts": {
            POLICY_ID: _checkpoint_attempt(count=3),
        },
    }
    checkpoint_state = {
        **_state(),
        "campaign_sanctuary_resource_attempts": {
            POLICY_ID: _checkpoint_attempt(count=2),
        },
    }

    restored = restore_checkpointed_sanctuary_attempts(
        current,
        [{"state_json": json.dumps(checkpoint_state)}],
    )

    assert restored["campaign_sanctuary_resource_attempts"][POLICY_ID][
        "count"
    ] == 3
