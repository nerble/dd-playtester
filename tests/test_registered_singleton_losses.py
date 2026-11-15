from types import SimpleNamespace

import pytest

import dd4tester.campaign as campaign
from dd4tester.campaign import _registered_research_xp_loss_policy_ids


def test_registered_alias_does_not_reprobe_a_closed_protected_target():
    state = {
        "level": 45, "world_boot_id": "boot",
        "campaign_source_ranked_xp_loss_policies": [{
            "policy_id": "source-ranked-hunt-mirror-realm-19034-19114-45",
            "level": 45, "boot_id": "boot", "loss_count": 1,
            "exact_stop_loss": True, "sanctuary_protected": True,
        }],
    }
    blocked = _registered_research_xp_loss_policy_ids(state)
    assert "mirror-realm-storn-probe-46-50" in blocked
    assert "mirror-realm-storn-hunt-46-50" in blocked
    assert "mirror-realm-master-dunn-probe-45-50" not in blocked
    state["level"] = 46
    assert "mirror-realm-storn-probe-46-50" not in _registered_research_xp_loss_policy_ids(state)
    state["level"] = 45
    state["campaign_source_ranked_xp_loss_policies"][0]["sanctuary_protected"] = False
    assert "mirror-realm-storn-probe-46-50" not in _registered_research_xp_loss_policy_ids(state)


@pytest.mark.parametrize("case,expected", [
    ("current", frozenset({19034})), ("prior-level", frozenset()),
    ("other-boot", frozenset()), ("unknown-policy", frozenset()),
    ("multi-target", frozenset()),
])
def test_registered_singleton_loss_is_shared_with_general_source_selection(monkeypatch, case, expected):
    loss = {"policy_id": "mirror-realm-storn-hunt-46-50", "level": 46, "boot_id": "boot"}
    state = {"level": 46, "world_boot_id": "boot",
             campaign._REGISTERED_RESEARCH_XP_LOSS_POLICIES_KEY: [loss]}
    if case == "prior-level":
        loss["level"] = 45
    elif case == "other-boot":
        loss["boot_id"] = "old"
    elif case == "unknown-policy":
        loss["policy_id"] = "not-registered"
    elif case == "multi-target":
        monkeypatch.setitem(campaign._POLICY_BY_ID, loss["policy_id"],
                            SimpleNamespace(source_mobile_vnums=(19034, 19028)))
    assert campaign._registered_singleton_loss_mobile_vnums(state) == expected
    assert state[campaign._REGISTERED_RESEARCH_XP_LOSS_POLICIES_KEY] == [loss]


def test_general_source_band_gate_rejects_named_loss_before_other_admission(monkeypatch):
    state = {"level": 46, "world_boot_id": "boot",
             campaign._REGISTERED_RESEARCH_XP_LOSS_POLICIES_KEY: [{
                 "policy_id": "mirror-realm-storn-hunt-46-50", "level": 46, "boot_id": "boot",
             }]}

    def reached_other_admission(*_a, **_kw):
        raise RuntimeError("independent candidate continues through ordinary gates")

    monkeypatch.setattr(campaign, "_source_ranked_plain_route_risk_fallback_allowed", reached_other_admission)
    kwargs = {"state": state, "world": object(), "character_level": 46,
              "allow_relative_level_target": True}
    assert campaign._source_ranked_candidate_in_current_band_uncached(
        SimpleNamespace(mobile_vnum=19034), **kwargs,
    ) is False
    with pytest.raises(RuntimeError, match="independent candidate"):
        campaign._source_ranked_candidate_in_current_band_uncached(
            SimpleNamespace(mobile_vnum=19028), **kwargs,
        )


def test_source_band_cache_tracks_replaced_registered_loss_ledger(monkeypatch):
    state = {"level": 46, "world_boot_id": "boot"}
    candidate = SimpleNamespace(mobile_vnum=19034)
    monkeypatch.setattr(campaign, "_source_ranked_candidate_in_current_band_uncached",
                        lambda candidate, state, **_kw:
                        candidate.mobile_vnum not in campaign._registered_singleton_loss_mobile_vnums(state))
    token = campaign._CAMPAIGN_SOURCE_GATE_CACHE.set({})
    try:
        assert campaign._source_ranked_candidate_in_current_band(candidate, state, character_level=46)
        state[campaign._REGISTERED_RESEARCH_XP_LOSS_POLICIES_KEY] = [{
            "policy_id": "mirror-realm-storn-hunt-46-50", "level": 46, "boot_id": "boot",
        }]
        assert not campaign._source_ranked_candidate_in_current_band(candidate, state, character_level=46)
    finally:
        campaign._CAMPAIGN_SOURCE_GATE_CACHE.reset(token)
