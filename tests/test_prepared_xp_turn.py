from types import SimpleNamespace
from dataclasses import replace

import pytest

import dd4tester.campaign as campaign


@pytest.mark.parametrize("streak,productive,expects_gear", [
    (0, True, False), (0, False, True), (1, True, True), (2, True, True),
])
def test_stale_primary_does_not_interrupt_fresh_productive_hunt(monkeypatch, streak, productive, expects_gear):
    runner = campaign.CampaignRunner.__new__(campaign.CampaignRunner)
    hunt = replace(campaign._SOURCE_RANKED_HUNT_POLICY,
                   policy_id="source-ranked-hunt-test-100-200-46")
    runner._policy_for_state_without_bank_reserve = lambda *_a, **_kw: hunt
    runner._source_gear_primary_is_stale = lambda _: True
    runner._source_ranked_no_progress_streak = streak
    runner._emit_progress = lambda _: None
    chosen = []

    def gear(state):
        chosen.append(state)
        return SimpleNamespace(source_kind="ground-reset")

    runner._select_source_gear_placement = gear
    monkeypatch.setattr(campaign, "_current_level_progression_loss_count", lambda *_a, **_kw: 2)
    monkeypatch.setattr(campaign, "_state_productive_policy_ids",
                        lambda _: frozenset({hunt.policy_id}) if productive else frozenset())
    monkeypatch.setattr(campaign, "_source_gear_upgrade_waiting_for_xp_trip", lambda *_a, **_kw: False)
    monkeypatch.setattr(campaign, "_source_protection_waiting_for_xp_trip", lambda *_a, **_kw: False)
    state = {
        "level": 46, "world_boot_id": "boot", "room_vnum": "3054",
        "area": "Midgaard", "room_flags": ["safe", "healing"],
        "hp": 1000, "max_hp": 1000, "mana": 600, "max_mana": 600,
        "move": 600, "max_move": 600, "quest_status": {"active": 0, "total_points": 18},
    }
    result = runner._policy_for_state(state)
    assert bool(chosen) is expects_gear
    assert result.policy_id == (campaign._SOURCE_GEAR_ACQUISITION_POLICY.policy_id if expects_gear else hunt.policy_id)


def prepared_state():
    return {
        "level": 46, "world_boot_id": "boot-1",
        "inventory": [[{"short_desc": "nectar"}]],
        campaign._SOURCE_RESOURCE_RESERVES_KEY: {"sanctuary": {
            "object_description": "nectar", "mode": "pill", "charges_remaining": 1,
        }},
        campaign._SANCTUARY_CARRIER_ACQUISITIONS_KEY: [{
            "level": 46, "boot_id": "boot-1", "acquisition_segment_id": 100,
            "required_object_acquired": True,
        }],
    }


@pytest.mark.parametrize("visit,waiting", [
    ("none", True), ("sale", True), ("maintenance", True), ("running", True),
    ("empty", True), ("missing_summary", True), ("route_only", True),
    ("fight", False), ("loss", False), ("kill", False),
])
def test_protection_pickup_keeps_its_real_xp_turn(visit, waiting):
    state = prepared_state()
    phase = {
        "sale": "liquidate-loot",
        "maintenance": "source-ranked-sanctuary-olympus-hephaestus-38-100",
    }.get(visit, "source-ranked-hunt-test-1-100-46")
    rows = [] if visit == "none" else [{
        "id": 101, "run_id": 201, "phase": phase,
        "status": "running" if visit == "running" else "success",
        "finished_at": None if visit == "running" else "2026-11-15T01:00:00+00:00",
    }]
    summary = None if visit == "missing_summary" else {
        "outcomes": {"safety": "loss" if visit == "loss" else "safe"},
        "progress": {
            "combat_starts": 1 if visit in {"fight", "route_only"} else 0,
            "confirmed_kills": ([{
                "xp_gained": 5000, "objective_eligible": visit == "kill",
                "source_policy_id": phase,
            }] if visit in {"kill", "route_only"} else []),
        },
    }
    assert campaign._source_protection_waiting_for_xp_trip(
        state, rows, storage=SimpleNamespace(get_run_summary=lambda _: summary),
    ) is waiting


def test_an_older_hunt_cannot_spend_a_newer_protection_pickup():
    row = {"id": 99, "run_id": 200, "phase": "source-ranked-hunt-test-1-100-46",
           "status": "success", "finished_at": "2026-11-15T01:00:00+00:00"}
    assert campaign._source_protection_waiting_for_xp_trip(prepared_state(), [row])


def test_unusable_or_unconfirmed_protection_does_not_hold_gear_repair():
    state = prepared_state()
    state[campaign._SOURCE_RESOURCE_RESERVES_KEY]["sanctuary"]["activation_usable"] = False
    assert not campaign._source_protection_waiting_for_xp_trip(state, [])
    state = prepared_state()
    state[campaign._SANCTUARY_CARRIER_ACQUISITIONS_KEY][0]["required_object_acquired"] = False
    assert not campaign._source_protection_waiting_for_xp_trip(state, [])


@pytest.mark.parametrize("blocker", [
    None, "gear_turn", "protection_turn", "quest", "qp", "wounded", "field", "combat",
])
def test_post_loss_gear_repair_can_precede_supply_without_bypassing_handoffs(monkeypatch, blocker):
    runner = campaign.CampaignRunner.__new__(campaign.CampaignRunner)
    supply = campaign._SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY
    runner._policy_for_state_without_bank_reserve = lambda *_a, **_kw: supply
    runner._source_gear_primary_is_stale = lambda _: False
    runner._source_ranked_no_progress_streak = 2
    runner._emit_progress = lambda _: None
    selected = []

    def choose_gear(state):
        selected.append(state)
        return SimpleNamespace(source_kind="ground-reset")

    runner._select_source_gear_placement = choose_gear
    monkeypatch.setattr(campaign, "_current_level_progression_loss_count", lambda *_a, **_kw: 2)
    monkeypatch.setattr(campaign, "_source_gear_upgrade_waiting_for_xp_trip",
                        lambda *_a, **_kw: blocker == "gear_turn")
    monkeypatch.setattr(campaign, "_source_protection_waiting_for_xp_trip",
                        lambda *_a, **_kw: blocker == "protection_turn")
    state = {
        "level": 46, "world_boot_id": "boot", "room_vnum": "3054",
        "area": "Midgaard", "room_flags": ["safe", "healing"],
        "hp": 1000, "max_hp": 1000, "mana": 600, "max_mana": 600,
        "move": 600, "max_move": 600,
        "quest_status": {"active": 0, "total_points": 18},
        campaign._PROTECTION_RECOVERY_KEY: {"boot_id": "boot", "level": 46},
    }
    if blocker == "quest":
        state["quest_status"]["active"] = 1
    elif blocker == "qp":
        state["quest_status"]["total_points"] = 0
    elif blocker == "wounded":
        state["hp"] = 400
    elif blocker == "field":
        state["room_vnum"] = "1573"
    elif blocker == "combat":
        state["in_combat"] = True
    result = runner._policy_for_state(state)
    assert bool(selected) is (blocker is None)
    assert result.execution == ("source-gear-acquisition" if blocker is None else supply.execution)


@pytest.mark.parametrize("reserve,gear_available,already_selected,expected", [
    (False, False, False, "source-ranked-hunt"),
    (True, False, False, "source-ranked-hunt"),
    (False, True, False, "source-gear-acquisition"),
    (False, False, True, "moria-sanctuary-hunt"),
])
def test_post_loss_gear_check_keeps_the_existing_hunt_or_supply_owner(
    monkeypatch, reserve, gear_available, already_selected, expected,
):
    runner = campaign.CampaignRunner.__new__(campaign.CampaignRunner)
    runner._source_world = SimpleNamespace()
    runner._policy_for_state_without_bank_reserve = lambda *_a, **_kw: (
        campaign._SOURCE_RANKED_SANCTUARY_ALTERNATE_POLICY
        if already_selected else campaign._SOURCE_RANKED_HUNT_POLICY
    )
    runner._compare_source_hunt_before_gear = lambda _s, policy: policy
    runner._source_gear_primary_is_stale = lambda _: False
    runner._source_ranked_no_progress_streak = 2
    runner._emit_progress = lambda _: None
    runner._select_source_gear_placement = lambda _: object() if gear_available else None
    visits = []

    def supply(state, **_kwargs):
        visits.append(state)
        return campaign._SOURCE_RANKED_SANCTUARY_ALTERNATE_POLICY

    runner._select_olympus_sanctuary_fallback = supply
    monkeypatch.setattr(campaign, "_current_level_progression_loss_count", lambda *_a, **_kw: 2)
    monkeypatch.setattr(campaign, "_source_gear_upgrade_waiting_for_xp_trip", lambda *_a, **_kw: False)
    monkeypatch.setattr(campaign, "_source_protection_waiting_for_xp_trip", lambda *_a, **_kw: False)
    monkeypatch.setattr(campaign, "_state_has_sanctuary_reserve", lambda _: reserve)
    state = {
        "level": 46, "room_vnum": "3054", "room_flags": ["safe", "healing"],
        "hp": 1000, "max_hp": 1000, "mana": 600, "max_mana": 600,
        "move": 600, "max_move": 600, "quest_status": {"active": 0, "total_points": 18},
    }
    assert runner._policy_for_state(state).execution == expected
    assert not visits


def test_legacy_missing_pouch_recheck_cannot_be_skipped_by_an_early_hunt(monkeypatch):
    runner = campaign.CampaignRunner.__new__(campaign.CampaignRunner)
    runner._policy_for_state_without_bank_reserve = lambda *_a, **_kw: campaign._SOURCE_RANKED_HUNT_POLICY
    runner._emit_progress = lambda _: None
    runner._selected_source_ranked_circuit = ("old-stop",)
    state = {
        "level": 46, "room_vnum": "3054", "room_flags": ["safe", "healing"],
        "hp": 1000, "max_hp": 1000, "mana": 600, "max_mana": 600,
        "move": 600, "max_move": 600, "quest_status": {"active": 0, "total_points": 18},
        "campaign_empty_equipment_categories": ["pouch"],
        "campaign_city_outfit": {"complete": True, "room_vnum": "3054", "quotes": [
            {"category": "pouch", "outcome": "no-legal-offer"},
        ]},
    }
    result = runner._policy_for_state(state)
    assert result.execution == "outfit-basic-gear"
    assert runner._selected_source_ranked_circuit == ()
