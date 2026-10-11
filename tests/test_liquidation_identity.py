from dd4tester.campaign import _has_campaign_sellable_loot, _matches_liquidation_baseline
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
