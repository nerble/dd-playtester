from dd4tester.campaign import (
    _campaign_should_liquidate_loot,
    _has_campaign_sellable_loot,
    _liquidation_retention_matches,
    _liquidation_retention_receipt,
    _matches_liquidation_baseline,
)
from dd4tester.character import CharacterSpec
from dd4tester.starter import StarterPolicy
from dd4tester.state import CharacterState


def test_unchanged_carried_signature_is_not_reduced_by_worn_namesake(monkeypatch):
    state = {
        "campaign_liquidation_baseline": ["hammer", "i.q. vine"],
        "campaign_worn_equipment": ["an I.Q. Vine"],
    }
    monkeypatch.setattr("dd4tester.campaign._campaign_liquidation_signature",
                        lambda *_args, **_kwargs: ("hammer", "i.q. vine"))
    assert _matches_liquidation_baseline(state)
    assert not _has_campaign_sellable_loot(state)


def test_actual_inventory_to_worn_transition_still_matches_baseline(monkeypatch):
    state = {
        "campaign_liquidation_baseline": ["hammer", "i.q. vine"],
        "campaign_worn_equipment": ["an I.Q. Vine"],
    }
    monkeypatch.setattr("dd4tester.campaign._campaign_liquidation_signature",
                        lambda *_args, **_kwargs: ("hammer",))
    assert _matches_liquidation_baseline(state)


def test_changed_carried_signature_reopens_sale_check(monkeypatch):
    state = {
        "campaign_liquidation_baseline": ["hammer", "i.q. vine"],
        "campaign_worn_equipment": ["an I.Q. Vine"],
    }
    monkeypatch.setattr("dd4tester.campaign._campaign_liquidation_signature",
                        lambda *_args, **_kwargs: ("hammer", "i.q. vine", "metal shield"))
    assert not _matches_liquidation_baseline(state)


def _finished_sale_policy():
    spec = CharacterSpec.from_mapping({
        "name": "SaleTest", "race": "dwarf", "gender": "female",
        "class": "warrior", "subclass": None, "title": "",
    })
    policy = StarterPolicy(spec, "test-password", liquidate_loot=True)
    policy.done = True
    policy.sale_phase = "outbound"
    policy.sale_origin_room = "3054"
    return policy


def test_completed_empty_plan_records_retention_not_profit():
    receipt = _finished_sale_policy().liquidation_checkpoint(CharacterState(room_vnum="3054"))
    assert receipt["complete"] and receipt["retention_only"]
    assert receipt["confirmed_sales"] == 0
    assert receipt["retention_policy_revision"] == 2


def test_old_retention_receipt_reopens_after_sale_policy_change(monkeypatch):
    state = {
        "campaign_liquidation_retention": {
            "retention_only": True,
            "signature": ["bishop piece"],
            "run_id": 1,
        },
    }
    monkeypatch.setattr(
        "dd4tester.campaign._campaign_liquidation_signature",
        lambda *_args, **_kwargs: ("bishop piece",),
    )
    assert not _liquidation_retention_matches(state)
    state["campaign_liquidation_retention"]["retention_policy_revision"] = 2
    assert _liquidation_retention_matches(state)


def test_versioned_retention_receipt_suppresses_unchanged_no_sale(monkeypatch):
    state = {
        "inventory": [[{"short_desc": "a staff of the bard"}]],
    }
    monkeypatch.setattr(
        "dd4tester.campaign._campaign_liquidation_signature",
        lambda *_args, **_kwargs: ("staff of the bard",),
    )
    state["campaign_liquidation_retention"] = _liquidation_retention_receipt(
        run_id=7,
        segment_id=9,
        signature=("staff of the bard",),
    )

    assert state["campaign_liquidation_retention"][
        "retention_policy_revision"
    ] == 2
    assert _liquidation_retention_matches(state)
    assert not _has_campaign_sellable_loot(state)
    assert _campaign_should_liquidate_loot(state, force=True) is False


def test_retention_receipt_allows_source_planner_to_drop_old_candidate(monkeypatch):
    state = {
        "inventory": [[
            {"short_desc": "a mithril helm"},
            {"short_desc": "a pair of mithril gauntlets"},
        ]],
        "campaign_liquidation_retention": _liquidation_retention_receipt(
            run_id=7,
            segment_id=9,
            signature=("mithril helm", "pair of mithril gauntlets"),
        ),
    }
    monkeypatch.setattr(
        "dd4tester.campaign._campaign_liquidation_signature",
        lambda *_args, **_kwargs: ("pair of mithril gauntlets",),
    )

    assert _liquidation_retention_matches(state)
    assert not _has_campaign_sellable_loot(state)


def test_interrupted_plan_cannot_close_retained_inventory():
    policy = _finished_sale_policy()
    state = CharacterState(room_vnum="3054")
    policy.runtime_boundary_requested = True
    assert not policy.liquidation_checkpoint(state)["complete"]
    policy.runtime_boundary_requested = False
    policy.sale_phase = "plan"
    assert not policy.liquidation_checkpoint(state)["complete"]
    policy.sale_phase = "outbound"
    policy.donation_pending_keyword = "flask"
    assert not policy.liquidation_checkpoint(state)["complete"]
    policy.donation_pending_keyword = None
    policy.sale_rejections = [{"reason": "refused"}]
    assert not policy.liquidation_checkpoint(state)["complete"]
