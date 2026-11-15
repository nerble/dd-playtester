from dd4tester.campaign import (
    CampaignRunner, _state_has_full_staff_fight_reserve,
    _active_crowded_research_policy_id,
    _RESEARCH_CROWD_COOLDOWN_KEY,
)


def test_two_verified_carried_charges_suppress_optional_supply_detour():
    state = {
        "room_vnum": "3054", "level": 45,
        "inventory": [{"short_desc": "the Red DragonOrb", "quan": "1"}],
        "campaign_source_resource_reserves": {"sanctuary": {
            "mode": "staff", "object_description": "red dragonorb",
            "charges_remaining": 5, "object_vnum": 7303,
        }},
    }
    assert _state_has_full_staff_fight_reserve(state)
    state["campaign_source_resource_reserves"]["sanctuary"]["charges_remaining"] = 1
    assert not _state_has_full_staff_fight_reserve(state)
    state["campaign_source_resource_reserves"]["sanctuary"]["charges_remaining"] = 5
    state["inventory"] = []
    assert not _state_has_full_staff_fight_reserve(state)


def test_optional_topup_returns_before_source_search_with_full_fight_reserve(monkeypatch):
    import dd4tester.campaign as campaign

    runner = object.__new__(CampaignRunner)
    runner._source_world = object()
    runner._gear_catalog = None
    monkeypatch.setattr(campaign, "_is_safe_healer_checkpoint", lambda state: True)
    monkeypatch.setattr(campaign, "_has_campaign_food", lambda state, **kwargs: True)
    monkeypatch.setattr(campaign, "_state_has_sanctuary_reserve", lambda state: True)
    monkeypatch.setattr(campaign, "_state_has_full_staff_fight_reserve", lambda state: True)
    assert runner._select_olympus_sanctuary_fallback(
        {}, practice_skill=None, allow_existing_reserve=True,
    ) is None


def test_optional_carrier_crowd_does_not_wait_with_two_staff_charges():
    policy_id = "source-ranked-hunt-olympus-916-927-45-sanctuary-maintenance"
    state = {
        "level": 45, "world_boot_id": "boot",
        "inventory": [{"short_desc": "the Red DragonOrb", "quan": "1"}],
        "campaign_source_resource_reserves": {"sanctuary": {
            "mode": "staff", "object_description": "red dragonorb",
            "charges_remaining": 5,
        }},
        "campaign_research_results": {policy_id: {"boot_id": "boot", "crowded": True}},
        _RESEARCH_CROWD_COOLDOWN_KEY: {policy_id: 3},
    }
    assert _active_crowded_research_policy_id(state) is None
    assert state["campaign_research_results"][policy_id]["crowded"] is True
    state["campaign_source_resource_reserves"]["sanctuary"]["charges_remaining"] = 1
    assert _active_crowded_research_policy_id(state) == policy_id
    state["campaign_research_results"]["unrelated-hunt"] = {"boot_id": "boot", "crowded": True}
    state[_RESEARCH_CROWD_COOLDOWN_KEY]["unrelated-hunt"] = 2
    state["campaign_source_resource_reserves"]["sanctuary"]["charges_remaining"] = 5
    assert _active_crowded_research_policy_id(state) == "unrelated-hunt"
