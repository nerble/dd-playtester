from types import SimpleNamespace

import pytest

import dd4tester.campaign as campaign
from dd4tester.hunt_candidates import WorldSource


@pytest.mark.parametrize("loss", [False, True])
def test_audited_low_moria_carrier_precedes_harder_fixed_fallbacks(monkeypatch, loss):
    runner = campaign.CampaignRunner.__new__(campaign.CampaignRunner)
    runner._source_world = WorldSource()
    runner._gear_catalog = None
    runner._emit_progress = lambda _: None
    candidate = SimpleNamespace(
        area_file="moria.are", mobile_vnum=4055, room_vnum=4064,
        target="the large hobgoblin",
    )
    monkeypatch.setattr(campaign, "_is_safe_healer_checkpoint", lambda _: True)
    monkeypatch.setattr(campaign, "_has_campaign_food", lambda *a, **kw: True)
    monkeypatch.setattr(campaign, "_state_has_sanctuary_reserve", lambda _: False)
    monkeypatch.setattr(campaign, "_source_ranked_proven_sanctuary_replenishment", lambda *a, **kw: None)
    monkeypatch.setattr(campaign, "_select_preferred_moria_sanctuary_recovery_candidate",
                        lambda *a, **kw: (candidate, (4050,)))
    monkeypatch.setattr(campaign, "_source_ranked_xp_loss_for_stop",
                        lambda *a, **kw: {"exact_stop_loss": True} if loss else None)
    monkeypatch.setattr(campaign, "_source_ranked_sanctuary_candidate_research_open", lambda *a, **kw: True)
    # This legacy aggregate cannot hide a fresh independent eligible carrier;
    # an exact loss still closes that carrier before reaching it.
    monkeypatch.setattr(campaign, "_source_ranked_terminal_sanctuary_failure", lambda _: True)
    state = {"level": 46, "world_boot_id": "boot-1"}
    result = runner._select_olympus_sanctuary_fallback(state, practice_skill=None)
    if loss:
        assert result is None
    else:
        assert result.policy_id == "source-ranked-hunt-moria-4055-4064-46-sanctuary-maintenance"
        assert runner._selected_source_consumable_candidate is candidate
        assert runner._selected_source_consumable_object_vnums == (4050,)
