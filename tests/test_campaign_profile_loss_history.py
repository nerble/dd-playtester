from __future__ import annotations

from pathlib import Path

from dd4tester.campaign import _reconcile_same_profile_source_ranked_losses
from dd4tester.storage import RunStorage


POLICY = "source-ranked-hunt-lotus-temple-10727-10820-39"
BOOT = "boot-2026-10-14"


def _state(*, xp: int = 40_000, character_class: str = "Warrior") -> dict:
    return {
        "name": "Dorrik",
        "race": "Dwarf",
        "character_class": character_class,
        "subclass": "Knight",
        "level": 39,
        "xp": xp,
        "progress_source": "gmcp",
        "world_boot_id": BOOT,
    }


def _campaign(storage, *, name: str, profile: Path, state: dict) -> int:
    campaign_id = storage.create_campaign(
        name=name,
        config_path=profile.with_name(f"{name}.yaml"),
        character_profile_path=profile,
        target_level=100,
    )
    segment_id = storage.start_campaign_segment(
        campaign_id,
        phase=POLICY,
        start_state=state,
    )
    storage.finish_campaign_segment(
        segment_id,
        status="success",
        run_id=None,
        end_state=state,
        command_count=0,
        duration_seconds=0,
    )
    storage.record_campaign_checkpoint(
        campaign_id,
        segment_id=segment_id,
        run_id=None,
        phase=POLICY,
        reason="test_checkpoint",
        state=state,
    )
    return campaign_id


def _saved_loss(segment_id: int) -> dict:
    return {
        "boot_id": BOOT,
        "level": 39,
        "loss_count": 1,
        "loss_event_id": segment_id,
        "policy_id": POLICY,
        "xp_delta": -1000,
    }


def test_same_profile_loss_is_restored_before_source_policy_selection(tmp_path) -> None:
    profile = tmp_path / "character.yaml"
    current_state = _state()
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        current_campaign = _campaign(
            storage, name="primary", profile=profile, state=current_state,
        )
        foreign_campaign = storage.create_campaign(
            name="legacy",
            config_path=tmp_path / "legacy.yaml",
            character_profile_path=profile,
            target_level=100,
        )
        loss_segment = storage.start_campaign_segment(
            foreign_campaign,
            phase=POLICY,
            start_state=_state(),
        )
        foreign_state = _state()
        foreign_state["campaign_source_ranked_xp_loss_policies"] = [
            _saved_loss(loss_segment)
        ]
        storage.record_campaign_checkpoint(
            foreign_campaign,
            segment_id=loss_segment,
            run_id=None,
            phase=POLICY,
            reason="test_loss",
            state=foreign_state,
        )

        reconciled = _reconcile_same_profile_source_ranked_losses(
            storage,
            campaign_id=current_campaign,
            character_profile_path=profile,
            state=current_state,
        )

    assert reconciled["campaign_source_ranked_xp_loss_policies"] == [
        _saved_loss(loss_segment)
    ]


def test_later_verified_useful_kill_clears_only_the_older_exact_loss(tmp_path) -> None:
    profile = tmp_path / "character.yaml"
    current_state = _state()
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        current_campaign = _campaign(
            storage, name="primary", profile=profile, state=current_state,
        )
        foreign_campaign = storage.create_campaign(
            name="legacy",
            config_path=tmp_path / "legacy.yaml",
            character_profile_path=profile,
            target_level=100,
        )
        loss_segment = storage.start_campaign_segment(
            foreign_campaign,
            phase=POLICY,
            start_state=_state(),
        )
        foreign_state = _state()
        foreign_state["campaign_source_ranked_xp_loss_policies"] = [
            _saved_loss(loss_segment)
        ]
        storage.record_campaign_checkpoint(
            foreign_campaign,
            segment_id=loss_segment,
            run_id=None,
            phase=POLICY,
            reason="test_loss",
            state=foreign_state,
        )

        run_id = storage.create_run(
            scenario_name="later-exact-target-kill",
            scenario_path=tmp_path / "scenario.yaml",
        )
        storage.set_run_boot_id(run_id, BOOT)
        next_start = _state(xp=40_000)
        kill_segment = storage.start_campaign_segment(
            current_campaign,
            phase=POLICY,
            start_state=next_start,
        )
        next_end = _state(xp=40_500)
        storage.record_mob_kill(
            run_id,
            character_name="Dorrik",
            boot_id=BOOT,
            mob_name="statue of the Golden Buddha",
            xp_gained=500,
            source_mobile_vnum=10727,
            source_policy_id=POLICY,
        )
        storage.finish_run(
            run_id,
            status="success",
            execution_status="success",
            objective_outcome="not_achieved",
            safety_outcome="safe",
        )
        storage.finish_campaign_segment(
            kill_segment,
            status="success",
            run_id=run_id,
            end_state=next_end,
            command_count=1,
            duration_seconds=1,
        )

        reconciled = _reconcile_same_profile_source_ranked_losses(
            storage,
            campaign_id=current_campaign,
            character_profile_path=profile,
            state=current_state,
        )

    assert "campaign_source_ranked_xp_loss_policies" not in reconciled


def test_current_campaign_loss_survives_an_older_useful_kill(tmp_path) -> None:
    profile = tmp_path / "character.yaml"
    current_state = _state()
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        current_campaign = _campaign(
            storage, name="primary", profile=profile, state=current_state,
        )
        foreign_campaign = storage.create_campaign(
            name="legacy",
            config_path=tmp_path / "legacy.yaml",
            character_profile_path=profile,
            target_level=100,
        )
        old_loss_segment = storage.start_campaign_segment(
            foreign_campaign,
            phase=POLICY,
            start_state=_state(),
        )
        foreign_state = _state()
        foreign_state["campaign_source_ranked_xp_loss_policies"] = [
            _saved_loss(old_loss_segment)
        ]
        storage.record_campaign_checkpoint(
            foreign_campaign,
            segment_id=old_loss_segment,
            run_id=None,
            phase=POLICY,
            reason="test_loss",
            state=foreign_state,
        )

        useful_run = storage.create_run(
            scenario_name="useful-exact-target-kill",
            scenario_path=tmp_path / "useful.yaml",
        )
        storage.set_run_boot_id(useful_run, BOOT)
        useful_segment = storage.start_campaign_segment(
            current_campaign,
            phase=POLICY,
            start_state=_state(),
        )
        storage.record_mob_kill(
            useful_run,
            character_name="Dorrik",
            boot_id=BOOT,
            mob_name="the measured target",
            xp_gained=500,
            source_mobile_vnum=10727,
            source_policy_id=POLICY,
        )
        storage.finish_run(
            useful_run,
            status="success",
            execution_status="success",
            objective_outcome="not_achieved",
            safety_outcome="safe",
        )
        storage.finish_campaign_segment(
            useful_segment,
            status="success",
            run_id=useful_run,
            end_state=_state(xp=40_500),
            command_count=1,
            duration_seconds=1,
        )

        later_loss_segment = storage.start_campaign_segment(
            current_campaign,
            phase=POLICY,
            start_state=_state(xp=40_500),
        )
        later_loss_state = _state(xp=40_000)
        later_loss_state["campaign_source_ranked_xp_loss_policies"] = [
            _saved_loss(later_loss_segment)
        ]
        storage.finish_campaign_segment(
            later_loss_segment,
            status="success",
            run_id=None,
            end_state=later_loss_state,
            command_count=1,
            duration_seconds=1,
        )

        reconciled = _reconcile_same_profile_source_ranked_losses(
            storage,
            campaign_id=current_campaign,
            character_profile_path=profile,
            state=current_state,
            campaign_segments=storage.list_campaign_segments(current_campaign),
        )

    record = reconciled["campaign_source_ranked_xp_loss_policies"][0]
    assert record["loss_event_id"] == later_loss_segment
    assert record["loss_count"] == 1


def test_current_checkpoint_tail_preserves_compact_loss_count(tmp_path) -> None:
    profile = tmp_path / "character.yaml"
    current_state = _state()
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        current_campaign = _campaign(
            storage, name="primary", profile=profile, state=current_state,
        )
        loss_segment = storage.start_campaign_segment(
            current_campaign,
            phase=POLICY,
            start_state=current_state,
        )
        loss_state = _state(xp=39_000)
        loss_state["campaign_source_ranked_xp_loss_policies"] = [
            _saved_loss(loss_segment)
        ]
        storage.finish_campaign_segment(
            loss_segment,
            status="success",
            run_id=None,
            end_state=loss_state,
            command_count=1,
            duration_seconds=1,
        )
        compact_state = _state(xp=39_000)
        compact_state["campaign_source_ranked_xp_loss_policies"] = [
            {**_saved_loss(loss_segment), "loss_count": 4}
        ]
        storage.record_campaign_checkpoint(
            current_campaign,
            segment_id=loss_segment,
            run_id=None,
            phase=POLICY,
            reason="compact_loss_checkpoint",
            state=compact_state,
        )

        reconciled = _reconcile_same_profile_source_ranked_losses(
            storage,
            campaign_id=current_campaign,
            character_profile_path=profile,
            state=current_state,
            campaign_segments=storage.list_campaign_segments(current_campaign),
        )

    record = reconciled["campaign_source_ranked_xp_loss_policies"][0]
    assert record["loss_event_id"] == loss_segment
    assert record["loss_count"] == 4


def test_distinct_same_profile_losses_accumulate_across_campaigns(tmp_path) -> None:
    profile = tmp_path / "character.yaml"
    current_state = _state()
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        current_campaign = _campaign(
            storage, name="primary", profile=profile, state=current_state,
        )
        loss_ids = []
        for name in ("legacy-one", "legacy-two"):
            foreign_campaign = storage.create_campaign(
                name=name,
                config_path=tmp_path / f"{name}.yaml",
                character_profile_path=profile,
                target_level=100,
            )
            loss_segment = storage.start_campaign_segment(
                foreign_campaign,
                phase=POLICY,
                start_state=_state(),
            )
            loss_ids.append(loss_segment)
            foreign_state = _state()
            foreign_state["campaign_source_ranked_xp_loss_policies"] = [
                _saved_loss(loss_segment)
            ]
            storage.record_campaign_checkpoint(
                foreign_campaign,
                segment_id=loss_segment,
                run_id=None,
                phase=POLICY,
                reason="test_loss",
                state=foreign_state,
            )

        reconciled = _reconcile_same_profile_source_ranked_losses(
            storage,
            campaign_id=current_campaign,
            character_profile_path=profile,
            state=current_state,
        )

    record = reconciled["campaign_source_ranked_xp_loss_policies"][0]
    assert record["loss_count"] == 2
    assert record["loss_event_id"] == max(loss_ids)


def test_other_profile_or_ineligible_kills_do_not_clear_loss(tmp_path) -> None:
    profile = tmp_path / "character.yaml"
    current_state = _state()
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        current_campaign = _campaign(
            storage, name="primary", profile=profile, state=current_state,
        )
        foreign_campaign = storage.create_campaign(
            name="legacy",
            config_path=tmp_path / "legacy.yaml",
            character_profile_path=profile,
            target_level=100,
        )
        loss_segment = storage.start_campaign_segment(
            foreign_campaign,
            phase=POLICY,
            start_state=_state(),
        )
        foreign_state = _state()
        foreign_state["campaign_source_ranked_xp_loss_policies"] = [
            _saved_loss(loss_segment)
        ]
        storage.record_campaign_checkpoint(
            foreign_campaign,
            segment_id=loss_segment,
            run_id=None,
            phase=POLICY,
            reason="test_loss",
            state=foreign_state,
        )

        unrelated_campaign = storage.create_campaign(
            name="same-name-other-character",
            config_path=tmp_path / "other.yaml",
            character_profile_path=tmp_path / "other-character.yaml",
            target_level=100,
        )
        unrelated_start = _state()
        unrelated_run = storage.create_run(
            scenario_name="unrelated-kill",
            scenario_path=tmp_path / "other-scenario.yaml",
        )
        unrelated_segment = storage.start_campaign_segment(
            unrelated_campaign,
            phase=POLICY,
            start_state=unrelated_start,
        )
        storage.record_mob_kill(
            unrelated_run,
            character_name="Dorrik",
            boot_id=BOOT,
            mob_name="statue of the Golden Buddha",
            xp_gained=500,
            source_mobile_vnum=10727,
            source_policy_id=POLICY,
        )
        storage.finish_campaign_segment(
            unrelated_segment,
            status="success",
            run_id=unrelated_run,
            end_state=_state(xp=40_500),
            command_count=1,
            duration_seconds=1,
        )

        ineligible_run = storage.create_run(
            scenario_name="below-band-kill",
            scenario_path=tmp_path / "below-band.yaml",
        )
        ineligible_segment = storage.start_campaign_segment(
            current_campaign,
            phase=POLICY,
            start_state=_state(),
        )
        storage.record_mob_kill(
            ineligible_run,
            character_name="Dorrik",
            boot_id=BOOT,
            mob_name="statue of the Golden Buddha",
            xp_gained=500,
            source_mobile_vnum=10727,
            source_policy_id=POLICY,
            below_useful_band=True,
        )
        storage.finish_run(
            ineligible_run,
            status="success",
            execution_status="success",
            objective_outcome="not_achieved",
            safety_outcome="safe",
        )
        storage.finish_campaign_segment(
            ineligible_segment,
            status="success",
            run_id=ineligible_run,
            end_state=_state(xp=40_500),
            command_count=1,
            duration_seconds=1,
        )

        retained = _reconcile_same_profile_source_ranked_losses(
            storage,
            campaign_id=current_campaign,
            character_profile_path=profile,
            state=current_state,
        )

        current_class_mismatch = _reconcile_same_profile_source_ranked_losses(
            storage,
            campaign_id=current_campaign,
            character_profile_path=profile,
            state=_state(character_class="Mage"),
        )

    assert current_class_mismatch == _state(character_class="Mage")
    assert current_class_mismatch.get(
        "campaign_source_ranked_xp_loss_policies"
    ) is None
    assert retained["campaign_source_ranked_xp_loss_policies"] == [
        _saved_loss(loss_segment)
    ]
