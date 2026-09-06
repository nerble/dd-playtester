import pytest

from dd4tester.autonomy import audit_hero_request, audit_json, render_autonomy_audit


def test_audit_separates_executable_research_from_verified_proof() -> None:
    audit = audit_hero_request(
        race="Human",
        sex="female",
        character_class="warrior",
        target_level=20,
    )

    assert audit.identity_legal
    assert audit.registered_through_target
    assert not audit.templates_marked_verified_through_target
    assert audit.first_proof_gap_level == 10
    assert audit.first_proof_gap_policy == "fleshmonger-guard-probe-10-12"
    assert audit.policy_bands[0].policy_id == "starter-0-2"
    assert any(
        "research policy fleshmonger-guard-probe-10-12" in blocker
        for blocker in audit.blockers
    )


def test_audit_models_subclass_handoff_and_post_handoff_identity() -> None:
    audit = audit_hero_request(
        race="human",
        sex="male",
        character_class="warrior",
        subclass="knight",
        target_level=31,
    )

    bands = {band.policy_id: band for band in audit.policy_bands}
    assert audit.subclass == "knight"
    assert bands["choose-subclass-30"].status == "research"
    assert bands["minotaur-gatekeeper-probe-31-35"].minimum_level == 31
    assert any("knight teacher handoff" in blocker for blocker in audit.blockers)


def test_audit_rejects_cross_class_subclass() -> None:
    with pytest.raises(ValueError, match="requires base class 'warrior'"):
        audit_hero_request(
            race="human",
            sex="female",
            character_class="mage",
            subclass="knight",
        )


def test_audit_renderers_are_operator_and_ci_friendly() -> None:
    audit = audit_hero_request(
        race="human",
        sex="female",
        character_class="thief",
        target_level=12,
    )

    rendered = render_autonomy_audit(audit)
    payload = audit_json(audit)
    assert "Template coverage: registered through target" in rendered
    assert "First unverified template: level 10" in rendered
    assert '"live_progression_assessed": false' in payload
    assert payload.endswith("\n")


def test_verified_starter_templates_do_not_claim_live_progression_proof() -> None:
    audit = audit_hero_request(
        race="human", sex="female", character_class="mage", target_level=2,
    )

    assert audit.templates_marked_verified_through_target
    assert audit.to_mapping()["audit_scope"] == "static_templates"
    assert audit.to_mapping()["live_progression_assessed"] is False
    assert "Live progression proof: not assessed" in render_autonomy_audit(audit)
    assert "proven_through_target" not in audit.to_mapping()


def test_audit_surfaces_declared_class_automation_gaps() -> None:
    audit = audit_hero_request(
        race="human",
        sex="female",
        character_class="shifter",
        target_level=100,
    )

    assert audit.combat_automation_status == "partial"
    assert any("form controller" in gap for gap in audit.automation_gaps)
    payload = audit.to_mapping()
    assert payload["training"]["combat_automation_status"] == "partial"
    assert "Automation gaps:" in render_autonomy_audit(audit)


def test_psionic_agitation_is_reported_as_automated_after_runtime_wiring() -> None:
    audit = audit_hero_request(
        race="human",
        sex="female",
        character_class="psionic",
        target_level=30,
    )

    assert "agitation" in audit.automated_combat_skills


def test_subclass_audit_combines_base_and_subclass_automation_gaps() -> None:
    audit = audit_hero_request(
        race="human",
        sex="male",
        character_class="shifter",
        subclass="werewolf",
        target_level=100,
    )

    assert any(gap.startswith("werewolf:") for gap in audit.automation_gaps)
    assert any(gap.startswith("shifter:") for gap in audit.automation_gaps)
