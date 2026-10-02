import json
from pathlib import Path
from types import SimpleNamespace

import dd4tester.cli
from dd4tester.campaign import CampaignResult
from dd4tester.cli import main
from dd4tester.equipment import GearSourcePlacement
from dd4tester.lease import CampaignLease, campaign_lease_path
from dd4tester.hunt_candidates import ObjectSource, ResourcePlacement, WorldSource
from dd4tester.matrix import (
    MatrixCredentialResult,
    MatrixEntryResult,
    MatrixResult,
)
from dd4tester.money import MoneyLoopResult
from dd4tester.runner import RunResult
from dd4tester.storage import RunStorage
from dd4tester.transcript import TranscriptRecorder


def test_show_runs_lists_existing_runs(tmp_path, capsys) -> None:
    database, _transcript = _create_recorded_run(tmp_path)

    exit_code = main(["show-runs", "--database", str(database), "--limit", "5"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert str(database.resolve()) in captured.out
    assert "id\tstatus\tscenario" in captured.out
    assert "login" in captured.out
    assert "success" in captured.out


def test_large_database_inspection_uses_latest_indexed_campaign_checkpoint(
    monkeypatch,
) -> None:
    calls: list[str] = []

    class LargeStorage:
        path = SimpleNamespace(
            stat=lambda _self=None: SimpleNamespace(
                st_size=dd4tester.cli._MAX_CAMPAIGN_CHARACTER_LOOKUP_BYTES + 1
            )
        )

        def get_latest_character_state(self, character: str):
            calls.append(f"snapshot:{character}")
            return {"name": character, "level": 24}

        def get_latest_campaign_checkpoint_for_character_bounded(
            self,
            character: str,
        ):
            calls.append(f"checkpoint:{character}")
            return {
                "state_json": json.dumps(
                    {
                        "name": character,
                        "level": 24,
                        "campaign_source_ranked_below_band_exclusions": [
                            "known target"
                        ],
                    }
                )
            }

    state = dd4tester.cli._latest_inspection_state(
        LargeStorage(),
        "Kestrel",
    )

    assert state == {
        "name": "Kestrel",
        "level": 24,
        "campaign_source_ranked_below_band_exclusions": ["known target"],
    }
    assert calls == ["checkpoint:Kestrel"]


def test_autonomy_audit_can_compare_all_base_classes(capsys) -> None:
    exit_code = main(
        [
            "autonomy-audit",
            "--race",
            "human",
            "--sex",
            "female",
            "--all-classes",
            "--target-level",
            "100",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.count("Request: human/female") == 9
    assert "Combat automation: partial" in captured.out
    assert "shifter:" in captured.out


def test_autonomy_audit_rejects_subclass_with_all_classes(capsys) -> None:
    exit_code = main(
        [
            "autonomy-audit",
            "--race",
            "human",
            "--sex",
            "female",
            "--all-classes",
            "--subclass",
            "werewolf",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "cannot be combined" in captured.err


def test_show_combat_readiness_reports_output_and_blockers(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    source = tmp_path / "area"
    source.mkdir()
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        run_id = storage.create_run(
            scenario_name="readiness",
            scenario_path=tmp_path / "readiness.yaml",
        )
        storage.record_state_snapshot(
            run_id,
            source_event_id=None,
            reason="prompt_seen",
            state={
                "name": "Ararisa",
                "level": 10,
                "max_hp": 100,
                "progress": {"level": "10", "alignment": "1000"},
                "stats": {"fame": "-12"},
            },
        )
        storage.finish_run(run_id, status="success")
    world = SimpleNamespace(objects={})
    candidate = SimpleNamespace(
        target="a test sentinel",
        mobile_vnum=101,
        room_vnum=202,
        room_name="Test Room",
        status="caution",
        score=123.0,
        estimated_level_range=(9, 11),
        estimated_base_hp_range=(80, 140),
        autonomous_safe=False,
        estimated_peak_round_damage=20,
        estimated_move_cost=10,
        requires_flight=False,
        loot=(),
        hazards=("target special: spec_test",),
        autonomy_rejections=("target has special procedure spec_test",),
        source_damage_modifier=0,
        estimated_min_peak_round_damage=1,
        equipped_weapons=(),
        specials=(),
        route_preflight_hard_hazard=False,
        route_hard_hazard_targets=(),
        route_attack_program_mobile_vnums=(),
        route_special_mobile_vnums=(),
        is_coin_stash=False,
        target_body_form_flags=(),
    )
    placement = SimpleNamespace(
        object_vnum=303,
        object_description="a test sword",
        category="wield",
        weapon_role="preferred",
        stance_rank=(10,),
        better_than_current=True,
        status="source-only",
        source_kind="mob-equipped",
        source_mobile_vnum=101,
        source_mobile="a test sentinel",
        room_vnum=202,
        room_name="Test Room",
        source_level_range=(8, 12),
        route=(),
        requires_flight=False,
        hazards=(),
        autonomy_rejections=(),
    )
    output = SimpleNamespace(
        action="knife toss",
        opening_action="backstab",
        minimum_damage=10,
        expected_damage=20,
        maximum_damage=30,
        conservative_damage=16,
        maximum_actions=4,
        opening_conservative_damage=12,
        source_reference="fight.c:test",
        opening_source_reference="fight.c:backstab",
    )
    captured_alignment: dict[str, object] = {}
    world_load_options: dict[str, object] = {}

    def fake_load_world_source(*_args, **kwargs):
        world_load_options.update(kwargs)
        return world

    monkeypatch.setattr(
        dd4tester.cli,
        "load_world_source",
        fake_load_world_source,
    )
    monkeypatch.setattr(
        dd4tester.cli,
        "_source_ranked_caster_output_for_state",
        lambda *args, **kwargs: output,
    )
    def fake_rank(_world, **kwargs):
        captured_alignment["value"] = kwargs["character_alignment"]
        captured_alignment["level_ceiling_offset"] = kwargs["level_ceiling_offset"]
        return [candidate]

    monkeypatch.setattr(dd4tester.cli, "rank_hunt_candidates", fake_rank)
    monkeypatch.setattr(
        dd4tester.cli,
        "rank_gear_sources",
        lambda *args, **kwargs: [placement],
    )
    monkeypatch.setattr(
        dd4tester.cli,
        "_source_revision",
        lambda _source: "source-current",
    )

    exit_code = main(
        [
            "show-combat-readiness",
            "--level",
            "10",
            "--class",
            "thief",
            "--source",
            str(source),
            "--database",
            str(database),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert exit_code == 0
    assert world_load_options == {
        "include_all_areas": False,
        "include_all_objects": True,
    }
    assert report["source_revision"] == "source-current"
    assert report["output"]["total_conservative_ceiling"] == 76
    assert report["target_summary"] == {
        "admission_fit": 0,
        "autonomous_safe": 0,
        "output_fit": 0,
        "protected_hp_probes": 0,
        "safe_and_output_fit": 0,
        "source_band": 1,
        "source_gate_fit": 0,
        "total": 1,
    }
    assert report["gear_upgrades"][0]["object_vnum"] == 303
    assert report["live_authorization"] is False
    assert report["character_alignment"] == 1000
    assert report["character_fame"] == -12
    assert report["fame_summary"]["ordinary_minimum_level_delta"] == 6
    assert report["fame_summary"]["ordinary_maximum_level_delta"] is None
    assert report["fame_summary"]["research_horizon_maximum_level_delta"] == 9
    assert report["fame_summary"]["ordinary_level_range"] == [16, 100]
    assert report["fame_summary"]["famous_level_range"] == [6, 100]
    assert report["fame_summary"]["ordinary_level_rule"] == (
        "victim level - character level > 5 (at least 6 levels higher)"
    )
    assert report["quest"]["fame_gate_allowed"] is False
    assert report["quest"]["request_allowed"] is False
    assert report["quest"]["request_blocker"] == (
        "DD4 rejects new quest requests while fame is below zero"
    )
    assert report["quest"]["questmaster"] == "Suturb"
    assert report["quest"]["level_gate_shortfall"] == 0
    assert any(
        constraint["key"] == "character_fame"
        for constraint in report["active_constraints"]
    )
    assert captured_alignment["value"] == 1000
    assert captured_alignment["level_ceiling_offset"] == 9


def test_readiness_candidate_reports_protected_hp_probe(monkeypatch) -> None:
    candidate = SimpleNamespace(
        target="a protected sentinel",
        mobile_vnum=101,
        room_vnum=202,
        room_name="Test Room",
        status="caution",
        score=123.0,
        estimated_level_range=(18, 22),
        estimated_base_hp_range=(225, 660),
        autonomous_safe=True,
        estimated_peak_round_damage=228,
        estimated_move_cost=10,
        requires_flight=True,
        loot=(),
        hazards=(),
        autonomy_rejections=(),
        source_damage_modifier=0,
    )
    monkeypatch.setattr(
        dd4tester.cli,
        "_source_ranked_protected_hp_fuzz_probe_allowed",
        lambda *_args, **_kwargs: True,
    )

    record = dd4tester.cli._readiness_candidate_record(
        candidate,
        level=24,
        output_ceiling=318,
        state={},
        source_world=object(),
    )

    assert record["protected_hp_probe"] is True


def test_readiness_candidate_separates_offensive_output_from_full_admission(
    monkeypatch,
) -> None:
    candidate = SimpleNamespace(
        target="Mr Smithy",
        mobile_vnum=2413,
        room_vnum=2406,
        room_name="Stables",
        status="caution",
        score=239.5,
        estimated_level_range=(23, 27),
        estimated_base_hp_range=(316, 945),
        autonomous_safe=True,
        estimated_peak_round_damage=276,
        estimated_move_cost=81,
        requires_flight=False,
        loot=(),
        hazards=(),
        autonomy_rejections=(),
        source_damage_modifier=0,
    )
    for helper in (
        "_source_ranked_protected_hp_fuzz_probe_allowed",
        "_source_ranked_protected_aggressive_hp_fuzz_probe_allowed",
        "_source_ranked_protected_level_ceiling_hp_probe_allowed",
    ):
        monkeypatch.setattr(dd4tester.cli, helper, lambda *_args, **_kwargs: False)
    monkeypatch.setattr(
        dd4tester.cli,
        "_source_ranked_hp_probe_admission_available",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        dd4tester.cli,
        "_source_ranked_candidate_requires_sanctuary_for_state",
        lambda *_args, **_kwargs: True,
    )
    monkeypatch.setattr(
        dd4tester.cli,
        "_state_has_sanctuary_reserve",
        lambda _state: False,
    )
    monkeypatch.setattr(
        dd4tester.cli,
        "_source_ranked_useful_fuzz_probability",
        lambda *_args, **_kwargs: 0.4,
    )
    monkeypatch.setattr(
        dd4tester.cli,
        "_source_ranked_candidate_excluded_by_below_band_evidence",
        lambda *_args, **_kwargs: True,
    )
    monkeypatch.setattr(
        dd4tester.cli,
        "_source_ranked_plain_aggressive_target_invisibility_allowed",
        lambda *_args, **_kwargs: True,
    )
    monkeypatch.setattr(
        dd4tester.cli,
        "_source_ranked_invisibility_route_candidate_allowed",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        dd4tester.cli,
        "_source_ranked_familiar_probe_allowed",
        lambda *_args, **_kwargs: False,
    )

    record = dd4tester.cli._readiness_candidate_record(
        candidate,
        level=25,
        output_ceiling=1092,
        state={"max_hp": 569},
        source_world=object(),
    )

    assert record["output_fit"] is True
    assert record["source_hp_admission"] is False
    assert record["requires_sanctuary"] is True
    assert record["sanctuary_available"] is False
    assert record["admission_fit"] is False
    assert record["source_gate_fit"] is False
    assert record["useful_xp_probability"] == 0.4
    assert "live consider evidence says this target is below the useful XP band" in record[
        "campaign_rejections"
    ]
    assert (
        "aggressive target requires a practiced invisibility route or familiar"
        in record["campaign_rejections"]
    )


def test_readiness_candidate_reports_exact_same_boot_protection_loss(
    monkeypatch,
) -> None:
    candidate = SimpleNamespace(
        area_file="new_ofcol.are",
        target="a sluggish Dragonhoard teller",
        mobile_vnum=635,
        room_vnum=800,
        room_name="Dragonhoard Bank, Ofcol Branch",
        route_origin_recall_index=0,
        level=20,
        status="caution",
        score=154.0,
        estimated_level_range=(18, 22),
        estimated_base_hp_range=(225, 660),
        autonomous_safe=True,
        estimated_peak_round_damage=228,
        estimated_move_cost=123,
        requires_flight=False,
        loot=(),
        hazards=(),
        autonomy_rejections=(),
        source_damage_modifier=0,
    )
    for helper in (
        "_source_ranked_protected_hp_fuzz_probe_allowed",
        "_source_ranked_protected_aggressive_hp_fuzz_probe_allowed",
        "_source_ranked_protected_level_ceiling_hp_probe_allowed",
    ):
        monkeypatch.setattr(
            dd4tester.cli,
            helper,
            lambda *_args, **_kwargs: False,
        )

    record = dd4tester.cli._readiness_candidate_record(
        candidate,
        level=21,
        output_ceiling=408,
        state={
            "world_boot_id": "boot-1",
            "campaign_protection_recovery_required": {
                "boot_id": "boot-1",
                "level": 21,
                "policy_id": "source-ranked-hunt-new-ofcol-635-800-21",
                "xp_delta": -334,
            },
        },
        source_world=None,
    )

    assert record["source_policy_id"] == "source-ranked-hunt-new-ofcol-635-800-21"
    assert (
        "this exact source reset already caused a 334 XP loss this reboot"
        in record["campaign_rejections"]
    )


def test_readiness_candidate_reports_exact_fame_branch_window(monkeypatch) -> None:
    monkeypatch.setattr(
        dd4tester.cli,
        "_source_ranked_protected_level_ceiling_hp_probe_allowed",
        lambda *_args, **_kwargs: False,
    )
    ordinary = SimpleNamespace(
        target="an ordinary fame target",
        mobile_vnum=101,
        room_vnum=201,
        room_name="Ordinary Room",
        status="caution",
        score=100.0,
        estimated_level_range=(15, 20),
        estimated_base_hp_range=(100, 300),
        level=18,
        autonomous_safe=True,
        estimated_peak_round_damage=20,
        estimated_move_cost=10,
        requires_flight=False,
        loot=(),
        hazards=(),
        autonomy_rejections=(),
        source_damage_modifier=0,
    )
    famous = SimpleNamespace(
        target="a famous target",
        mobile_vnum=102,
        room_vnum=202,
        room_name="Famous Room",
        status="caution",
        score=100.0,
        estimated_level_range=(5, 12),
        estimated_base_hp_range=(60, 180),
        level=10,
        autonomous_safe=True,
        estimated_peak_round_damage=20,
        estimated_move_cost=10,
        requires_flight=False,
        loot=(),
        hazards=(),
        autonomy_rejections=(),
        source_damage_modifier=0,
    )
    world = SimpleNamespace(
        mobiles={
            101: SimpleNamespace(awards_fame=False),
            102: SimpleNamespace(awards_fame=True),
        }
    )

    ordinary_record = dd4tester.cli._readiness_candidate_record(
        ordinary,
        level=10,
        output_ceiling=300,
        state={},
        source_world=world,
    )
    famous_record = dd4tester.cli._readiness_candidate_record(
        famous,
        level=10,
        output_ceiling=300,
        state={},
        source_world=world,
    )

    assert ordinary_record["fame_kind"] == "ordinary"
    assert ordinary_record["fame_window"] == [16, 20]
    assert famous_record["fame_kind"] == "famous"
    assert famous_record["fame_window"] == [6, 12]


def test_readiness_fame_window_stops_at_hero_level() -> None:
    ordinary = SimpleNamespace(estimated_level_range=(100, 110))
    famous = SimpleNamespace(estimated_level_range=(96, 110))

    assert dd4tester.campaign._source_ranked_fame_level_window(
        ordinary,
        character_level=100,
        awards_fame=False,
    ) is None
    assert dd4tester.campaign._source_ranked_fame_level_window(
        famous,
        character_level=100,
        awards_fame=True,
    ) == (96, 100)
    assert dd4tester.campaign._source_ranked_fame_level_window(
        SimpleNamespace(estimated_level_range=(106, 110)),
        character_level=100,
        awards_fame=False,
        maximum_level_delta=9,
    ) is None
    assert dd4tester.cli._readiness_level_range(106, 109) == []
    assert dd4tester.cli._readiness_level_range(96, 109) == [96, 100]


def test_readiness_fame_window_requires_six_levels_for_ordinary_victims() -> None:
    five_levels_high = SimpleNamespace(estimated_level_range=(15, 15))
    six_levels_high = SimpleNamespace(estimated_level_range=(16, 16))

    assert dd4tester.campaign._source_ranked_fame_level_window(
        five_levels_high,
        character_level=10,
        awards_fame=False,
    ) is None
    assert dd4tester.campaign._source_ranked_fame_level_window(
        six_levels_high,
        character_level=10,
        awards_fame=False,
    ) == (16, 16)


def test_inspection_state_merges_durable_pouch_ledger_from_checkpoint(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Kestrel to HERO",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=100,
        )
        run_id = storage.create_run(
            scenario_name="campaign",
            scenario_path=tmp_path / "campaign.yaml",
        )
        storage.record_state_snapshot(
            run_id,
            source_event_id=None,
            reason="prompt_seen",
            state={"name": "Kestrel", "level": 24, "max_hp": 334},
        )
        storage.finish_run(run_id, status="success")
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=None,
            run_id=run_id,
            phase="source-ranked-hunt",
            reason="segment_complete",
            state={
                "name": "Kestrel",
                "campaign_known_skills": ["backstab"],
                "combat_pouch_potions": {"purple": 1},
                "verified_combat_pouch_potions": {"purple": 1},
            },
        )

    state, _boot_id, _kill_counts = dd4tester.cli._load_inspection_state(
        database,
        "Kestrel",
    )

    assert state["campaign_known_skills"] == ["backstab"]
    assert state["combat_pouch_potions"] == {"purple": 1}
    assert state["verified_combat_pouch_potions"] == {"purple": 1}


def test_show_hunt_candidates_reuses_persisted_recall_origins(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    source = tmp_path / "area"
    source.mkdir()
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        run_id = storage.create_run(
            scenario_name="starter",
            scenario_path=Path("scenarios/starter.yaml"),
        )
        storage.record_state_snapshot(
            run_id,
            source_event_id=None,
            reason="prompt_seen",
            state={
                "name": "Ararisa",
                "level": 25,
                "recall_points": [{"index": 2, "name": "Draagdim"}],
                "current_recall": 2,
            },
        )
        storage.finish_run(run_id, status="success")

    captured_origins: list[dict[int, int] | None] = []

    def fake_rank(*args, **kwargs):
        captured_origins.append(kwargs["recall_origins"])
        return []

    monkeypatch.setattr(dd4tester.cli, "rank_hunt_candidates", fake_rank)

    exit_code = main(
        [
            "show-hunt-candidates",
            "--level",
            "25",
            "--source",
            str(source),
            "--database",
            str(database),
            "--all-areas",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured_origins == [{0: 3001, 2: 28003}]
    assert "Recall origins: 0 Default recall, 2 Draagdim" in captured.out


def test_show_hunt_candidates_uses_nested_gmcp_alignment(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    source = tmp_path / "area"
    source.mkdir()
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        run_id = storage.create_run(
            scenario_name="hunt",
            scenario_path=tmp_path / "hunt.yaml",
        )
        storage.record_state_snapshot(
            run_id,
            source_event_id=None,
            reason="prompt_seen",
            state={
                "name": "Ararisa",
                "level": 10,
                "progress": {"level": "10", "alignment": "1000"},
                "stats": {"fame": "-12"},
            },
        )
        storage.finish_run(run_id, status="success")

    captured_alignment: dict[str, object] = {}
    monkeypatch.setattr(
        dd4tester.cli,
        "load_world_source",
        lambda *_args, **_kwargs: WorldSource(),
    )

    def fake_rank(_world, **kwargs):
        captured_alignment["value"] = kwargs["character_alignment"]
        return []

    monkeypatch.setattr(dd4tester.cli, "rank_hunt_candidates", fake_rank)

    exit_code = main(
        [
            "show-hunt-candidates",
            "--level",
            "10",
            "--character",
            "Ararisa",
            "--source",
            str(source),
            "--database",
            str(database),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured_alignment["value"] == 1000
    assert "Player alignment: 1000" in captured.out
    assert "Player fame: -12" in captured.out


def test_show_gear_sources_renders_source_and_hazard_fields(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    source = tmp_path / "area"
    source.mkdir()
    placement = GearSourcePlacement(
        object_vnum=50,
        object_keywords="needle dagger",
        object_description="a needle dagger",
        category="wield",
        stance_rank=(12, 4),
        better_than_current=True,
        source_kind="mob-equipped",
        source_mobile_vnum=100,
        source_mobile="a quiet guard",
        room_vnum=200,
        room_name="the guard post",
        area_file="test.are",
        maximum_count=1,
        source_level_range=(5, 5),
        status="caution",
        route=("south",),
        hazards=("target equips a needle dagger",),
        weapon_role="preferred",
    )
    captured_options: dict[str, object] = {}

    monkeypatch.setattr(
        dd4tester.cli,
        "load_world_source",
        lambda *_args, **_kwargs: object(),
    )

    def fake_rank(_world, **kwargs):
        captured_options.update(kwargs)
        return [placement]

    monkeypatch.setattr(dd4tester.cli, "rank_gear_sources", fake_rank)

    exit_code = main(
        [
            "show-gear-sources",
            "--level",
            "5",
            "--class",
            "thief",
            "--stance",
            "combat",
            "--source",
            str(source),
            "--database",
            str(tmp_path / "missing.sqlite3"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured_options["character_level"] == 5
    assert captured_options["character_class"] == "thief"
    assert captured_options["stance"] == "combat"
    assert "Weapon preference: piercing" in captured.out
    assert "object_vnum\tkeywords\tobject\tcategory" in captured.out
    assert "50\tneedle dagger\ta needle dagger\twield\tyes\tcaution" in captured.out
    assert "mob-equipped" in captured.out
    assert "target equips a needle dagger" in captured.out
    assert "target equips a needle dagger\t-\tpreferred" in captured.out


def test_show_gear_sources_counts_inventory_without_duplicating_worn_gear(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    source = tmp_path / "area"
    source.mkdir()
    database = tmp_path / "runs.sqlite3"
    current = ObjectSource(
        40,
        "needle dagger",
        "a needle dagger",
        5,
        (0, 1, 1, 2),
        10,
        wear_flags=1 << 13,
    )
    with RunStorage(database) as storage:
        run_id = storage.create_run(
            scenario_name="gear",
            scenario_path=tmp_path / "gear.yaml",
        )
        storage.record_state_snapshot(
            run_id,
            source_event_id=None,
            reason="prompt_seen",
            state={
                "name": "Scout",
                "level": 5,
                "max_hp": 50,
                "equipment": '{"wield": {"name": "a needle dagger"}}',
                "campaign_worn_equipment": ["a needle dagger"],
                "inventory": '[{"quan": "2", "short_desc": "a needle dagger"}]',
            },
        )

    captured_options: dict[str, object] = {}
    monkeypatch.setattr(
        dd4tester.cli,
        "load_world_source",
        lambda *_args, **_kwargs: WorldSource(objects={current.vnum: current}),
    )

    def fake_rank(_world, **kwargs):
        captured_options.update(kwargs)
        return []

    monkeypatch.setattr(dd4tester.cli, "rank_gear_sources", fake_rank)

    exit_code = main(
        [
            "show-gear-sources",
            "--level",
            "5",
            "--class",
            "thief",
            "--character",
            "Scout",
            "--source",
            str(source),
            "--database",
            str(database),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured_options["character_max_hp"] == 50
    assert captured_options["current_items"] == [current, current, current]
    assert "Character max HP: 50" in captured.out


def test_hero_prepare_only_builds_source_validated_campaign(tmp_path, capsys) -> None:
    source = tmp_path / "const.c"
    source.write_text(
        """
        const struct class_type class_table[MAX_CLASS] = {
            {"Mag", "Mage", APPLY_INT, 1, 3018, 95, 18, 6, 6, 9, TRUE,
             "Necromancer", "Warlock", "Nec", "Wlk", {-1, 3, 1, 1, -1}}
        };
        const struct sub_class_type sub_class_table[MAX_SUB_CLASS] = {
            {"Non", "None", APPLY_STR, FALSE},
            {"Nec", "Necromancer", APPLY_WIS, TRUE},
            {"Wlk", "Warlock", APPLY_STR, TRUE}
        };
        const struct race_struct race_table[MAX_RACE] = {
            {"None", "None", 0, 0, 0, 0, 0, 0, 0, 0, "NULL", "NULL", 0},
            {"Human", "Human", 0, 1, 0, 0, 0, 0, 0, 0,
             "Identify", "Detect Evil", CHAR_SIZE_MEDIUM}
        };
        """,
        encoding="utf-8",
    )
    source.with_name("comm.c").write_text(
        """
        case CON_GET_NEW_SEX:
            switch (argument[0]) {
            case 'm': ch->sex = SEX_MALE; break;
            case 'f': ch->sex = SEX_FEMALE; break;
            case 'n': ch->sex = SEX_NEUTRAL; break;
            }
            break;
        case CON_DISPLAY_CLASS:
        """,
        encoding="utf-8",
    )

    exit_code = main(
        [
            "hero",
            "--name",
            "Valora",
            "--race",
            "human",
            "--sex",
            "female",
            "--class",
            "mage",
            "--source",
            str(source),
            "--workspace",
            str(tmp_path / "heroes"),
            "--transport",
            "mudlet",
            "--mudlet-directory",
            str(tmp_path / "shared-mudlet"),
            "--prepare-only",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Character: Valora (human mage)" in captured.out
    assert "Prepared: new" in captured.out
    assert (tmp_path / "heroes" / "valora" / "campaign.yaml").is_file()
    profile = (tmp_path / "heroes" / "valora" / "character.yaml").read_text(
        encoding="utf-8"
    )
    assert 'transport: "mudlet"' in profile


def test_hero_command_accepts_reset_gated_ready_campaign(tmp_path, capsys, monkeypatch) -> None:
    captured_request: dict[str, object] = {}

    async def fake_hero(request, **kwargs):
        captured_request["request"] = request
        captured_request["options"] = kwargs
        prepared = type(
            "Prepared",
            (),
            {
                "character": type(
                    "Character",
                    (), {"name": "Valora", "race": "human", "character_class": "mage"},
                )(),
                "manifest_path": tmp_path / "hero.json",
                "profile_path": tmp_path / "character.yaml",
                "campaign_path": tmp_path / "campaign.yaml",
                "resumed": True,
            },
        )()
        result = CampaignResult(
            4,
            "ready",
            9,
            "mud-school-2-6 arena circuit was empty at level 3. "
            "Campaign checkpointed while awaiting the Mud School area reset.",
            {"level": 3},
        )
        return prepared, result

    monkeypatch.setattr(dd4tester.cli, "run_hero_request", fake_hero)

    exit_code = main(
        [
            "hero",
            "--race",
            "human",
            "--sex",
            "female",
            "--class",
            "mage",
            "--username",
            "Valora",
            "--password",
            "command-line-secret",
            "--remember-password",
            "--target-level",
            "30",
            "--retry-stalled",
        ]
    )

    assert exit_code == 0
    request = captured_request["request"]
    assert isinstance(request, dd4tester.cli.HeroRequest)
    assert (request.race, request.sex, request.character_class) == (
        "human",
        "female",
        "mage",
    )
    assert request.name == "Valora"
    assert captured_request["options"]["reset_retries"] is None
    assert captured_request["options"]["max_segment_runtime"] == 300.0
    assert captured_request["options"]["target_level"] == 30
    assert captured_request["options"]["retry_stalled"] is True
    assert captured_request["options"]["password"] == "command-line-secret"
    assert captured_request["options"]["remember_password"] is True
    captured = capsys.readouterr()
    assert "awaiting the Mud School area reset" in captured.out
    assert "command-line-secret" not in captured.out


def test_hero_command_dispatches_autonomous_supervisor(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    captured_options: dict[str, object] = {}

    async def fake_hero(request, **kwargs):
        captured_options.update(kwargs)
        prepared = type(
            "Prepared",
            (),
            {
                "character": type(
                    "Character",
                    (),
                    {
                        "name": "Valora",
                        "race": "human",
                        "character_class": "mage",
                    },
                )(),
                "manifest_path": tmp_path / "hero.json",
                "profile_path": tmp_path / "character.yaml",
                "campaign_path": tmp_path / "campaign.yaml",
                "resumed": False,
            },
        )()
        return prepared, CampaignResult(
            4,
            "ready",
            9,
            "checkpointed for the next verified segment",
            {"level": 8},
        )

    monkeypatch.setattr(dd4tester.cli, "run_hero_until_target", fake_hero)

    exit_code = main(
        [
            "hero",
            "--name",
            "Valora",
            "--race",
            "human",
            "--sex",
            "female",
            "--class",
            "mage",
            "--autonomous",
            "--segments",
            "4",
            "--max-reset-waits",
            "2",
            "--password",
            "command-line-secret",
        ]
    )

    assert exit_code == 0
    assert captured_options["cycles"] == 4
    assert captured_options["max_reset_waits"] == 2
    assert "Valora (human mage)" in capsys.readouterr().out


def test_hero_command_turns_keyboard_interrupt_into_resumable_stop(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    def interrupted_run(coro):
        coro.close()
        raise KeyboardInterrupt

    monkeypatch.setattr(dd4tester.cli.asyncio, "run", interrupted_run)

    exit_code = main(
        [
            "hero",
            "--name",
            "Valora",
            "--race",
            "human",
            "--sex",
            "female",
            "--class",
            "mage",
            "--workspace",
            str(tmp_path / "heroes"),
            "--autonomous",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 130
    assert "durable checkpoint is preserved" in captured.err
    assert "Traceback" not in captured.err


def test_hero_command_infers_existing_identity_for_level_goal(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    workspace = tmp_path / "heroes"
    hero_directory = workspace / "valora"
    hero_directory.mkdir(parents=True)
    (hero_directory / "hero.json").write_text(
        json.dumps(
            {
                "request": {
                    "name": "Valora",
                    "race": "human",
                    "sex": "female",
                    "class": "mage",
                    "subclass": "warlock",
                    "personality": "patient and dryly funny",
                }
            }
        ),
        encoding="utf-8",
    )
    captured_request: dict[str, object] = {}

    async def fake_hero(request, **kwargs):
        captured_request["request"] = request
        captured_request["options"] = kwargs
        prepared = type(
            "Prepared",
            (),
            {
                "character": type(
                    "Character",
                    (),
                    {"name": "Valora", "race": "human", "character_class": "mage"},
                )(),
                "manifest_path": hero_directory / "hero.json",
                "profile_path": hero_directory / "character.yaml",
                "campaign_path": hero_directory / "campaign.yaml",
                "resumed": True,
            },
        )()
        return prepared, CampaignResult(8, "ready", 11, "checkpoint", {"level": 15})

    monkeypatch.setattr(dd4tester.cli, "run_hero_request", fake_hero)

    exit_code = main(
        [
            "hero",
            "--name",
            "Valora",
            "--password",
            "command-line-secret",
            "--target-level",
            "30",
            "--workspace",
            str(workspace),
        ]
    )

    assert exit_code == 0
    request = captured_request["request"]
    assert request.name == "Valora"
    assert (request.race, request.sex, request.character_class) == (
        "human",
        "female",
        "mage",
    )
    assert request.subclass == "warlock"
    assert request.personality == "patient and dryly funny"
    assert captured_request["options"]["target_level"] == 30
    assert captured_request["options"]["password"] == "command-line-secret"
    assert "command-line-secret" not in capsys.readouterr().out


def test_hero_command_rejects_conflicting_name_and_username(capsys) -> None:
    exit_code = main(
        [
            "hero",
            "--race",
            "human",
            "--class",
            "mage",
            "--name",
            "Valora",
            "--username",
            "Someoneelse",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "must identify the same DD4 character" in captured.err


def test_recover_runs_marks_orphaned_records(tmp_path, capsys) -> None:
    database, _transcript = _create_recorded_run(tmp_path)
    with RunStorage(database) as storage:
        storage.create_run(scenario_name="arena", scenario_path=tmp_path / "arena.yaml")
        campaign_id = storage.create_campaign(
            name="Ararisa to HERO",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=100,
        )
        storage.start_campaign_segment(
            campaign_id,
            phase="ambush-exterior-8-10",
            start_state={"name": "Ararisa", "level": 8},
        )

    exit_code = main(["recover-runs", "--database", str(database)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Marked 1 interrupted run(s) as failed." in captured.out
    assert (
        "Marked 1 interrupted campaign segment(s) across 1 campaign(s) as failed."
        in captured.out
    )
    with RunStorage(database) as storage:
        assert storage.get_campaign(campaign_id)["status"] == "failed"
        assert storage.list_campaign_segments(campaign_id)[0]["status"] == "failed"


def test_recover_runs_reopens_campaign_left_running_before_segment_creation(
    tmp_path,
    capsys,
) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Praelarran to HERO",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=100,
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=None,
            run_id=None,
            phase="source-ranked-hunt-test",
            reason="segment_complete",
            state={"name": "Praelarran", "level": 15, "xp": 1000},
        )
        storage.connection.execute(
            "UPDATE campaigns SET status = 'running' WHERE id = ?",
            (campaign_id,),
        )
        storage.connection.commit()

    exit_code = main(
        [
            "recover-runs",
            "--database",
            str(database),
            "--reason",
            "orphaned campaign worker",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Returned 1 orphaned campaign(s) without a running segment to ready." in captured.out
    with RunStorage(database) as storage:
        campaign = storage.get_campaign(campaign_id)
        checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)

    assert campaign is not None
    assert campaign["status"] == "ready"
    assert campaign["error"] == "orphaned campaign worker"
    assert checkpoint is not None
    assert checkpoint["phase"] == "source-ranked-hunt-test"


def test_recover_runs_leaves_campaign_with_active_lease_untouched(
    tmp_path,
    capsys,
) -> None:
    database = tmp_path / "runs.sqlite3"
    config_path = tmp_path / "campaign.yaml"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Praelarran to HERO",
            config_path=config_path,
            character_profile_path=tmp_path / "character.yaml",
            target_level=100,
        )
        storage.connection.execute(
            "UPDATE campaigns SET status = 'running' WHERE id = ?",
            (campaign_id,),
        )
        storage.connection.commit()

    lease = CampaignLease(campaign_lease_path(database, config_path))
    lease.acquire()
    try:
        exit_code = main(
            [
                "recover-runs",
                "--database",
                str(database),
                "--reason",
                "active worker still owns lease",
            ]
        )
    finally:
        lease.release()

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Returned 0 orphaned campaign(s) without a running segment to ready." in captured.out
    with RunStorage(database) as storage:
        campaign = storage.get_campaign(campaign_id)

    assert campaign is not None
    assert campaign["status"] == "running"
    assert campaign["error"] is None


def test_recover_runs_can_scope_one_campaign_without_global_recovery(
    tmp_path,
    capsys,
) -> None:
    database = tmp_path / "runs.sqlite3"
    config_path = tmp_path / "campaign.yaml"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Aeloria to HERO",
            config_path=config_path,
            character_profile_path=tmp_path / "character.yaml",
            target_level=100,
        )
        storage.start_campaign_segment(
            campaign_id,
            phase="source-ranked-hunt-test",
            start_state={"name": "Aeloria", "level": 18},
        )

    exit_code = main(
        [
            "recover-runs",
            "--database",
            str(database),
            "--campaign-id",
            str(campaign_id),
            "--character",
            "Aeloria",
            "--reason",
            "bounded worker stopped",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "indexed scoped queries" in captured.out
    assert "campaign 1" in captured.out.casefold()
    with RunStorage(database) as storage:
        assert storage.get_campaign(campaign_id)["status"] == "failed"
        assert storage.list_campaign_segments(campaign_id)[0]["status"] == "failed"


def test_arena_research_passes_kill_limit_to_runner(tmp_path, capsys, monkeypatch) -> None:
    captured_args: dict[str, object] = {}

    async def run_arena(profile, *, target_level, kill_limit):
        captured_args.update(
            profile=profile,
            target_level=target_level,
            kill_limit=kill_limit,
        )
        return RunResult(1, "success", tmp_path / "run.jsonl", tmp_path / "runs.sqlite3", {})

    monkeypatch.setattr(dd4tester.cli, "run_arena_research_profile", run_arena)

    exit_code = main(
        ["arena-research", str(tmp_path / "character.yaml"), "--target-level", "7", "--kill-limit", "2"]
    )

    assert exit_code == 0
    assert captured_args["target_level"] == 7
    assert captured_args["kill_limit"] == 2


def test_money_loop_passes_level_trip_limit_and_source(tmp_path, capsys, monkeypatch) -> None:
    captured_args: dict[str, object] = {}
    profile = tmp_path / "character.yaml"
    source = tmp_path / "area"
    run = RunResult(
        8,
        "success",
        tmp_path / "run.jsonl",
        tmp_path / "runs.sqlite3",
        {},
    )

    async def run_money(profile_path, *, character_level, trip_limit, source_directory):
        captured_args.update(
            profile=profile_path,
            character_level=character_level,
            trip_limit=trip_limit,
            source_directory=source_directory,
        )
        return MoneyLoopResult((run,), run, run, ("Uburz",))

    monkeypatch.setattr(dd4tester.cli, "run_money_loop_profile", run_money)

    exit_code = main(
        [
            "money-loop",
            str(profile),
            "--level",
            "6",
            "--trips",
            "2",
            "--source",
            str(source),
        ]
    )

    assert exit_code == 0
    assert captured_args == {
        "profile": profile,
        "character_level": 6,
        "trip_limit": 2,
        "source_directory": source,
    }
    assert "Money loop completed runs: 8, 8, 8" in capsys.readouterr().out


def test_show_sales_lists_recorded_proceeds(tmp_path, capsys) -> None:
    database, _transcript = _create_recorded_run(tmp_path)
    with RunStorage(database) as storage:
        storage.record_loot_sale(
            1,
            character_name="Ararisa",
            item_keyword="cap",
            item_description="an iron cap",
            shop_name="Leather Shop",
            shop_room_vnum="3035",
            offered_coins=11,
            sold_coins=11,
        )

    exit_code = main(
        ["show-sales", "--database", str(database), "--character", "Ararisa"]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "an iron cap" in captured.out
    assert "Total shown: 11 coins" in captured.out


def test_show_transcript_reads_run_id_from_database(tmp_path, capsys) -> None:
    database, transcript = _create_recorded_run(tmp_path)

    exit_code = main(["show-transcript", "1", "--database", str(database)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert str(transcript.resolve()) in captured.out
    assert "command" in captured.out
    assert '"command": "guest"' in captured.out


def test_show_transcript_reads_direct_path(tmp_path, capsys) -> None:
    _database, transcript = _create_recorded_run(tmp_path)

    exit_code = main(["show-transcript", str(transcript), "--raw"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out.splitlines()[0])["kind"] == "command"


def test_mudlet_bridge_command_generates_shared_files(tmp_path, capsys) -> None:
    directory = tmp_path / "mudlet-shared"

    exit_code = main(["mudlet-bridge", "--directory", str(directory)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert (directory / "dd4tester_bridge.lua").is_file()
    assert (directory / "commands.txt").is_file()
    assert (directory / "events.jsonl").is_file()
    assert "Mudlet script:" in captured.out


def test_show_state_prints_latest_snapshot_and_history(tmp_path, capsys) -> None:
    database, _transcript = _create_recorded_run(tmp_path)

    exit_code = main(["show-state", "1", "--database", str(database)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "state revision 1" in captured.out
    assert '"room_name": "The Entrance"' in captured.out

    exit_code = main(
        ["show-state", "1", "--database", str(database), "--history"]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "snapshot\ttimestamp\trevision\treason" in captured.out
    assert "room_entered" in captured.out


def test_starter_command_runs_character_profile(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "starter.yaml"
    profile.write_text("name: Rulemage", encoding="utf-8")
    transcript = tmp_path / "starter-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_run(path: Path) -> RunResult:
        assert path == profile
        return RunResult(7, "success", transcript, database, {"level": 2})

    monkeypatch.setattr(dd4tester.cli, "run_starter_profile", fake_run)

    exit_code = main(["starter", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 7 success" in captured.out
    assert f"Transcript: {transcript}" in captured.out


def test_campaign_command_prints_checkpointed_status(tmp_path, capsys, monkeypatch) -> None:
    config = tmp_path / "campaign.yaml"

    async def fake_campaign(path: Path, **_kwargs) -> CampaignResult:
        assert path == config
        assert _kwargs["force_new"] is True
        assert _kwargs["segments"] == 1
        assert _kwargs["reset_retries"] is None
        assert _kwargs["max_segment_runtime"] == 300.0
        return CampaignResult(4, "blocked", 9, "awaiting verified policy", {"level": 2})

    monkeypatch.setattr(dd4tester.cli, "run_campaign_file", fake_campaign)

    exit_code = main(["campaign", str(config), "--new"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Campaign 4 blocked" in captured.out
    assert "Checkpoint: 9" in captured.out
    assert "Level: 2" in captured.out


def test_campaign_progress_option_reports_to_stderr(tmp_path, capsys, monkeypatch) -> None:
    config = tmp_path / "campaign.yaml"

    async def fake_campaign(path: Path, **kwargs) -> CampaignResult:
        assert path == config
        kwargs["progress_callback"]("attempt started")
        return CampaignResult(4, "ready", 9, "checkpointed", {"level": 2, "xp": 100})

    monkeypatch.setattr(dd4tester.cli, "run_campaign_file", fake_campaign)

    assert main(["campaign", str(config), "--progress"]) == 0
    captured = capsys.readouterr()
    assert "Progress: attempt started" in captured.err


def test_campaign_command_uses_source_backed_default_reset_wait(
    tmp_path, monkeypatch
) -> None:
    config = tmp_path / "campaign.yaml"
    captured_options: dict[str, object] = {}

    async def fake_campaign(path: Path, **kwargs) -> CampaignResult:
        captured_options.update(kwargs)
        return CampaignResult(4, "ready", 9, "checkpointed", {"level": 2})

    monkeypatch.setattr(dd4tester.cli, "run_campaign_file", fake_campaign)

    assert main(["campaign", str(config)]) == 0
    assert captured_options["reset_wait"] == 180.0


def test_campaign_command_passes_per_segment_runtime_cap(tmp_path, capsys, monkeypatch) -> None:
    config = tmp_path / "campaign.yaml"
    captured_options: dict[str, object] = {}

    async def fake_campaign(path: Path, **kwargs) -> CampaignResult:
        assert path == config
        captured_options.update(kwargs)
        return CampaignResult(4, "ready", 9, "checkpointed", {"level": 2})

    monkeypatch.setattr(dd4tester.cli, "run_campaign_file", fake_campaign)

    exit_code = main(
        ["campaign", str(config), "--max-segment-runtime", "180"]
    )

    assert exit_code == 0
    assert captured_options["max_segment_runtime"] == 180
    assert "Campaign 4 ready" in capsys.readouterr().out


def test_campaign_command_returns_success_for_ready_checkpoint(tmp_path, capsys, monkeypatch) -> None:
    config = tmp_path / "campaign.yaml"

    async def fake_campaign(path: Path, **_kwargs) -> CampaignResult:
        return CampaignResult(
            4,
            "ready",
            9,
            "mud-school-6-10 segment completed at level 6. "
            "Campaign checkpointed for the next verified segment.",
            {"level": 6},
        )

    monkeypatch.setattr(dd4tester.cli, "run_campaign_file", fake_campaign)

    exit_code = main(["campaign", str(config)])

    assert exit_code == 0
    assert "Campaign 4 ready" in capsys.readouterr().out


def test_campaign_command_returns_success_when_an_empty_area_is_reset_gated(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    config = tmp_path / "campaign.yaml"

    async def fake_campaign(path: Path, **_kwargs) -> CampaignResult:
        return CampaignResult(
            4,
            "ready",
            9,
            "mud-school-2-6 arena circuit was empty at level 3. "
            "Campaign checkpointed while awaiting the Mud School area reset.",
            {"level": 3},
        )

    monkeypatch.setattr(dd4tester.cli, "run_campaign_file", fake_campaign)

    exit_code = main(["campaign", str(config)])

    assert exit_code == 0
    assert "awaiting the Mud School area reset" in capsys.readouterr().out


def test_arena_research_command_runs_with_requested_target(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "level-two.yaml"
    transcript = tmp_path / "arena-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_arena_research(
        path: Path,
        *,
        target_level: int,
        kill_limit: int | None,
    ) -> RunResult:
        assert path == profile
        assert target_level == 3
        assert kill_limit is None
        return RunResult(8, "success", transcript, database, {"level": 3})

    monkeypatch.setattr(dd4tester.cli, "run_arena_research_profile", fake_arena_research)

    exit_code = main(["arena-research", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 8 success" in captured.out
    assert f"Transcript: {transcript}" in captured.out


def test_resupply_command_runs_bounded_recovery(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "resupply-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_resupply(path: Path) -> RunResult:
        assert path == profile
        return RunResult(9, "success", transcript, database, {"level": 4})

    monkeypatch.setattr(dd4tester.cli, "run_resupply_profile", fake_resupply)

    exit_code = main(["resupply", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 9 success" in captured.out
    assert f"Transcript: {transcript}" in captured.out


def test_restock_command_runs_city_provisioning(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "restock-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_restock(path: Path) -> RunResult:
        assert path == profile
        return RunResult(10, "success", transcript, database, {"level": 4})

    monkeypatch.setattr(dd4tester.cli, "run_restock_profile", fake_restock)

    exit_code = main(["restock", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 10 success" in captured.out
    assert f"Transcript: {transcript}" in captured.out


def test_rearm_command_runs_verified_weapon_recovery(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "rearm-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_rearm(path: Path) -> RunResult:
        assert path == profile
        return RunResult(16, "success", transcript, database, {"level": 13})

    monkeypatch.setattr(dd4tester.cli, "run_rearm_profile", fake_rearm)

    exit_code = main(["rearm", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 16 success" in captured.out
    assert f"Transcript: {transcript}" in captured.out


def test_guildmaster_research_command_runs_bounded_route(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "guildmaster-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_guildmaster_research(path: Path) -> RunResult:
        assert path == profile
        return RunResult(11, "success", transcript, database, {"level": 6})

    monkeypatch.setattr(
        dd4tester.cli,
        "run_guildmaster_research_profile",
        fake_guildmaster_research,
    )

    exit_code = main(["guildmaster-research", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 11 success" in captured.out
    assert f"Transcript: {transcript}" in captured.out


def test_magic_shop_research_command_runs_bounded_route(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "magic-shop-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_magic_shop_research(path: Path, *, buy_fly: bool) -> RunResult:
        assert path == profile
        assert buy_fly is False
        return RunResult(13, "success", transcript, database, {"level": 6})

    monkeypatch.setattr(
        dd4tester.cli,
        "run_magic_shop_research_profile",
        fake_magic_shop_research,
    )

    exit_code = main(["magic-shop-research", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 13 success" in captured.out
    assert f"Transcript: {transcript}" in captured.out


def test_magic_shop_research_command_can_buy_and_use_fly_potion(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "magic-shop-2.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_magic_shop_research(path: Path, *, buy_fly: bool) -> RunResult:
        assert path == profile
        assert buy_fly is True
        return RunResult(14, "success", transcript, database, {"level": 6})

    monkeypatch.setattr(
        dd4tester.cli,
        "run_magic_shop_research_profile",
        fake_magic_shop_research,
    )

    exit_code = main(["magic-shop-research", str(profile), "--buy-fly"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 14 success" in captured.out


def test_return_home_command_runs_safe_recall(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "return-home-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_return_home(path: Path) -> RunResult:
        assert path == profile
        return RunResult(15, "success", transcript, database, {"level": 6})

    monkeypatch.setattr(
        dd4tester.cli,
        "run_return_home_profile",
        fake_return_home,
    )

    exit_code = main(["return-home", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 15 success" in captured.out


def test_fastwalk_research_command_runs_named_route(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "fastwalk-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_fastwalk_research(
        path: Path,
        route: str,
        *,
        explore_direction: str | None = None,
        explore_depth: int = 1,
        attack_target: str | None = None,
        consider_target: str | None = None,
        maximum_target_count: int = 1,
    ) -> RunResult:
        assert path == profile
        assert route == "moria"
        assert explore_direction is None
        assert explore_depth == 1
        assert attack_target is None
        assert consider_target is None
        assert maximum_target_count == 1
        return RunResult(15, "success", transcript, database, {"level": 6})

    monkeypatch.setattr(
        dd4tester.cli,
        "run_fastwalk_research_profile",
        fake_fastwalk_research,
    )

    exit_code = main(["fastwalk-research", str(profile), "moria"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 15 success" in captured.out


def test_fastwalk_research_command_can_inspect_one_exit(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "fastwalk-2.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_fastwalk_research(
        path: Path,
        route: str,
        *,
        explore_direction: str | None = None,
        explore_depth: int = 1,
        attack_target: str | None = None,
        consider_target: str | None = None,
        maximum_target_count: int = 1,
    ) -> RunResult:
        assert path == profile
        assert route == "moria"
        assert explore_direction == "north"
        assert explore_depth == 2
        assert attack_target is None
        assert consider_target is None
        assert maximum_target_count == 1
        return RunResult(16, "success", transcript, database, {"level": 6})

    monkeypatch.setattr(
        dd4tester.cli,
        "run_fastwalk_research_profile",
        fake_fastwalk_research,
    )

    exit_code = main(
        [
            "fastwalk-research",
            str(profile),
            "moria",
            "--exit",
            "north",
            "--depth",
            "2",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 16 success" in captured.out


def test_fastwalk_research_command_can_consider_without_attacking(
    tmp_path, capsys, monkeypatch
) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "fastwalk-consider.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_fastwalk_research(
        path: Path,
        route: str,
        *,
        explore_direction: str | None = None,
        explore_depth: int = 1,
        attack_target: str | None = None,
        consider_target: str | None = None,
        maximum_target_count: int = 1,
        allowed_bystanders: tuple[str, ...] = (),
    ) -> RunResult:
        assert path == profile
        assert route == "gnome mine"
        assert explore_direction is None
        assert explore_depth == 1
        assert attack_target is None
        assert consider_target == "hobgoblin miner"
        assert maximum_target_count == 1
        assert allowed_bystanders == ("mine foreman",)
        return RunResult(17, "success", transcript, database, {"level": 7})

    monkeypatch.setattr(
        dd4tester.cli,
        "run_fastwalk_research_profile",
        fake_fastwalk_research,
    )

    exit_code = main(
        [
            "fastwalk-research",
            str(profile),
            "gnome mine",
            "--consider",
            "hobgoblin miner",
            "--allow-bystander",
            "mine foreman",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 17 success" in captured.out


def test_midennir_research_command_collects_large_sack(
    tmp_path, capsys, monkeypatch
) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "midennir-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_midennir_research(path: Path) -> RunResult:
        assert path == profile
        return RunResult(17, "success", transcript, database, {"level": 7})

    monkeypatch.setattr(
        dd4tester.cli,
        "run_midennir_research_profile",
        fake_midennir_research,
    )

    exit_code = main(["midennir-research", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 17 success" in captured.out


def test_ambush_research_command_runs_exterior_circuit(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "ambush-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_ambush_research(
        path: Path,
        *,
        guard_probe: bool,
        vile_probe: bool,
        raider_probe: bool,
        horseman_probe: bool,
        vile_hunt: bool,
    ) -> RunResult:
        assert path == profile
        assert guard_probe is True
        assert vile_probe is False
        assert raider_probe is False
        assert horseman_probe is False
        assert vile_hunt is False
        return RunResult(18, "success", transcript, database, {"level": 9})

    monkeypatch.setattr(
        dd4tester.cli,
        "run_ambush_research_profile",
        fake_ambush_research,
    )

    exit_code = main(["ambush-research", str(profile), "--guard-probe"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 18 success" in captured.out
    assert f"Transcript: {transcript}" in captured.out


def test_ambush_research_command_selects_vile_goblin_probe(
    tmp_path,
    monkeypatch,
) -> None:
    profile = tmp_path / "character.yaml"

    async def fake_ambush_research(
        path: Path,
        *,
        guard_probe: bool,
        vile_probe: bool,
        raider_probe: bool,
        horseman_probe: bool,
        vile_hunt: bool,
    ) -> RunResult:
        assert path == profile
        assert guard_probe is False
        assert vile_probe is True
        assert raider_probe is False
        assert horseman_probe is False
        assert vile_hunt is False
        return RunResult(
            19,
            "success",
            tmp_path / "ambush-2.jsonl",
            tmp_path / "runs.sqlite3",
            {"level": 8},
        )

    monkeypatch.setattr(
        dd4tester.cli,
        "run_ambush_research_profile",
        fake_ambush_research,
    )

    assert main(["ambush-research", str(profile), "--vile-probe"]) == 0


def test_ambush_research_command_selects_raider_probe(
    tmp_path,
    monkeypatch,
) -> None:
    profile = tmp_path / "character.yaml"

    async def fake_ambush_research(
        path: Path,
        *,
        guard_probe: bool,
        vile_probe: bool,
        raider_probe: bool,
        horseman_probe: bool,
        vile_hunt: bool,
    ) -> RunResult:
        assert path == profile
        assert guard_probe is False
        assert vile_probe is False
        assert raider_probe is True
        assert horseman_probe is False
        assert vile_hunt is False
        return RunResult(
            20,
            "success",
            tmp_path / "ambush-raider.jsonl",
            tmp_path / "runs.sqlite3",
            {"level": 10},
        )

    monkeypatch.setattr(
        dd4tester.cli,
        "run_ambush_research_profile",
        fake_ambush_research,
    )

    assert main(["ambush-research", str(profile), "--raider-probe"]) == 0


def test_ambush_research_command_selects_bounded_raider_hunt(
    tmp_path,
    monkeypatch,
) -> None:
    profile = tmp_path / "character.yaml"

    async def fake_ambush_research(path: Path, **options: bool) -> RunResult:
        assert path == profile
        assert options == {
            "guard_probe": False,
            "vile_probe": False,
            "raider_probe": False,
            "raider_hunt": True,
            "horseman_probe": False,
            "vile_hunt": False,
        }
        return RunResult(
            21,
            "success",
            tmp_path / "ambush-raider-hunt.jsonl",
            tmp_path / "runs.sqlite3",
            {"level": 10},
        )

    monkeypatch.setattr(
        dd4tester.cli,
        "run_ambush_research_profile",
        fake_ambush_research,
    )

    assert main(["ambush-research", str(profile), "--raider-hunt"]) == 0


def test_ambush_research_command_selects_horseman_probe(
    tmp_path,
    monkeypatch,
) -> None:
    profile = tmp_path / "character.yaml"

    async def fake_ambush_research(
        path: Path,
        *,
        guard_probe: bool,
        vile_probe: bool,
        raider_probe: bool,
        horseman_probe: bool,
        vile_hunt: bool,
    ) -> RunResult:
        assert path == profile
        assert guard_probe is False
        assert vile_probe is False
        assert raider_probe is False
        assert horseman_probe is True
        assert vile_hunt is False
        return RunResult(
            20,
            "success",
            tmp_path / "ambush-horseman.jsonl",
            tmp_path / "runs.sqlite3",
            {"level": 9},
        )

    monkeypatch.setattr(
        dd4tester.cli,
        "run_ambush_research_profile",
        fake_ambush_research,
    )

    assert main(["ambush-research", str(profile), "--horseman-probe"]) == 0


def test_ambush_research_command_selects_bounded_vile_hunt(
    tmp_path,
    monkeypatch,
) -> None:
    profile = tmp_path / "character.yaml"

    async def fake_ambush_research(
        path: Path,
        *,
        guard_probe: bool,
        vile_probe: bool,
        raider_probe: bool,
        horseman_probe: bool,
        vile_hunt: bool,
    ) -> RunResult:
        assert path == profile
        assert guard_probe is False
        assert vile_probe is False
        assert raider_probe is False
        assert horseman_probe is False
        assert vile_hunt is True
        return RunResult(
            21,
            "success",
            tmp_path / "ambush-vile-hunt.jsonl",
            tmp_path / "runs.sqlite3",
            {"level": 9},
        )

    monkeypatch.setattr(
        dd4tester.cli,
        "run_ambush_research_profile",
        fake_ambush_research,
    )

    assert main(["ambush-research", str(profile), "--vile-hunt"]) == 0


def test_moria_research_command_runs_bounded_route(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "moria-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_moria_research(
        path: Path,
        *,
        depth: int,
        sanctuary_probe: bool,
        sanctuary_hunt: bool,
        sanctuary_deep_hunt: bool,
    ) -> RunResult:
        assert path == profile
        assert depth == 0
        assert sanctuary_probe is False
        assert sanctuary_hunt is False
        assert sanctuary_deep_hunt is False
        return RunResult(12, "success", transcript, database, {"level": 6})

    monkeypatch.setattr(
        dd4tester.cli,
        "run_moria_research_profile",
        fake_moria_research,
    )

    exit_code = main(["moria-research", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 12 success" in captured.out
    assert f"Transcript: {transcript}" in captured.out


def test_moria_research_command_selects_sanctuary_probe(
    tmp_path,
    monkeypatch,
) -> None:
    profile = tmp_path / "character.yaml"

    async def fake_moria_research(
        path: Path,
        *,
        depth: int,
        sanctuary_probe: bool,
        sanctuary_hunt: bool,
        sanctuary_deep_hunt: bool,
    ) -> RunResult:
        assert path == profile
        assert depth == 0
        assert sanctuary_probe is True
        assert sanctuary_hunt is False
        assert sanctuary_deep_hunt is False
        return RunResult(
            22,
            "success",
            tmp_path / "moria-sanctuary.jsonl",
            tmp_path / "runs.sqlite3",
            {"level": 9},
        )

    monkeypatch.setattr(
        dd4tester.cli,
        "run_moria_research_profile",
        fake_moria_research,
    )

    assert (
        main(["moria-research", str(profile), "--sanctuary-probe"])
        == 0
    )


def test_moria_research_command_selects_sanctuary_hunt(
    tmp_path,
    monkeypatch,
) -> None:
    profile = tmp_path / "character.yaml"

    async def fake_moria_research(
        path: Path,
        *,
        depth: int,
        sanctuary_probe: bool,
        sanctuary_hunt: bool,
        sanctuary_deep_hunt: bool,
    ) -> RunResult:
        assert path == profile
        assert depth == 0
        assert sanctuary_probe is False
        assert sanctuary_hunt is True
        assert sanctuary_deep_hunt is False
        return RunResult(
            23,
            "success",
            tmp_path / "moria-sanctuary-hunt.jsonl",
            tmp_path / "runs.sqlite3",
            {"level": 9},
        )

    monkeypatch.setattr(
        dd4tester.cli,
        "run_moria_research_profile",
        fake_moria_research,
    )

    assert main(["moria-research", str(profile), "--sanctuary-hunt"]) == 0


def test_moria_research_command_selects_deep_sanctuary_hunt(
    tmp_path,
    monkeypatch,
) -> None:
    profile = tmp_path / "character.yaml"

    async def fake_moria_research(
        path: Path,
        *,
        depth: int,
        sanctuary_probe: bool,
        sanctuary_hunt: bool,
        sanctuary_deep_hunt: bool,
    ) -> RunResult:
        assert path == profile
        assert depth == 0
        assert sanctuary_probe is False
        assert sanctuary_hunt is False
        assert sanctuary_deep_hunt is True
        return RunResult(
            24,
            "success",
            tmp_path / "moria-sanctuary-deep-hunt.jsonl",
            tmp_path / "runs.sqlite3",
            {"level": 25},
        )

    monkeypatch.setattr(
        dd4tester.cli,
        "run_moria_research_profile",
        fake_moria_research,
    )

    assert (
        main(["moria-research", str(profile), "--sanctuary-deep-hunt"])
        == 0
    )


def test_show_fastwalks_filters_official_routes_by_level(capsys) -> None:
    exit_code = main(["show-fastwalks", "--level", "6"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "name\tlevels\tnotation\tcommands" in captured.out
    assert "ambush\t6-16\t6s" in captured.out
    assert "moria\t5-15\t2s6e8n" in captured.out


def test_show_hunt_candidates_reports_source_risk_and_spawn_limits(
    tmp_path,
    capsys,
) -> None:
    source = tmp_path / "area"
    source.mkdir()
    fixture = Path(__file__).parent / "fixtures" / "hunt_area.are"
    (source / "foundry.are").write_text(
        fixture.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "show-hunt-candidates",
            "--level",
            "10",
            "--source",
            str(source),
            "--database",
            str(tmp_path / "missing.sqlite3"),
            "--include-xp-only",
            "--all-areas",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Current reboot: unknown" in captured.out
    assert "Character max HP: unknown" in captured.out
    assert "fuzzed_levels\tbase_hp\tpeak_round\troom" in captured.out
    assert "mobility\tsearch_rooms\trank\tsource_level" in captured.out
    assert "move_cost\tflight_cost\trequires_flight" in captured.out
    assert "room_spawns\tspawn_limit\tboot_kills" in captured.out
    assert "autonomy_rejections" in captured.out
    assert "template\txp_modifier\tdamage_modifier\tundead" in captured.out
    assert "caution\t" in captured.out
    assert "the dangerous guard" in captured.out
    assert "reachable wanderer: a cellar rat L3" in captured.out
    assert "a cellar rat\t3\t1-5" not in captured.out


def test_show_resource_sources_reports_exact_object_and_hazards(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    placement = ResourcePlacement(
        effect="sanctuary",
        object_vnum=4050,
        object_keywords="potion purple",
        object_description="a purple potion",
        item_type=10,
        source_kind="mob-carried",
        source_mobile_vnum=4055,
        source_mobile="the large hobgoblin",
        room_vnum=4064,
        room_name="The tunnel",
        area_file="moria.are",
        maximum_count=2,
        source_level_range=(8, 12),
        status="reject",
        route=("south", "east"),
        hazards=("target reset permits up to 2 matching mobiles in the room",),
        autonomy_rejections=("target reset capacity exceeds one",),
    )
    monkeypatch.setattr(
        dd4tester.cli,
        "load_world_source",
        lambda _source, *, include_all_areas: object(),
    )
    monkeypatch.setattr(
        dd4tester.cli,
        "rank_resource_sources",
        lambda _world, **_kwargs: [placement],
    )

    exit_code = main(
        [
            "show-resource-sources",
            "--level",
            "18",
            "--effect",
            "sanctuary",
            "--source",
            str(tmp_path / "area"),
            "--database",
            str(tmp_path / "missing.sqlite3"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "effect\tstatus\tobject_vnum\tobject" in captured.out
    assert "container_objects\tcontainer_keys\tcontainer_key_sources" in captured.out
    assert "sanctuary\treject\t4050\ta purple potion\tpotion" in captured.out
    assert "4055 the large hobgoblin" in captured.out
    assert "4064 The tunnel" in captured.out
    assert "target reset capacity exceeds one" in captured.out


def test_show_hunt_candidates_ignores_hp_from_a_different_level(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    source = tmp_path / "area"
    source.mkdir()
    fixture = Path(__file__).parent / "fixtures" / "hunt_area.are"
    (source / "foundry.are").write_text(
        fixture.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    database = tmp_path / "runs.sqlite3"
    storage = RunStorage(database)
    run_id = storage.create_run(
        scenario_name="starter",
        scenario_path=Path("scenarios/starter.yaml"),
    )
    storage.record_state_snapshot(
        run_id,
        source_event_id=None,
        reason="prompt_seen",
        state={"name": "Ararisa", "level": 6, "max_hp": 136},
    )
    storage.finish_run(run_id, status="success")
    storage.close()
    captured_max_hp: list[int | None] = []
    original_rank = dd4tester.cli.rank_hunt_candidates

    def capture_rank(*args, **kwargs):
        captured_max_hp.append(kwargs["character_max_hp"])
        return original_rank(*args, **kwargs)

    monkeypatch.setattr(dd4tester.cli, "rank_hunt_candidates", capture_rank)

    exit_code = main(
        [
            "show-hunt-candidates",
            "--level",
            "20",
            "--source",
            str(source),
            "--database",
            str(database),
            "--include-xp-only",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured_max_hp == [None]
    assert "Character max HP: unknown" in captured.out


def test_show_hunt_candidates_uses_durable_campaign_capabilities(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    source = tmp_path / "area"
    source.mkdir()
    fixture = Path(__file__).parent / "fixtures" / "hunt_area.are"
    (source / "foundry.are").write_text(
        fixture.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Aeloria to HERO",
            config_path=Path("runs/heroes/aeloria/campaign.yaml"),
            character_profile_path=Path("runs/heroes/aeloria/character.yaml"),
            target_level=100,
        )
        run_id = storage.create_run(
            scenario_name="starter",
            scenario_path=Path("scenarios/starter.yaml"),
        )
        storage.record_state_snapshot(
            run_id,
            source_event_id=None,
            reason="prompt_seen",
            state={
                "name": "Aeloria",
                "level": 18,
                "max_hp": 218,
                "character_class": "Mage",
            },
        )
        storage.finish_run(run_id, status="success")
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=None,
            run_id=run_id,
            phase="source-ranked-hunt-test",
            reason="segment_complete",
            state={
                "name": "Aeloria",
                "campaign_known_skills": ["burning hands"],
                "campaign_known_skill_levels": {"burning hands": 31},
            },
        )

    captured_kwargs: dict[str, object] = {}

    def capture_rank(*args, **kwargs):
        captured_kwargs.update(kwargs)
        return []

    monkeypatch.setattr(dd4tester.cli, "rank_hunt_candidates", capture_rank)

    exit_code = main(
        [
            "show-hunt-candidates",
            "--level",
            "18",
            "--character",
            "Aeloria",
            "--source",
            str(source),
            "--database",
            str(database),
            "--include-xp-only",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured_kwargs["known_skills"] == ("burning hands",)
    assert captured_kwargs["known_skill_levels"] == {"burning hands": 31}
    assert "Character class: Mage" in captured.out


def test_configure_login_command_uses_named_credential(capsys, monkeypatch) -> None:
    configured: list[str] = []
    monkeypatch.setattr(
        dd4tester.cli,
        "configure_login",
        lambda name: configured.append(name),
    )

    exit_code = main(["configure-login", "--credential-name", "research-login"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert configured == ["research-login"]
    assert "Stored login credential: research-login" in captured.out


def test_configure_character_password_uses_profile_credential(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "character.yaml"
    configured: list[str] = []

    monkeypatch.setattr(
        dd4tester.cli,
        "load_character_spec",
        lambda _path: type("Spec", (), {"credential_name": "character:rulemira"})(),
    )
    monkeypatch.setattr(
        dd4tester.cli,
        "configure_character_password",
        lambda name: configured.append(name),
    )

    exit_code = main(["configure-character-password", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert configured == ["character:rulemira"]
    assert "Stored character password credential: character:rulemira" in captured.out


def test_matrix_cli_reports_each_character_without_hiding_incomplete_work(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    captured_kwargs: dict[str, object] = {}

    async def fake_run_matrix_file(*_args, **_kwargs):
        captured_kwargs.update(_kwargs)
        return MatrixResult(
            "Mage Thief Warrior",
            10,
            "incomplete",
            (
                MatrixEntryResult("mage", "Aeloria", "mage", 1, "success", 10, None),
                MatrixEntryResult(
                    "thief",
                    "Kestrel",
                    "thief",
                    2,
                    "blocked",
                    8,
                    "awaiting policy evidence",
                ),
                MatrixEntryResult("warrior", "Dorrik", "warrior", 3, "success", 10, None),
            ),
        )

    monkeypatch.setattr(dd4tester.cli, "run_matrix_file", fake_run_matrix_file)

    exit_code = main(
        [
            "matrix",
            str(tmp_path / "matrix.yaml"),
            "--rounds",
            "2",
            "--segments-per-character",
            "3",
            "--max-segment-runtime",
            "180",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Matrix: Mage Thief Warrior" in captured.out
    assert "mage\tAeloria\tmage\t10\tsuccess\t1\t-" in captured.out
    assert "thief\tKestrel\tthief\t8\tblocked\t2\tawaiting policy evidence" in captured.out
    assert "warrior\tDorrik\twarrior\t10\tsuccess\t3\t-" in captured.out
    assert captured_kwargs["max_segment_runtime"] == 180


def test_configure_matrix_passwords_reports_status_without_secrets(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        dd4tester.cli,
        "provision_matrix_passwords",
        lambda _path: (
            MatrixCredentialResult("mage", "character:aeloria", "existing"),
            MatrixCredentialResult("thief", "character:kestrel", "generated"),
        ),
    )

    exit_code = main(
        ["configure-matrix-passwords", str(tmp_path / "matrix.yaml")]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "mage: existing credential character:aeloria" in captured.out
    assert "thief: generated credential character:kestrel" in captured.out
    assert "password" not in captured.out.casefold()


def test_show_campaign_prints_checkpoint_and_segments(tmp_path, capsys) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Rulemage to HERO",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=100,
        )
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="starter",
            start_state={"level": 1},
        )
        storage.finish_campaign_segment(
            segment_id,
            status="success",
            run_id=7,
            end_state={"level": 2},
            command_count=42,
            duration_seconds=12.5,
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=segment_id,
            run_id=7,
            phase="starter",
            reason="segment_complete",
            state={"level": 2},
        )
        storage.finish_campaign(
            campaign_id,
            status="blocked",
            error="awaiting verified policy",
        )

    exit_code = main(["show-campaign", str(campaign_id), "--database", str(database)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Campaign 1: Rulemage to HERO" in captured.out
    assert "Checkpoint 1: starter (segment_complete), level 2" in captured.out
    assert "1\tstarter\tsuccess\t7\t42\t12.5s\t-" in captured.out
    assert "recent segments (up to 20; newest segment last)" in captured.out


def test_show_campaign_prints_frontier_diagnosis(tmp_path, capsys) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Dorrik to HERO",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=100,
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=None,
            run_id=None,
            phase="source-ranked-hunt-unavailable-25",
            reason="awaiting_area_reset",
            state={
                "level": 25,
                "campaign_source_ranked_frontier_diagnosis": {
                    "boot_id": "boot-1",
                    "reason": "no executable source-ranked frontier",
                    "candidate_count": 12,
                    "current_band_count": 3,
                    "autonomous_safe_count": 2,
                    "sanctuary_required_count": 1,
                    "no_sanctuary_count": 1,
                    "same_boot_below_band_count": 1,
                    "no_sanctuary_candidates": [{
                        "policy_id": "source-ranked-hunt-example-25",
                        "selection_pool": "recent-mobile-kill",
                        "target": "a plain target",
                        "mobile_vnum": 103,
                        "area_file": "example.are",
                        "room_vnum": 203,
                        "room_name": "The Test Room",
                        "level_range": [24, 26],
                    }],
                    "top_blockers": [
                        {"reason": "sanctuary reserve required", "count": 1}
                    ],
                },
                "world_boot_id": "boot-1",
                "campaign_below_band_policy_exclusions": {
                    "source-ranked-hunt-example-25": {
                        "boot_id": "boot-1",
                        "level": 25,
                        "targets": ["a plain target"],
                    }
                },
                "campaign_source_ranked_timeout_policies": [{
                    "boot_id": "boot-1",
                    "level": 25,
                    "policy_id": "source-ranked-hunt-example-25",
                    "revalidation_attempted": True,
                    "revalidation_attempts": 1,
                }],
                "campaign_research_results": {
                    "source-ranked-hunt-example-25": {
                        "boot_id": "boot-1",
                        "route_hazard": (
                            "segment runtime boundary requested a safe healer return"
                        ),
                    }
                },
            },
        )

    exit_code = main(["show-campaign", str(campaign_id), "--database", str(database)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Frontier diagnosis: no executable source-ranked frontier" in captured.out
    assert "candidates=12 current-band=3 autonomous-safe=2" in captured.out
    assert "Frontier blockers: sanctuary reserve required: 1" in captured.out
    assert "No-sanctuary frontier options (diagnostic only):" in captured.out
    assert "a plain target [103] at The Test Room" in captured.out
    assert "pool=recent-mobile-kill" in captured.out
    assert (
        "same-boot history: last result=segment runtime boundary requested a safe healer return; "
        "blocked=live below-band evidence for this reset; "
        "timeout revalidation already used"
    ) in captured.out


def test_show_campaign_rejects_nonpositive_limit(tmp_path, capsys) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Rulemage to HERO",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=100,
        )

    exit_code = main(
        [
            "show-campaign",
            str(campaign_id),
            "--database",
            str(database),
            "--limit",
            "0",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "--limit must be at least 1" in captured.err


def test_show_policies_displays_evidence_and_practice_candidate(capsys) -> None:
    exit_code = main(["show-policies", "--level", "2", "--class", "mage"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Policy: mud-school-2-6" in captured.out
    assert "Status: verified" in captured.out
    assert "Practice candidate: magic missile" in captured.out
    assert "Live run 56" in captured.out


def test_show_policy_coverage_makes_unavailable_hero_bands_explicit(capsys) -> None:
    exit_code = main(
        [
            "show-policy-coverage",
            "--class",
            "thief",
            "--from-level",
            "12",
            "--to-level",
            "16",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "levels\tpolicy\tstatus\texecution" in captured.out
    assert "12\tfleshmonger-thief-rotation-research-12-13\tresearch" in captured.out
    assert (
        "16\tmirror-realm-watchman-probe-16-20\tresearch\t"
        "mirror-realm-watchman-research"
    ) in captured.out


def test_matrix_coverage_reports_legal_pair_gap(capsys) -> None:
    exit_code = main(["matrix-coverage", "matrices/level-10.yaml"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Legal race/class pairs: 225" in captured.out
    assert "Declared pairs: 3" in captured.out
    assert "Undeclared pairs: 222" in captured.out
    assert "Live-validated pairs at level 10:" in captured.out
    assert "Live-pending declared pairs:" in captured.out
    assert "entry\tlevel\tstatus\tcampaign" in captured.out


def test_show_prereqs_displays_bundled_skill_requirements(capsys) -> None:
    exit_code = main(["show-prereqs", "--class", "mage", "--skill", "fireball"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Skill: fireball" in captured.out
    assert "group evocation: 75%" in captured.out


def test_skill_analysis_displays_ranked_source_backed_class_value(capsys) -> None:
    exit_code = main(["skill-analysis", "--class", "psionic"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Class: psionic" in captured.out
    assert "Strategy:" in captured.out
    assert "Practice policy:" in captured.out
    assert "Highest leveling value:" in captured.out
    assert "Automation gaps:" in captured.out
    assert "Ordered leveling priorities:" in captured.out
    assert "telepathy disciplines" in captured.out
    assert "damage-gateway, automated" in captured.out
    assert "mind thrust 10%" in captured.out
    assert "psychic crush" in captured.out


def test_skill_analysis_supports_subclass_alias_and_priorities(capsys) -> None:
    exit_code = main(["skill-analysis", "--class", "bounty hunter"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Class: bounty hunter" in captured.out
    assert "assassinate" in captured.out
    assert "group stealth 85%" in captured.out


def _create_recorded_run(tmp_path) -> tuple[Path, Path]:
    database = tmp_path / "runs.sqlite3"
    storage = RunStorage(database)
    run_id = storage.create_run(scenario_name="login", scenario_path=Path("scenarios/login.yaml"))
    recorder = TranscriptRecorder.create(tmp_path / "transcripts", scenario_name="login", run_id=run_id)
    storage.set_transcript_path(run_id, recorder.path)
    event = recorder.record("command", {"command": "guest"})
    source_event_id = storage.record_event(
        run_id,
        kind=event.kind,
        payload=event.payload,
        timestamp=event.timestamp,
    )
    storage.record_state_snapshot(
        run_id,
        source_event_id=source_event_id,
        reason="room_entered",
        state={
            "schema_version": 1,
            "revision": 1,
            "level": 2,
            "hp": 60,
            "max_hp": 60,
            "room_name": "The Entrance",
        },
        timestamp=event.timestamp,
    )
    storage.finish_run(run_id, status="success")
    transcript_path = recorder.path
    recorder.close()
    storage.close()
    return database, transcript_path
