import pytest

import dd4tester.campaign as campaign


@pytest.mark.parametrize("signature,saved_hints,current_hints,expected", [
    (["elite sword"], None, {"elite sword": 30232}, False),
    ([], {"branch": 6104}, {"branch": 6104}, False),
    ([], {"branch": 6103}, {"branch": 6104}, True),
    ([], None, {"branch": 6104}, True),
])
def test_repeated_capacity_suggestion_does_not_override_completed_retention(
    monkeypatch, signature, saved_hints, current_hints, expected,
):
    retained = {"signature": signature, "retention_only": True, "retention_policy_revision": 2}
    if saved_hints is not None:
        retained["inventory_source_hints"] = saved_hints
    state = {campaign._LIQUIDATION_RETENTION_KEY: retained,
             campaign._CAMPAIGN_INVENTORY_SOURCE_HINTS_KEY: current_hints}
    keyword = "sword" if signature else "branch"
    monkeypatch.setattr(campaign, "_campaign_capacity_relief_inventory_keyword", lambda *a, **kw: keyword)
    monkeypatch.setattr(campaign, "_liquidation_retention_matches", lambda *a, **kw: True)
    monkeypatch.setattr(campaign, "_matches_liquidation_baseline", lambda *a, **kw: True)
    monkeypatch.setattr(campaign, "_has_campaign_sellable_loot", lambda *a, **kw: False)
    monkeypatch.setattr(campaign, "_campaign_liquidation_descriptions", lambda *a, **kw: ())
    assert campaign._campaign_should_liquidate_loot(state, force=True) is expected


def test_retention_receipt_copies_source_hints():
    hints = {"branch": 6104}
    receipt = campaign._liquidation_retention_receipt(
        run_id=7, segment_id=20, signature=(), inventory_source_hints=hints,
    )
    hints["branch"] = 6103
    assert receipt["inventory_source_hints"] == {"branch": 6104}
