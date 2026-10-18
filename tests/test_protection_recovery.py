from pathlib import Path
import json

from dd4tester.campaign import (
    _PROTECTION_RECOVERY_KEY,
    _merge_protection_recovery_metadata,
    _repair_protection_recovery_metadata,
    _select_preferred_moria_sanctuary_recovery_candidate,
)
from dd4tester.progression import ProgressionPolicy
from dd4tester.hunt_candidates import load_world_source
from tests.test_caerlin_sanctuary_recovery import _level_39_healer_state


SOURCE_DIRECTORY = Path("runs/dd4-source/server/area")


def _research_policy(policy_id: str) -> ProgressionPolicy:
    return ProgressionPolicy(
        policy_id=policy_id,
        minimum_level=39,
        maximum_level=39,
        status="research",
        execution="moria-sanctuary-hunt",
        summary="test recovery policy",
        evidence=(),
        practice_skill=None,
    )


def _recovery_state(route: str) -> dict[str, object]:
    return {
        "world_boot_id": "test-boot",
        "level": 39,
        "xp": 1_000_000,
        "campaign_objective_kills": [],
        "campaign_fastwalk_consider_outcomes": {"target": True},
        "fastwalk_route": route,
    }


def test_protection_recovery_marker_counts_consecutive_losses() -> None:
    first = _recovery_state("source sanctuary reserve alchemist 927")
    first_merged = _merge_protection_recovery_metadata(
        first,
        policy=_research_policy("source-ranked-sanctuary-reserve-19-20"),
        xp_delta=-683,
        previous=first,
    )
    assert first_merged[_PROTECTION_RECOVERY_KEY]["loss_count"] == 1

    second = {
        **first_merged,
        "fastwalk_route": "source sanctuary reserve alchemist 927",
    }
    second_merged = _merge_protection_recovery_metadata(
        second,
        policy=_research_policy("source-ranked-sanctuary-recovery-2-100"),
        xp_delta=-651,
        previous=first_merged,
    )
    marker = second_merged[_PROTECTION_RECOVERY_KEY]
    assert marker["loss_count"] == 2
    assert marker["failed_route"] == "source sanctuary reserve alchemist 927"


def test_protection_recovery_prefers_moria_purple_potion_carrier() -> None:
    world = load_world_source(
        SOURCE_DIRECTORY,
        include_all_areas=True,
        include_all_objects=True,
    )
    state = _level_39_healer_state()

    selection = _select_preferred_moria_sanctuary_recovery_candidate(
        state,
        source_directory=SOURCE_DIRECTORY,
        source_world=world,
    )

    assert selection is not None
    candidate, object_vnums = selection
    assert (candidate.mobile_vnum, candidate.room_vnum) == (4055, 4064)
    assert object_vnums == (4050,)


def test_protection_recovery_repair_counts_prior_route_loss() -> None:
    def segment(
        segment_id: int,
        phase: str,
        start_xp: int,
        end_xp: int,
        route: str,
    ) -> dict[str, object]:
        start = {
            "level": 39,
            "xp": start_xp,
            "world_boot_id": "test-boot",
        }
        end = {
            **start,
            "xp": end_xp,
            "campaign_fastwalk_consider_outcomes": {"target": True},
            "campaign_objective_kills": [],
            "campaign_fastwalk_abort_reason": (
                "field combat aborted for safety: one observed incoming round "
                "would cross the 20% health floor"
            ),
            "fastwalk_route": route,
        }
        return {
            "id": segment_id,
            "status": "success",
            "phase": phase,
            "start_state_json": json.dumps(start),
            "end_state_json": json.dumps(end),
        }

    repaired = _repair_protection_recovery_metadata(
        {
            "level": 39,
            "world_boot_id": "test-boot",
            _PROTECTION_RECOVERY_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "policy_id": "source-ranked-sanctuary-recovery-2-100",
                "xp_delta": -651,
                "reason": "viable hunt withdrew with an XP loss before a kill",
            },
        },
        [
            segment(
                1,
                "source-ranked-sanctuary-reserve-19-20",
                1_000_000,
                999_317,
                "moria reserve alchemist",
            ),
            segment(
                2,
                "source-ranked-sanctuary-recovery-2-100",
                999_317,
                998_666,
                "moria recovery alchemist",
            ),
        ],
    )

    assert repaired[_PROTECTION_RECOVERY_KEY]["loss_count"] == 2
