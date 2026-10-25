import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from dd4tester.campaign import (
    _BUY_FLIGHT_POLICY,
    _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY,
    _CAERLIN_STAFF_RESERVE_REACQUISITION_KEY,
    _FLIGHT_FUNDING_REQUIRED_KEY,
    _MORIA_SANCTUARY_SECOND_FIXED_RESET_ATTEMPT_KEY,
    _MORIA_SANCTUARY_SECOND_FIXED_RESET_POLICY_ID,
    _MORIA_SANCTUARY_SECOND_FIXED_RESET_REACQUISITION_KEY,
    _SOURCE_REVISION_KEY,
    _SOURCE_RANKED_HUNT_POLICY,
    _SOURCE_RANKED_SANCTUARY_ALTERNATE_POLICY,
    _SOURCE_RANKED_OLYMPUS_SANCTUARY_POLICY,
    _SOURCE_RANKED_OLYMPUS_ADEPT_SANCTUARY_POLICY,
    _SOURCE_RANKED_OLYMPUS_HEPHAESTUS_SANCTUARY_POLICY,
    _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY,
    _SOURCE_CONSUMABLE_SANCTUARY_POLICY_IDS,
    CampaignRunner,
    load_campaign_spec,
    _campaign_has_caerlin_staff,
    _campaign_segment_end_state,
    _repair_caerlin_staff_attempt_metadata,
    _repair_source_resource_dispatch_contract,
    _repair_stale_caerlin_staff_reserve,
    _state_has_sanctuary_reserve,
    _caerlin_staff_handoff_repair_allowed,
    _caerlin_staff_locator_revalidation_allowed,
    _caerlin_staff_locator_retry_allowed,
    _caerlin_staff_reserve_reacquisition_allowed,
    _caerlin_staff_source_revision_retry_allowed,
    _caerlin_staff_retry_open,
    _moria_sanctuary_second_fixed_reset_reacquisition_allowed,
    _select_source_ranked_alternate_sanctuary_candidate,
    _select_source_ranked_moria_4071_reacquisition_candidate,
    _select_source_ranked_olympus_sanctuary_candidate,
    _select_source_ranked_olympus_adept_sanctuary_candidate,
    _select_source_ranked_olympus_hephaestus_sanctuary_candidate,
    _select_source_ranked_sanctuary_maintenance_candidate,
    _select_source_consumable_candidate,
    _sanctuary_policy_retry_terminal,
    _source_consumable_required_loot_level_offset,
    _source_consumable_selective_loot_keywords,
    _source_caerlin_staff_candidate_shape_allowed,
    _source_hephaestus_sanctuary_candidate_shape_allowed,
    _source_hephaestus_dispatch_contract_allowed,
    _source_ranked_healer_blindness_recovery_allowed,
    _source_ranked_hunt_stops,
    _source_ranked_sanctuary_candidate_research_open,
    _source_sanctuary_carrier_output_allowed,
)
from dd4tester.encounters import active_encounter_budget
from dd4tester.hunt_candidates import SourceCombatOutput, load_world_source
from dd4tester.starter import StarterPolicy


SOURCE_DIRECTORY = Path("runs/dd4-source/server/area")


def _level_39_healer_state() -> dict[str, object]:
    return {
        "level": 39,
        "hp": 918,
        "max_hp": 918,
        "mana": 500,
        "max_mana": 500,
        "room_vnum": "3054",
        "alignment": 1000,
        "character_class": "warrior",
        "subclass": "knight",
        "affects": (),
        "campaign_known_skills": (
            "armed combat knowledge",
            "armor",
            "defense knowledge",
            "dodge",
            "enhanced damage",
            "headbutt",
            "kick",
            "parry",
            "second attack",
            "shield block",
            "stun",
            "third attack",
            "unarmed combat knowledge",
        ),
        "campaign_known_skill_levels": {
            "enhanced damage": 68,
            "headbutt": 68,
            "kick": 68,
            "parry": 65,
            "second attack": 64,
            "stun": 68,
            "third attack": 63,
        },
        "equipment": [
            {
                "vnum": 20508,
                "item_type": 5,
                "name": "a bishop piece",
                "keywords": "bishop",
                "wear_loc": 16,
                "slot": "wield",
                "level": 36,
            }
        ],
        "currencies": {
            "platinum": 0,
            "gold": 4,
            "silver": 0,
            "copper": 1,
            "electrum": 0,
        },
        "world_boot_id": "test-boot",
    }


def test_campaign_staff_detection_parses_ansi_nested_char_items() -> None:
    state = {
        "inventory": (
            '[[{"quan":"1","short_desc":"\\u001b[38;5;121m(Glowing)'
            '\\u001b[0m Staff of the Bard"}]]'
        )
    }

    assert _campaign_has_caerlin_staff(state)


def test_campaign_staff_detection_accepts_structured_gmcp_equipment() -> None:
    state = {
        "equipment": [
            {
                "name": "Staff of the Bard",
                "slot": "hold",
                "vnum": 19173,
            }
        ]
    }

    assert _campaign_has_caerlin_staff(state)


def test_caerlin_is_selected_as_exact_staff_recovery_carrier() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()

    selection = _select_source_consumable_candidate(
        state,
        spell_name="sanctuary",
        short_description=None,
        source_directory=SOURCE_DIRECTORY,
        source_world=world,
        require_unarmed=True,
        required_reset=(19004, 19068),
    )

    assert selection is not None
    candidate, object_vnums = selection
    assert (candidate.mobile_vnum, candidate.room_vnum) == (19004, 19068)
    assert object_vnums == (19173,)
    assert _source_caerlin_staff_candidate_shape_allowed(candidate, world)
    assert candidate.route_economic_hunt_mobile_vnums == (19036,)
    assert candidate.autonomy_rejections == (
        "target has special procedure spec_cast_cleric",
    )
    assert _source_ranked_healer_blindness_recovery_allowed(
        candidate,
        state,
        source_world=world,
    )
    assert _source_sanctuary_carrier_output_allowed(
        candidate,
        state,
        policy_id=_SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id,
        character_level=39,
        source_world=world,
    )


def test_alternate_sanctuary_carrier_stays_closed_after_same_boot_absence() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    state["campaign_source_revision"] = "test-source"
    state["campaign_research_results"] = {
        "source-ranked-hunt-olympus-916-927-39": {
            "boot_id": "test-boot",
            "absent": True,
            "observed": False,
            "viable": False,
        }
    }

    assert (
        _select_source_ranked_alternate_sanctuary_candidate(
            state,
            source_directory=SOURCE_DIRECTORY,
            source_world=world,
        )
        is None
    )


def test_alternate_policy_absence_closes_candidate_specific_carrier() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    state["campaign_source_revision"] = "test-source"
    state["campaign_research_results"] = {
        _SOURCE_RANKED_SANCTUARY_ALTERNATE_POLICY.policy_id: {
            "boot_id": "test-boot",
            "absent": True,
            "observed": False,
            "viable": False,
        }
    }

    assert (
        _select_source_ranked_alternate_sanctuary_candidate(
            state,
            source_directory=SOURCE_DIRECTORY,
            source_world=world,
        )
        is None
    )


def test_alternate_sanctuary_carrier_stays_closed_without_boot_boundary() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    state.pop("world_boot_id")
    state["campaign_source_revision"] = "test-source"
    state["campaign_research_results"] = {
        "source-ranked-hunt-olympus-916-927-39": {
            "absent": True,
            "observed": False,
            "viable": False,
        }
    }

    assert (
        _select_source_ranked_alternate_sanctuary_candidate(
            state,
            source_directory=SOURCE_DIRECTORY,
            source_world=world,
        )
        is None
    )


def test_alternate_sanctuary_carrier_reopens_after_reboot() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    state["campaign_source_revision"] = "test-source"
    state["world_boot_id"] = "next-boot"
    state["campaign_research_results"] = {
        "source-ranked-hunt-olympus-916-927-39": {
            "boot_id": "previous-boot",
            "absent": True,
            "observed": False,
            "viable": False,
        }
    }

    selection = _select_source_ranked_alternate_sanctuary_candidate(
        state,
        source_directory=SOURCE_DIRECTORY,
        source_world=world,
    )

    assert selection is not None
    candidate, object_vnums = selection
    assert (candidate.mobile_vnum, candidate.room_vnum) == (916, 927)
    assert object_vnums == (905, 926)
    assert _SOURCE_RANKED_SANCTUARY_ALTERNATE_POLICY.execution == (
        "moria-sanctuary-hunt"
    )


def test_olympus_sanctuary_policy_selects_exact_staff_reset() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    state["campaign_source_revision"] = "test-source"
    state["campaign_research_results"] = {
        _SOURCE_RANKED_SANCTUARY_ALTERNATE_POLICY.policy_id: {
            "boot_id": "test-boot",
            "level": 39,
            "fatal_failure": True,
            "completed_kill": False,
        }
    }

    selection = _select_source_ranked_olympus_sanctuary_candidate(
        state,
        source_directory=SOURCE_DIRECTORY,
        source_world=world,
    )

    assert selection is not None
    candidate, object_vnums = selection
    assert (candidate.mobile_vnum, candidate.room_vnum) == (916, 927)
    assert candidate.area_file.casefold() == "olympus.are"
    assert object_vnums == (905,)
    assert _SOURCE_RANKED_OLYMPUS_SANCTUARY_POLICY.policy_id not in (
        state["campaign_research_results"]
    )


def test_olympus_sanctuary_policy_closes_after_its_own_fatal_result() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    state["campaign_source_revision"] = "test-source"
    state["campaign_research_results"] = {
        _SOURCE_RANKED_OLYMPUS_SANCTUARY_POLICY.policy_id: {
            "boot_id": "test-boot",
            "level": 39,
            "fatal_failure": True,
            "completed_kill": False,
        }
    }

    assert (
        _select_source_ranked_olympus_sanctuary_candidate(
            state,
            source_directory=SOURCE_DIRECTORY,
            source_world=world,
        )
        is None
    )


def test_olympus_sanctuary_carrier_closes_after_same_boot_source_xp_loss() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    state["campaign_source_ranked_xp_loss_policies"] = [
        {
            "boot_id": "test-boot",
            "level": 39,
            "policy_id": "source-ranked-hunt-olympus-916-927-39",
            "loss_count": 1,
            "loss_event_id": 18218,
            "xp_delta": -1000,
        }
    ]

    assert _sanctuary_policy_retry_terminal(
        state,
        _SOURCE_RANKED_OLYMPUS_SANCTUARY_POLICY.policy_id,
    )
    assert (
        _select_source_ranked_olympus_sanctuary_candidate(
            state,
            source_directory=SOURCE_DIRECTORY,
            source_world=world,
        )
        is None
    )
    assert (
        _select_source_consumable_candidate(
            state,
            spell_name="sanctuary",
            short_description="an ivory staff",
            source_directory=SOURCE_DIRECTORY,
            source_world=world,
            require_unarmed=True,
            required_reset=(916, 927),
        )
        is None
    )


def test_sanctuary_maintenance_can_use_fresh_out_of_band_armed_adept() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    state.update(
        {
            "level": 40,
            "hp": 962,
            "max_hp": 962,
            _SOURCE_REVISION_KEY: "test-source",
            "campaign_research_results": {
                "source-ranked-hunt-olympus-905-926-40": {
                    "boot_id": "test-boot",
                    "completed_kill": False,
                    "consider_viable": False,
                    "observed": True,
                    "viable": False,
                }
            },
        }
    )

    selection = _select_source_ranked_sanctuary_maintenance_candidate(
        state,
        source_directory=SOURCE_DIRECTORY,
        source_world=world,
        excluded_target_stops=((916, 927), (907, 925), (908, 937)),
        level_ceiling_offset=100,
        require_unarmed=False,
        allowed_target_specials=("spec_cast_adept",),
        allow_armed_carrier=True,
    )

    assert selection is not None
    candidate, object_vnums = selection
    assert (candidate.mobile_vnum, candidate.room_vnum) == (905, 926)
    assert candidate.estimated_level_range == (42, 46)
    assert candidate.specials == ("spec_cast_adept",)
    assert len(candidate.equipped_weapons) == 1
    assert object_vnums == (926,)
    assert (
        _source_consumable_required_loot_level_offset(
            candidate,
            world,
            character_level=40,
            allow_out_of_band=True,
        )
        == 6
    )


def test_olympus_adept_policy_selects_athena_after_alchemist_closes() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    state["campaign_source_revision"] = "test-source"
    state["campaign_research_results"] = {
        _SOURCE_RANKED_OLYMPUS_SANCTUARY_POLICY.policy_id: {
            "boot_id": "test-boot",
            "level": 39,
            "fatal_failure": True,
            "completed_kill": False,
        }
    }

    selection = _select_source_ranked_olympus_adept_sanctuary_candidate(
        state,
        source_directory=SOURCE_DIRECTORY,
        source_world=world,
    )

    assert selection is not None
    candidate, object_vnums = selection
    assert (candidate.mobile_vnum, candidate.room_vnum) == (907, 925)
    assert candidate.specials == ("spec_cast_adept",)
    assert object_vnums == (905,)
    assert _source_consumable_required_loot_level_offset(candidate, world) == 5
    assert _SOURCE_RANKED_OLYMPUS_ADEPT_SANCTUARY_POLICY.policy_id not in (
        state["campaign_research_results"]
    )


def test_olympus_adept_policy_uses_athena_nectar_for_negative_alignment() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    state.update(
        {
            "level": 40,
            "alignment": -766,
            "campaign_source_revision": "test-source",
        }
    )

    selection = _select_source_ranked_olympus_adept_sanctuary_candidate(
        state,
        source_directory=SOURCE_DIRECTORY,
        source_world=world,
    )

    assert selection is not None
    candidate, object_vnums = selection
    assert (candidate.mobile_vnum, candidate.room_vnum) == (907, 925)
    assert object_vnums == (926,)


def test_olympus_adept_policy_keeps_its_own_fatal_result_closed() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    state["campaign_source_revision"] = "test-source"
    state["campaign_research_results"] = {
        _SOURCE_RANKED_OLYMPUS_ADEPT_SANCTUARY_POLICY.policy_id: {
            "boot_id": "test-boot",
            "level": 39,
            "fatal_failure": True,
            "completed_kill": False,
        }
    }

    assert (
        _select_source_ranked_olympus_adept_sanctuary_candidate(
            state,
            source_directory=SOURCE_DIRECTORY,
            source_world=world,
        )
        is None
    )


def test_olympus_hephaestus_policy_selects_exact_lightning_carrier() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    state["campaign_source_revision"] = "test-source"
    selection = _select_source_ranked_olympus_hephaestus_sanctuary_candidate(
        state,
        source_directory=SOURCE_DIRECTORY,
        source_world=world,
    )

    assert selection is not None
    candidate, object_vnums = selection
    assert (candidate.mobile_vnum, candidate.room_vnum) == (908, 937)
    assert candidate.specials == ("spec_breath_lightning",)
    assert object_vnums == (926,)
    assert _source_hephaestus_sanctuary_candidate_shape_allowed(candidate, world)
    assert _SOURCE_RANKED_OLYMPUS_HEPHAESTUS_SANCTUARY_POLICY.minimum_level == 38
    stops = _source_ranked_hunt_stops(
        candidate,
        world,
        character_level=39,
        state=state,
    )
    endpoint = next(stop for stop in stops if stop.target is not None)
    assert endpoint.require_sanctuary is False
    assert endpoint.allow_source_hephaestus_special_endpoint is True


def test_hephaestus_policy_uses_source_consumable_dispatch_contract() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    selection = _select_source_ranked_olympus_hephaestus_sanctuary_candidate(
        state,
        source_directory=SOURCE_DIRECTORY,
        source_world=world,
    )

    assert (
        _SOURCE_RANKED_OLYMPUS_HEPHAESTUS_SANCTUARY_POLICY.policy_id
        in _SOURCE_CONSUMABLE_SANCTUARY_POLICY_IDS
    )
    assert selection is not None
    candidate, object_vnums = selection
    assert _source_hephaestus_dispatch_contract_allowed(
        candidate,
        object_vnums,
    )
    assert not _source_hephaestus_dispatch_contract_allowed(candidate, (4050,))


def test_misrouted_hephaestus_receipt_is_invalidated_without_editing_run() -> None:
    policy_id = _SOURCE_RANKED_OLYMPUS_HEPHAESTUS_SANCTUARY_POLICY.policy_id

    class MemoryStorage:
        def __init__(self) -> None:
            self.segments = [{
                "id": 18449,
                "sequence": 800,
                "phase": policy_id,
                "run_id": 19055,
            }]
            self.checkpoints: list[dict[str, object]] = []

        def list_recent_campaign_segments(self, _campaign_id: int, *, limit: int):
            return self.segments[:limit]

        def record_campaign_checkpoint(self, _campaign_id: int, **kwargs):
            self.checkpoints.append(kwargs)

    storage = MemoryStorage()
    state = {
        "level": 39,
        "world_boot_id": "test-boot",
        "campaign_source_revision": "test-source",
        "campaign_research_results": {
            policy_id: {
                "observed": True,
                "viable": True,
                "completed_kill": False,
                "required_object_acquired": True,
                "required_object_vnums": [4050],
                "boot_id": "test-boot",
            }
        },
    }
    checkpoint = {
        "segment_id": 18449,
        "run_id": 19055,
        "phase": policy_id,
    }

    repaired = _repair_source_resource_dispatch_contract(
        storage,
        35,
        checkpoint,
        state,
    )

    assert policy_id not in repaired.get("campaign_research_results", {})
    assert repaired["campaign_source_resource_dispatch_contract_repair"][
        "observed_object_vnums"
    ] == [4050]
    assert storage.checkpoints[0]["reason"] == (
        "source_resource_dispatch_contract_repaired"
    )


def test_invalidated_misrouted_hephaestus_receipt_reopens_selector() -> None:
    policy_id = _SOURCE_RANKED_OLYMPUS_HEPHAESTUS_SANCTUARY_POLICY.policy_id
    state = _level_39_healer_state()
    state.update(
        {
            "world_boot_id": "test-boot",
            "campaign_source_revision": "test-source",
            "campaign_source_resource_dispatch_contract_repair": {
                "status": "invalidated",
                "policy_id": policy_id,
                "boot_id": "test-boot",
                "source_revision": "test-source",
                "observed_object_vnums": [4050],
                "expected_object_vnums": [926],
            },
            "campaign_research_results": {
                policy_id: {
                    "boot_id": "test-boot",
                    "required_object_acquired": True,
                    "required_object_vnums": [4050],
                    "viable": True,
                }
            },
        }
    )
    candidate = SimpleNamespace(
        mobile_vnum=908,
        room_vnum=937,
    )

    assert _source_ranked_sanctuary_candidate_research_open(
        state,
        candidate,
        policy_id=policy_id,
    )


def test_olympus_hephaestus_policy_keeps_its_own_fatal_result_closed() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    state["campaign_source_revision"] = "test-source"
    state["campaign_research_results"] = {
        _SOURCE_RANKED_OLYMPUS_HEPHAESTUS_SANCTUARY_POLICY.policy_id: {
            "boot_id": "test-boot",
            "level": 39,
            "fatal_failure": True,
            "completed_kill": False,
        }
    }

    assert (
        _select_source_ranked_olympus_hephaestus_sanctuary_candidate(
            state,
            source_directory=SOURCE_DIRECTORY,
            source_world=world,
        )
        is None
    )


def test_olympus_viability_result_opens_athena_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    config_path = Path("runs/heroes/dorrik/campaign.yaml")
    runner = CampaignRunner(load_campaign_spec(config_path), config_path)
    runner._source_world = world
    runner._boot_id = "test-boot"
    runner._select_source_ranked_candidate = lambda _state, **_kwargs: None
    monkeypatch.setattr(
        "dd4tester.campaign.policy_for",
        lambda *_args, **_kwargs: _SOURCE_RANKED_HUNT_POLICY,
    )
    monkeypatch.setattr(
        "dd4tester.campaign._caerlin_staff_handoff_repair_allowed",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        "dd4tester.campaign._caerlin_staff_retry_open",
        lambda *_args, **_kwargs: False,
    )
    state = _level_39_healer_state()
    state.update(
        {
            "inventory": [[
                {"short_desc": "a big pot pie"},
                {"short_desc": "a buffalo water skin"},
            ]],
            "hunger": 100,
            "thirst": 100,
            "move": 500,
            "max_move": 500,
            "affects": [{"name": "fly", "duration": "100"}],
            _SOURCE_REVISION_KEY: "test-source",
            "campaign_source_resource_reserves": {},
            "campaign_fastwalk_training_complete": True,
            "campaign_training_deficit_repair": {
                "attempted": True,
                "boot_id": "test-boot",
                "deficits": [],
            },
            "campaign_training_audit": {
                "observed": True,
                "boot_id": "test-boot",
                "level": 39,
                "physical_practices": 0,
                "intellectual_practices": 0,
                "deficits": [],
            },
            "campaign_protection_recovery_required": {
                "boot_id": "test-boot",
                "level": 39,
                "loss_count": 1,
                "policy_id": "source-ranked-hunt-quake-12038-12199-39",
                "trigger": "hard_health_floor",
                "xp_delta": 0,
            },
            "campaign_research_results": {
                _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id: {
                    "boot_id": "test-boot",
                    "level": 39,
                    "fatal_failure": True,
                    "completed_kill": False,
                },
                _SOURCE_RANKED_SANCTUARY_ALTERNATE_POLICY.policy_id: {
                    "boot_id": "test-boot",
                    "level": 39,
                    "fatal_failure": True,
                    "completed_kill": False,
                },
                _SOURCE_RANKED_OLYMPUS_SANCTUARY_POLICY.policy_id: {
                    "boot_id": "test-boot",
                    "level": 39,
                    "observed": True,
                    "completed_kill": False,
                    "viable": False,
                },
            },
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "closed",
                "outcome": "route_hazard",
                "retry_count": 1,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
            },
        }
    )

    assert _sanctuary_policy_retry_terminal(
        state,
        _SOURCE_RANKED_OLYMPUS_SANCTUARY_POLICY.policy_id,
    )
    selected = runner._policy_without_learned_flight(state)

    assert selected.policy_id == _SOURCE_RANKED_OLYMPUS_ADEPT_SANCTUARY_POLICY.policy_id
    assert runner._selected_source_consumable_candidate is not None
    assert runner._selected_source_consumable_candidate.mobile_vnum == 907
    assert runner._selected_source_consumable_object_vnums == (905,)


def test_olympus_hephaestus_fallback_opens_after_athena_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    config_path = Path("runs/heroes/dorrik/campaign.yaml")
    runner = CampaignRunner(load_campaign_spec(config_path), config_path)
    runner._source_world = world
    runner._boot_id = "test-boot"
    runner._select_source_ranked_candidate = lambda _state, **_kwargs: None
    monkeypatch.setattr(
        "dd4tester.campaign.policy_for",
        lambda *_args, **_kwargs: _SOURCE_RANKED_HUNT_POLICY,
    )
    monkeypatch.setattr(
        "dd4tester.campaign._caerlin_staff_handoff_repair_allowed",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        "dd4tester.campaign._caerlin_staff_retry_open",
        lambda *_args, **_kwargs: False,
    )
    state = _level_39_healer_state()
    state.update(
        {
            "inventory": [[
                {"short_desc": "a big pot pie"},
                {"short_desc": "a buffalo water skin"},
            ]],
            "hunger": 100,
            "thirst": 100,
            "move": 500,
            "max_move": 500,
            "affects": [{"name": "fly", "duration": "100"}],
            _SOURCE_REVISION_KEY: "test-source",
            "campaign_source_resource_reserves": {},
            "campaign_fastwalk_training_complete": True,
            "campaign_training_deficit_repair": {
                "attempted": True,
                "boot_id": "test-boot",
                "deficits": [],
            },
            "campaign_training_audit": {
                "observed": True,
                "boot_id": "test-boot",
                "level": 39,
                "physical_practices": 0,
                "intellectual_practices": 0,
                "deficits": [],
            },
            "campaign_protection_recovery_required": {
                "boot_id": "test-boot",
                "level": 39,
                "loss_count": 1,
                "policy_id": "source-ranked-hunt-quake-12038-12199-39",
                "trigger": "hard_health_floor",
                "xp_delta": 0,
            },
            "campaign_research_results": {
                _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id: {
                    "boot_id": "test-boot",
                    "level": 39,
                    "fatal_failure": True,
                    "completed_kill": False,
                },
                _SOURCE_RANKED_SANCTUARY_ALTERNATE_POLICY.policy_id: {
                    "boot_id": "test-boot",
                    "level": 39,
                    "fatal_failure": True,
                    "completed_kill": False,
                },
                _SOURCE_RANKED_OLYMPUS_SANCTUARY_POLICY.policy_id: {
                    "boot_id": "test-boot",
                    "level": 39,
                    "observed": True,
                    "completed_kill": False,
                    "viable": False,
                },
                _SOURCE_RANKED_OLYMPUS_ADEPT_SANCTUARY_POLICY.policy_id: {
                    "boot_id": "test-boot",
                    "level": 39,
                    "fatal_failure": True,
                    "completed_kill": False,
                },
            },
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "closed",
                "outcome": "route_hazard",
                "retry_count": 1,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
            },
        }
    )

    assert _sanctuary_policy_retry_terminal(
        state,
        _SOURCE_RANKED_OLYMPUS_ADEPT_SANCTUARY_POLICY.policy_id,
    )
    selected = runner._policy_without_learned_flight(state)

    assert selected.policy_id == (
        _SOURCE_RANKED_OLYMPUS_HEPHAESTUS_SANCTUARY_POLICY.policy_id
    )
    assert runner._selected_source_consumable_candidate is not None
    assert runner._selected_source_consumable_candidate.mobile_vnum == 908
    assert runner._selected_source_consumable_object_vnums == (926,)


def test_caerlin_recovery_stop_is_unprotected_but_healer_backed() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    candidate, _object_vnums = _select_source_consumable_candidate(
        state,
        spell_name="sanctuary",
        short_description=None,
        source_directory=SOURCE_DIRECTORY,
        source_world=world,
        require_unarmed=True,
        required_reset=(19004, 19068),
    )
    assert candidate is not None

    stops = _source_ranked_hunt_stops(
        candidate,
        world,
        character_level=39,
        state=state,
    )
    locator = next(stop for stop in stops if stop.where_target == "caerlin")
    endpoint = next(
        stop
        for stop in stops
        if stop.target is not None and "19068" in stop.route_vnums
    )

    assert locator.actions == ("where caerlin",)
    assert locator.where_source_mobile_vnum == 19004
    assert dict(locator.where_location_routes)["the path"] == ("19002",)
    assert any(
        origin == "19068"
        and label == "the path"
        and route
        and route[-1] == "19002"
        for origin, label, route in locator.where_relocation_routes
    )
    assert endpoint.source_mobile_vnum == 19004
    assert endpoint.require_sanctuary is False
    assert endpoint.allow_source_caerlin_special_endpoint is True
    assert endpoint.allow_healer_blindness_recovery is True
    assert endpoint.source_specials == ("spec_cast_cleric",)
    assert endpoint.outbound_intercept_room_vnums == ("19002",)


def test_caerlin_staff_uses_selective_loot_keyword() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)

    assert _source_consumable_selective_loot_keywords(
        world.objects[19173]
    ) == ("staff",)


def test_caerlin_staff_special_follows_the_wanderer_through_opened_doors() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    candidate, _object_vnums = _select_source_consumable_candidate(
        state,
        spell_name="sanctuary",
        short_description=None,
        source_directory=SOURCE_DIRECTORY,
        source_world=world,
        require_unarmed=True,
        required_reset=(19004, 19068),
    )
    assert candidate is not None
    endpoint = next(
        stop
        for stop in _source_ranked_hunt_stops(
            candidate,
            world,
            character_level=39,
            state=state,
        )
        if stop.target is not None and "19068" in stop.route_vnums
    )
    policy = StarterPolicy.__new__(StarterPolicy)
    policy.source_world = world
    endpoint = replace(endpoint, source_loot_object_vnums=())

    assert policy._source_stop_has_caerlin_staff_special(endpoint)
    assert policy._source_stop_has_caerlin_staff_special(
        endpoint,
        room_vnum="19002",
    )
    assert policy._source_stop_has_caerlin_staff_special(
        endpoint,
        room_vnum="19003",
    )
    assert not policy._source_stop_has_caerlin_staff_special(
        endpoint,
        room_vnum="3001",
    )


def test_live_budget_requires_the_exact_caerlin_allowlist() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    output = SourceCombatOutput(
        action="weapon strike",
        minimum_damage=40,
        expected_damage=70,
        maximum_damage=100,
        resource="actions",
        resource_cost=0,
        conservative_damage=56,
    )
    enemy = {
        "isnpc": "19004",
        "level": 35,
        "hp": 600,
        "maxhp": 600,
    }
    common = dict(
        world=world,
        enemies=(enemy,),
        character_level=39,
        hp=918,
        max_hp=918,
        mana=500,
        max_mana=500,
        output=output,
        target_hp_evidence_only=True,
        maximum_level_offsets_by_vnum={19004: 1},
    )

    rejected = active_encounter_budget(**common)
    accepted = active_encounter_budget(
        **common,
        allowed_caerlin_special_vnums=(19004,),
    )

    assert rejected.allowed is False
    assert "separate source-hazard" in rejected.reason
    assert accepted.allowed is True


def test_caerlin_locator_miss_is_persisted_and_allows_one_retry() -> None:
    previous = _level_39_healer_state()
    previous.update(
        {
            "campaign_source_revision": "test-source",
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "attempted",
                "retry_count": 0,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
            },
        }
    )
    current = {
        **previous,
        _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: None,
        "campaign_fastwalk_abort_reason": (
            "positive `where` result remains in the already-checked room "
            "with no unsearched source-safe relocation"
        ),
        "campaign_fastwalk_target_present_observed": True,
        "campaign_fastwalk_target_absent": False,
        "campaign_fastwalk_source_absent_sightings": [
            {"target": "caerlin", "room_vnum": "19061"}
        ],
        "campaign_fastwalk_where_decisions": [
            {
                "source_mobile_vnum": 19004,
                "target": "caerlin",
                "locations": ["bend in the path"],
            }
        ],
        "campaign_objective_kills": [],
        "campaign_completed_kills": [],
    }

    merged = _campaign_segment_end_state(
        previous,
        current,
        execution="moria-sanctuary-hunt",
        policy_id=_SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id,
    )

    assert merged[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY]["retry_count"] == 0
    assert _caerlin_staff_locator_retry_allowed(merged)
    merged["campaign_fastwalk_abort_reason"] = (
        "refreshed `where` located the wandering target outside the "
        "source-safe relocation graph"
    )
    assert _caerlin_staff_locator_retry_allowed(merged)


def test_caerlin_locator_retry_closes_after_second_miss() -> None:
    previous = _level_39_healer_state()
    previous.update(
        {
            "campaign_source_revision": "test-source",
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "attempted",
                "retry_count": 1,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
            },
        }
    )
    current = {
        **previous,
        "campaign_fastwalk_route": "source sanctuary reserve caerlin 19068",
    }

    merged = _campaign_segment_end_state(
        previous,
        current,
        execution="moria-sanctuary-hunt",
        policy_id=_SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id,
    )

    marker = merged[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY]
    assert marker["status"] == "closed"
    assert marker["outcome"] == "locator_retry_missed"
    assert not _caerlin_staff_locator_retry_allowed(merged)


def test_caerlin_combat_abort_closes_attempt_without_locator_retry() -> None:
    previous = _level_39_healer_state()
    previous.update(
        {
            "campaign_source_revision": "test-source",
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "attempted",
                "retry_count": 0,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
            },
        }
    )
    current = {
        **previous,
        "fastwalk_route": "source sanctuary reserve caerlin 19068",
        "campaign_fastwalk_abort_reason": (
            "field combat aborted for safety: health at or below 34%"
        ),
        "campaign_fastwalk_target_present_observed": True,
        "campaign_fastwalk_target_absent": False,
        "campaign_fastwalk_consider_outcomes": {"caerlin": True},
        "campaign_fastwalk_source_consider_outcomes": {
            "source-ranked-hunt-mirror-realm-19004-19068-39": True
        },
        "campaign_objective_kills": [],
        "campaign_completed_kills": [],
    }

    merged = _campaign_segment_end_state(
        previous,
        current,
        execution="moria-sanctuary-hunt",
        policy_id=_SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id,
    )

    marker = merged[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY]
    assert marker["status"] == "closed"
    assert marker["outcome"] == "combat_aborted_no_acquisition"
    assert marker["retry_count"] == 0


def test_stale_caerlin_combat_abort_marker_is_reconciled_from_history() -> None:
    state = _level_39_healer_state()
    state.update(
        {
            "campaign_source_revision": "test-source",
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "attempted",
                "retry_count": 0,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
            },
        }
    )
    end_state = {
        **state,
        "fastwalk_route": "source sanctuary reserve caerlin 19068",
        "campaign_fastwalk_abort_reason": (
            "field combat aborted for safety: health at or below 34%"
        ),
        "campaign_fastwalk_target_present_observed": True,
        "campaign_fastwalk_target_absent": False,
        "campaign_fastwalk_consider_outcomes": {"caerlin": True},
        "campaign_fastwalk_source_consider_outcomes": {
            "source-ranked-hunt-mirror-realm-19004-19068-39": True
        },
        "campaign_objective_kills": [],
        "campaign_completed_kills": [],
    }
    segments = [
        {
            "id": 18290,
            "phase": _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id,
            "status": "success",
            "end_state_json": json.dumps(end_state),
        }
    ]

    repaired = _repair_caerlin_staff_attempt_metadata(state, segments)

    marker = repaired[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY]
    assert marker["status"] == "closed"
    assert marker["outcome"] == "combat_aborted_no_acquisition"
    assert marker["closed_segment_id"] == 18290


def test_closed_caerlin_attempt_stays_closed_for_same_boot_and_source() -> None:
    state = _level_39_healer_state()
    attempt = {
        "boot_id": "test-boot",
        "level": 39,
        "source_revision": "test-source",
        "status": "closed",
    }

    assert not _caerlin_staff_retry_open(
        {**state, "campaign_source_revision": "test-source"},
        attempt,
        locator_retry=False,
        handoff_repair=False,
    )
    assert _caerlin_staff_retry_open(
        {**state, "campaign_source_revision": "new-source"},
        attempt,
        locator_retry=False,
        handoff_repair=False,
    )


def test_caerlin_staff_can_be_reacquired_once_after_liquidation_loss() -> None:
    state = _level_39_healer_state()
    state.update(
        {
            "campaign_source_revision": "test-source",
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "succeeded",
                "outcome": "staff_acquired",
                "retry_count": 1,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
            },
            "campaign_source_resource_reserves": {},
            "inventory": "[ { \"short_desc\": \"a leather jerkin\" } ]",
        }
    )

    assert _caerlin_staff_reserve_reacquisition_allowed(state)
    state[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY][
        _CAERLIN_STAFF_RESERVE_REACQUISITION_KEY
    ] = True
    assert not _caerlin_staff_reserve_reacquisition_allowed(state)


def test_moria_4071_reserve_reacquisition_is_one_shot() -> None:
    state = _level_39_healer_state()
    state.update(
        {
            _SOURCE_REVISION_KEY: "current-source",
            "campaign_source_resource_reserves": {},
            _MORIA_SANCTUARY_SECOND_FIXED_RESET_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "old-source",
                "status": "attempted",
                "source_mobile_vnum": 4055,
                "source_reset_room_vnum": 4071,
                "source_object_vnum": 4050,
            },
            "campaign_research_results": {
                _MORIA_SANCTUARY_SECOND_FIXED_RESET_POLICY_ID: {
                    "boot_id": "test-boot",
                    "level": 39,
                    "observed": True,
                    "completed_kill": False,
                    "required_object_acquired": True,
                    "required_object_vnums": [4050],
                    "viable": True,
                }
            },
        }
    )

    assert _moria_sanctuary_second_fixed_reset_reacquisition_allowed(state)
    state[_MORIA_SANCTUARY_SECOND_FIXED_RESET_ATTEMPT_KEY][
        _MORIA_SANCTUARY_SECOND_FIXED_RESET_REACQUISITION_KEY
    ] = True
    assert not _moria_sanctuary_second_fixed_reset_reacquisition_allowed(state)


def test_moria_4071_reacquisition_selects_exact_potion_reset() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    state[_SOURCE_REVISION_KEY] = "current-source"

    selection = _select_source_ranked_moria_4071_reacquisition_candidate(
        state,
        source_directory=SOURCE_DIRECTORY,
        source_world=world,
    )

    assert selection is not None
    candidate, object_vnums = selection
    assert (candidate.mobile_vnum, candidate.room_vnum) == (4055, 4071)
    assert candidate.area_file.casefold() == "moria.are"
    assert object_vnums == (4050,)


def test_caerlin_source_revision_retry_preempts_exhausted_alternate_policy() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    runner = CampaignRunner.__new__(CampaignRunner)
    runner.progress_callback = None
    runner._gear_catalog = None
    runner._source_world = world
    runner._selected_source_consumable_candidate = None
    runner._selected_source_consumable_object_vnums = ()
    runner._policy_without_learned_flight = (
        lambda _state: _SOURCE_RANKED_SANCTUARY_ALTERNATE_POLICY
    )
    runner._catacombs_key_recovery_policy_if_ready = lambda _state: None
    runner.spec = SimpleNamespace(
        character=SimpleNamespace(character_class="warrior")
    )
    state = _level_39_healer_state()
    state.update(
        {
            "inventory": [[{"short_desc": "a big pot pie"}]],
            _SOURCE_REVISION_KEY: "new-source",
            "campaign_source_resource_reserves": {},
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "old-source",
                "status": "closed",
                "outcome": "reserve_reacquisition_missed",
                "retry_count": 1,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
                _CAERLIN_STAFF_RESERVE_REACQUISITION_KEY: True,
            },
        }
    )

    assert _caerlin_staff_source_revision_retry_allowed(state)
    selected = runner._policy_for_state(state)

    assert selected.policy_id == _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
    assert runner._selected_source_consumable_candidate is not None
    assert runner._selected_source_consumable_candidate.mobile_vnum == 19004
    assert runner._selected_source_consumable_object_vnums == (19173,)
    assert state[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY][
        _CAERLIN_STAFF_RESERVE_REACQUISITION_KEY
    ] is True


def test_caerlin_source_revision_retry_is_available_to_maintenance_selector() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    runner = CampaignRunner.__new__(CampaignRunner)
    runner.progress_callback = None
    runner._gear_catalog = None
    runner._source_world = world
    runner._selected_source_consumable_candidate = None
    runner._selected_source_consumable_object_vnums = ()
    state = _level_39_healer_state()
    state.update(
        {
            "inventory": [[{"short_desc": "a big pot pie"}]],
            _SOURCE_REVISION_KEY: "new-source",
            "campaign_source_resource_reserves": {},
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "old-source",
                "status": "closed",
                "outcome": "reserve_reacquisition_missed",
                "retry_count": 1,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
                _CAERLIN_STAFF_RESERVE_REACQUISITION_KEY: True,
            },
        }
    )

    selected = runner._select_caerlin_source_revision_sanctuary_fallback(
        state,
        practice_skill="enhanced damage",
    )

    assert selected is not None
    assert selected.policy_id == _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
    assert runner._selected_source_consumable_candidate is not None
    assert runner._selected_source_consumable_candidate.mobile_vnum == 19004
    assert runner._selected_source_consumable_object_vnums == (19173,)
    assert state[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY]["status"] == "attempted"


def test_out_of_band_sanctuary_maintenance_admits_apollo_armed_carrier() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()

    selection = _select_source_ranked_sanctuary_maintenance_candidate(
        state,
        source_directory=SOURCE_DIRECTORY,
        source_world=world,
        level_ceiling_offset=100,
        require_unarmed=False,
        allowed_target_specials=("spec_cast_adept",),
        allow_armed_carrier=True,
    )

    assert selection is not None
    candidate, object_vnums = selection
    assert (candidate.mobile_vnum, candidate.room_vnum) == (905, 926)
    assert object_vnums == (926,)
    assert candidate.equipped_weapons == ("a silver bow",)


def test_newer_live_liquidation_loss_reopens_caerlin_reacquisition() -> None:
    state = _level_39_healer_state()
    state.update(
        {
            "campaign_source_revision": "new-source",
            "campaign_source_resource_reserves": {
                "sanctuary": {
                    "effect": "sanctuary",
                    "object_vnum": 19173,
                    "object_description": "staff of the bard",
                    "mode": "staff",
                    "charges_remaining": 9,
                }
            },
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "old-source",
                "status": "closed",
                "outcome": "reserve_reacquisition_missed",
                "retry_count": 1,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
                _CAERLIN_STAFF_RESERVE_REACQUISITION_KEY: True,
            },
        }
    )

    repaired = _repair_stale_caerlin_staff_reserve(
        state,
        {
            **state,
            "inventory": "[[{\"short_desc\": \"a bard's amulet\"}]]",
        },
        source_revision="new-source",
    )

    assert repaired["campaign_source_resource_reserves"] == {}
    assert repaired[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY]["status"] == "succeeded"
    assert repaired[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY][
        _CAERLIN_STAFF_RESERVE_REACQUISITION_KEY
    ] is False
    assert _caerlin_staff_reserve_reacquisition_allowed(repaired)


def test_live_nested_staff_inventory_keeps_caerlin_reserve() -> None:
    state = _level_39_healer_state()
    reserve = {
        "effect": "sanctuary",
        "object_vnum": 19173,
        "object_description": "staff of the bard",
        "mode": "staff",
        "charges_remaining": 9,
    }
    state.update({"campaign_source_resource_reserves": {"sanctuary": reserve}})
    live_state = {
        **state,
        "inventory": (
            '[[{"quan":"1","short_desc":"\\u001b[38;5;121m(Glowing)'
            '\\u001b[0m Staff of the Bard"}]]'
        ),
    }

    repaired = _repair_stale_caerlin_staff_reserve(
        state,
        live_state,
        source_revision="test-source",
    )

    assert repaired["campaign_source_resource_reserves"] == {
        "sanctuary": reserve
    }


def test_structured_live_staff_rebuilds_missing_caerlin_reserve() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    state.update(
        {
            "world_boot_id": "test-boot",
            "campaign_source_revision": "test-source",
            "campaign_source_resource_reserves": {},
            "equipment": [
                {
                    "name": "Staff of the Bard",
                    "slot": "hold",
                    "vnum": 19173,
                }
            ],
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "succeeded",
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
            },
        }
    )

    repaired = _repair_stale_caerlin_staff_reserve(
        state,
        state,
        source_revision="test-source",
        source_world=world,
    )

    reserve = repaired["campaign_source_resource_reserves"]["sanctuary"]
    assert reserve["object_vnum"] == 19173
    assert reserve["charges_remaining"] == 10
    assert reserve["command"] == "brandish"
    assert _state_has_sanctuary_reserve(repaired)


def test_memory_staff_does_not_rebuild_caerlin_reserve() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    state.update(
        {
            "world_boot_id": "test-boot",
            "campaign_source_revision": "test-source",
            "campaign_source_resource_reserves": {},
            "inventory": '[[{"short_desc":"the memory staff"}]]',
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "closed",
                "outcome": "reserve_reacquisition_missed",
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
            },
        }
    )

    assert not _campaign_has_caerlin_staff(state)
    repaired = _repair_stale_caerlin_staff_reserve(
        state,
        state,
        source_revision="test-source",
        source_world=world,
    )

    assert repaired["campaign_source_resource_reserves"] == {}
    assert not _state_has_sanctuary_reserve(repaired)


def test_memory_staff_clears_a_false_caerlin_reserve_from_merged_state() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    state.update(
        {
            "world_boot_id": "test-boot",
            "campaign_source_revision": "test-source",
            "campaign_source_resource_reserves": {
                "sanctuary": {
                    "effect": "sanctuary",
                    "object_vnum": 19173,
                    "object_description": "memory staff",
                    "mode": "staff",
                    "charges_remaining": 10,
                }
            },
            "inventory": '[[{"short_desc":"the memory staff"}]]',
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "closed",
                "outcome": "reserve_reacquisition_missed",
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
            },
        }
    )
    live_state = {"inventory": '[[{"short_desc":"the memory staff"}]]'}

    repaired = _repair_stale_caerlin_staff_reserve(
        state,
        live_state,
        source_revision="test-source",
        source_world=world,
    )

    assert repaired["campaign_source_resource_reserves"] == {}
    assert not _state_has_sanctuary_reserve(repaired)


def test_caerlin_reacquisition_preempts_optional_rearming() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    runner = CampaignRunner.__new__(CampaignRunner)
    runner.progress_callback = None
    runner._gear_catalog = None
    runner._source_world = world
    runner._selected_source_consumable_candidate = None
    runner._selected_source_consumable_object_vnums = ()
    runner._policy_without_learned_flight = (
        lambda _state: _SOURCE_RANKED_SANCTUARY_ALTERNATE_POLICY
    )
    runner._catacombs_key_recovery_policy_if_ready = lambda _state: None
    runner.spec = SimpleNamespace(
        character=SimpleNamespace(character_class="warrior")
    )
    state = _level_39_healer_state()
    state.update(
        {
            "inventory": [[{"short_desc": "a big pot pie"}]],
            _SOURCE_REVISION_KEY: "test-source",
            "campaign_source_resource_reserves": {},
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "succeeded",
                "outcome": "staff_acquired",
                "retry_count": 1,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
            },
        }
    )

    selected = runner._policy_for_state(state)

    assert selected.policy_id == _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
    assert selected.execution == "moria-sanctuary-hunt"
    assert runner._selected_source_consumable_candidate is not None
    assert runner._selected_source_consumable_candidate.mobile_vnum == 19004
    assert runner._selected_source_consumable_object_vnums == (19173,)
    assert state[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY][
        _CAERLIN_STAFF_RESERVE_REACQUISITION_KEY
    ] is True


def test_prepared_moria_sanctuary_candidate_preempts_caerlin_reacquisition() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    runner = CampaignRunner.__new__(CampaignRunner)
    runner.progress_callback = None
    runner._gear_catalog = None
    runner._source_world = world
    runner._selected_source_consumable_candidate = SimpleNamespace(
        mobile_vnum=4055,
        room_vnum=4064,
        requires_flight=False,
    )
    runner._selected_source_consumable_object_vnums = (4050,)
    runner._policy_without_learned_flight = (
        lambda _state: _SOURCE_RANKED_SANCTUARY_ALTERNATE_POLICY
    )
    runner._catacombs_key_recovery_policy_if_ready = lambda _state: None
    runner.spec = SimpleNamespace(
        character=SimpleNamespace(character_class="warrior")
    )
    state = _level_39_healer_state()
    state.update(
        {
            "inventory": [[{"short_desc": "a big pot pie"}]],
            _SOURCE_REVISION_KEY: "test-source",
            "campaign_source_resource_reserves": {},
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "succeeded",
                "outcome": "staff_acquired",
                "retry_count": 1,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
            },
        }
    )

    selected = runner._policy_for_state(state)

    assert selected.policy_id == _SOURCE_RANKED_SANCTUARY_ALTERNATE_POLICY.policy_id
    assert runner._selected_source_consumable_candidate.mobile_vnum == 4055
    assert runner._selected_source_consumable_object_vnums == (4050,)
    assert state[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY].get(
        _CAERLIN_STAFF_RESERVE_REACQUISITION_KEY
    ) is not True


def test_moria_recovery_prepares_affordable_flight_before_deep_route() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    runner = CampaignRunner.__new__(CampaignRunner)
    runner.progress_callback = None
    runner._gear_catalog = None
    runner._source_world = world
    runner._selected_source_consumable_candidate = SimpleNamespace(
        mobile_vnum=4055,
        room_vnum=4064,
        requires_flight=True,
    )
    runner._selected_source_consumable_object_vnums = (4050,)
    runner._policy_without_learned_flight = (
        lambda _state: _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY
    )
    runner._catacombs_key_recovery_policy_if_ready = lambda _state: None
    runner.spec = SimpleNamespace(
        character=SimpleNamespace(character_class="warrior")
    )
    state = _level_39_healer_state()
    state.update(
        {
            "area": "Midgaard",
            "inventory": [[{"short_desc": "a big pot pie"}]],
            _SOURCE_REVISION_KEY: "test-source",
            "campaign_magic_shop_flight_price": 108,
            "campaign_magic_shop_flight_price_boot_id": "test-boot",
            "campaign_source_resource_reserves": {},
        }
    )

    selected = runner._policy_for_state(state)

    assert selected.policy_id == _BUY_FLIGHT_POLICY.policy_id
    assert selected.execution == "buy-flight"
    assert selected.minimum_flight_duration == 3
    assert state[_FLIGHT_FUNDING_REQUIRED_KEY] is True


def test_source_ranked_alternate_sanctuary_carrier_prepares_flight() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    runner = CampaignRunner.__new__(CampaignRunner)
    runner.progress_callback = None
    runner._gear_catalog = None
    runner._source_world = world
    runner._selected_source_consumable_candidate = SimpleNamespace(
        mobile_vnum=916,
        room_vnum=927,
        requires_flight=True,
    )
    runner._selected_source_consumable_object_vnums = (4050,)
    runner._policy_without_learned_flight = (
        lambda _state: _SOURCE_RANKED_SANCTUARY_ALTERNATE_POLICY
    )
    runner._catacombs_key_recovery_policy_if_ready = lambda _state: None
    runner.spec = SimpleNamespace(
        character=SimpleNamespace(character_class="warrior")
    )
    state = _level_39_healer_state()
    state.update(
        {
            "area": "Midgaard",
            "inventory": [[{"short_desc": "a big pot pie"}]],
            _SOURCE_REVISION_KEY: "test-source",
            "campaign_magic_shop_flight_price": 108,
            "campaign_magic_shop_flight_price_boot_id": "test-boot",
            "campaign_source_resource_reserves": {},
        }
    )

    selected = runner._policy_for_state(state)

    assert selected.policy_id == _BUY_FLIGHT_POLICY.policy_id
    assert selected.execution == "buy-flight"
    assert selected.minimum_flight_duration == 3
    assert state[_FLIGHT_FUNDING_REQUIRED_KEY] is True


def test_caerlin_reacquisition_handoff_reopens_after_pre_dispatch_return_home() -> None:
    state = _level_39_healer_state()
    state.update(
        {
            "campaign_source_revision": "test-source",
            "inventory": "[ { \"short_desc\": \"a leather jerkin\" } ]",
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "attempted",
                "retry_count": 0,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
                _CAERLIN_STAFF_RESERVE_REACQUISITION_KEY: True,
            },
        }
    )
    prior = dict(state[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY])
    segments = [
        {
            "phase": "return-home",
            "status": "success",
            "start_state_json": json.dumps(
                {_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: prior}
            ),
            "end_state_json": json.dumps(
                {
                    "world_boot_id": "test-boot",
                    "level": 39,
                    "fastwalk_route": None,
                    "campaign_source_resource_reserve": None,
                    "campaign_source_consumable_candidate": None,
                    "campaign_source_consumable_object_vnums": None,
                    "campaign_died_during_segment": False,
                    "xp_loss_observed": False,
                    "campaign_objective_kills": [],
                    "campaign_completed_kills": [],
                    "inventory": "[ { \"short_desc\": \"a leather jerkin\" } ]",
                }
            ),
        }
    ]

    assert _caerlin_staff_handoff_repair_allowed(state, segments)
    state[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY]["handoff_repair_consumed"] = True
    assert not _caerlin_staff_handoff_repair_allowed(state, segments)


def test_closed_caerlin_locator_miss_allows_one_source_map_revalidation() -> None:
    state = _level_39_healer_state()
    state.update(
        {
            "campaign_source_revision": "test-source",
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "closed",
                "outcome": "locator_retry_missed",
                "retry_count": 1,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
            },
        }
    )

    assert _caerlin_staff_locator_revalidation_allowed(state)
    state[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY][
        "locator_revalidation_revision"
    ] = 3
    assert not _caerlin_staff_locator_revalidation_allowed(state)


def test_caerlin_handoff_repair_only_reopens_a_non_caerlin_moria_dispatch() -> None:
    state = _level_39_healer_state()
    state.update(
        {
            "campaign_source_revision": "test-source",
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "attempted",
                "retry_count": 0,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
            },
        }
    )
    prior = dict(state[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY])
    segments = [
        {
            "phase": _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id,
            "start_state_json": json.dumps(
                {_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: prior}
            ),
            "end_state_json": json.dumps(
                {
                    "world_boot_id": "test-boot",
                    "level": 39,
                    "fastwalk_route": "moria",
                    "campaign_source_resource_reserve": None,
                    "campaign_source_consumable_candidate": None,
                    "campaign_source_consumable_object_vnums": None,
                }
            ),
        }
    ]

    assert _caerlin_staff_handoff_repair_allowed(state, segments)
    state[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY] = {
        **prior,
        "handoff_repair_consumed": True,
    }
    assert not _caerlin_staff_handoff_repair_allowed(state, segments)


def test_caerlin_handoff_repair_reopens_pre_dispatch_interruption() -> None:
    state = _level_39_healer_state()
    state.update(
        {
            "campaign_source_revision": "test-source",
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "attempted",
                "retry_count": 0,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
            },
        }
    )
    prior = dict(state[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY])
    segments = [
        {
            "phase": _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id,
            "status": "ready",
            "execution_status": "interrupted",
            "start_state_json": json.dumps(
                {_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: prior}
            ),
            "end_state_json": json.dumps(
                {
                    "world_boot_id": "test-boot",
                    "level": 39,
                    "room_vnum": "3001",
                    "fastwalk_route": None,
                    "campaign_source_consumable_candidate": None,
                    "campaign_source_consumable_object_vnums": None,
                }
            ),
        }
    ]

    assert _caerlin_staff_handoff_repair_allowed(state, segments)
