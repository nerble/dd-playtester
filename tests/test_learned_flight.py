from dataclasses import replace
import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import dd4tester.campaign as campaign
from dd4tester.character import CharacterSpec
from dd4tester.decisions import classify_decision
from dd4tester.flight import (
    FLIGHT_EVIDENCE_KEY, FlightPreparation, FlightSpell, flight_retry_pending,
    learned_flight_spell,
)
from dd4tester.observations import GameEvent
from dd4tester.starter import StarterPolicy
from dd4tester.state import CharacterState
from dd4tester.storage import RunStorage


@pytest.mark.parametrize("base,subclass,spell", [
    ("mage", None, "fly"), ("cleric", None, "fly"), ("mage", "none", "fly"),
    ("mage", "warlock", "fly"), ("psionic", None, "levitation"),
    ("psionic", "witch", "levitation"),
    ("brawler", "monk", "levitation"),
])
def test_source_authorized_class_paths(base, subclass, spell):
    assert learned_flight_spell(base, subclass, {spell: 48}) == FlightSpell(spell, 48)


@pytest.mark.parametrize("base,subclass,percent", [
    ("warrior", None, 48), ("thief", None, 48), ("shifter", None, 48),
    ("psionic", "witch", 48), ("mage", None, 0), ("mage", None, True),
    ("mage", None, "48"), ("mage", None, 101), ("mage", None, -1),
])
def test_observed_name_alone_is_not_cast_authorization(base, subclass, percent):
    assert learned_flight_spell(base, subclass, {"fly": percent}) is None


@pytest.mark.parametrize("percent,cost", [(1, 44), (30, 15), (48, 10), (100, 10)])
def test_source_nonoffensive_mana_formula(percent, cost):
    assert FlightSpell("fly", percent).mana_cost == cost


def advance(preparation, **changes):
    args = dict(active=False, affect_revision=1, mana=100, standing=True, now=1.0)
    args.update(changes)
    return preparation.next_command(FlightSpell("fly", 48), **args)


def test_fresh_affect_confirmation_not_success_text_authorizes_flight():
    preparation = FlightPreparation()
    assert advance(preparation) == "cast 'fly' self"
    preparation.observe("The sensation of gravity leaves your body.\n")
    assert advance(preparation, active=True) == "affects"
    assert preparation.status == "pending"
    assert advance(preparation, active=True, affect_revision=2) is None
    assert preparation.status == "confirmed" and preparation.attempts == 1


@pytest.mark.parametrize("failure", [
    "You lost your concentration.", "You lose your concentration.",
    "You fail to correctly recite the spell!",
])
def test_concentration_retries_are_bounded_and_use_current_mana(failure):
    preparation = FlightPreparation()
    for attempt in range(3):
        assert advance(preparation) == "cast 'fly' self"
        assert preparation.attempts == attempt + 1
        preparation.observe(failure[:12])
        preparation.observe(failure[12:] + "\n")
    assert advance(preparation) is None
    assert preparation.status == "unavailable" and preparation.attempts == 3
    assert advance(preparation) is None


@pytest.mark.parametrize("boundary", ["mana", "deadline", "refused", "no-affect", "stand"])
def test_preparation_stops_at_resource_and_acknowledgement_boundaries(boundary):
    preparation = FlightPreparation()
    if boundary == "stand":
        assert advance(preparation, standing=False) == "stand"
        assert advance(preparation, standing=False) is None
    else:
        assert advance(preparation) == "cast 'fly' self"
        if boundary == "mana":
            preparation.observe("You lost your concentration.\n")
            advance(preparation, mana=9)
        elif boundary == "deadline":
            advance(preparation, now=32)
        elif boundary == "refused":
            preparation.observe("You don't know any spells of that name.\n")
        else:
            assert advance(preparation) == "affects"
            advance(preparation, affect_revision=2)
    assert preparation.status == "unavailable"


def mage_spec():
    return CharacterSpec.from_mapping({
        "name": "Testmage", "race": "human", "gender": "female", "class": "mage",
    })


def healer():
    return CharacterState(
        level=18, xp=161052, hp=218, max_hp=218, mana=628, max_mana=628,
        move=320, max_move=320, room_vnum="3054", position=7, affects=[], enemies=[],
        inventory=[[{"short_desc": "a big pot pie"}]],
    )


def test_policy_casts_at_healer_and_records_live_confirmation():
    policy = StarterPolicy(mage_spec(), "fixture-password", prepare_learned_flight=True,
                           known_skills=("fly",), known_skill_levels={"fly": 48})
    policy.world_boot_id = "boot"
    state = healer()
    decision = policy._learned_flight_decision(state)
    assert decision.command == "cast 'fly' self"
    event = GameEvent("affects_changed", "gmcp", {"value": [[{"name": "fly", "duration": 21}]]})
    state.apply(event)
    policy.observe_events([event], state)
    assert policy._learned_flight_decision(state) is None
    evidence = policy.learned_flight_checkpoint(state)
    assert evidence["status"] == "confirmed" and evidence["attempts"] == 1
    assert evidence["boot_id"] == "boot" and evidence["level"] == 18
    assert policy._is_noncombat_utility_run


@pytest.mark.parametrize("boundary", ["combat", "runtime", "unknown-spell", "sleeping"])
def test_live_policy_preparation_boundaries(boundary):
    policy = StarterPolicy(mage_spec(), "fixture-password", prepare_learned_flight=True,
                           known_skill_levels={"fly": 48})
    state = healer()
    if boundary == "combat":
        state.position = 6
    elif boundary == "runtime":
        policy.runtime_boundary_requested = True
    elif boundary == "unknown-spell":
        policy.known_skill_levels.clear()
    else:
        state.position = 4
    decision = policy._learned_flight_decision(state)
    if boundary == "sleeping":
        assert decision.command == "stand"
    else:
        assert decision is None and policy.learned_flight_preparation.status == "unavailable"


def campaign_fixture(monkeypatch, selected=None):
    spec = campaign.CampaignSpec("test", Path("character.yaml"), mage_spec())
    runner = campaign.CampaignRunner(spec, Path("campaign.yaml"))
    selected = selected or campaign._PROVISION_FUNDING_POLICY
    monkeypatch.setattr(runner, "_policy_without_learned_flight", lambda state: selected)
    state = healer().to_dict()
    state.update(world_boot_id="boot", campaign_known_skill_levels={"fly": 48},
                 campaign_flight_funding_retry_pending=True)
    return runner, state, selected


def test_healer_spell_preempts_existing_potion_funding_without_claiming_flight(monkeypatch):
    runner, state, _ = campaign_fixture(monkeypatch)
    selected = runner._policy_for_state(state)
    assert selected.execution == "cast-flight"
    assert state["affects"] == [] and state[campaign._FLIGHT_FUNDING_RETRY_KEY]
    assert FLIGHT_EVIDENCE_KEY not in state  # inspection must not consume a retry


@pytest.mark.parametrize("boundary", [
    "food", "provision-funding", "off-site", "recovery", "unknown-affects",
    "already-flying", "untrained", "low-mana", "unknown-boot",
])
def test_preparation_handoff_preserves_other_gates(monkeypatch, boundary):
    runner, state, selected = campaign_fixture(monkeypatch)
    changes = {
        "food": {"inventory": []}, "provision-funding": {campaign._PROVISION_FUNDING_REQUIRED_KEY: True},
        "off-site": {"room_vnum": "3001"}, "recovery": {"hp": 20},
        "unknown-affects": {"affects": None},
        "already-flying": {"affects": [[{"name": "fly", "duration": 10}]]},
        "untrained": {"campaign_known_skill_levels": {}}, "low-mana": {"mana": 1},
        "unknown-boot": {"world_boot_id": None},
    }
    state.update(changes[boundary])
    assert runner._policy_for_state(state) == selected


def test_failure_cooldown_survives_checkpoints_and_expires(monkeypatch):
    runner, state, selected = campaign_fixture(monkeypatch)
    now = datetime.now(timezone.utc)
    marker = {"spell": "fly", "proficiency": 48, "level": 18, "boot_id": "boot",
              "status": "pending", "attempted_at": now.isoformat()}
    state[FLIGHT_EVIDENCE_KEY] = marker
    assert runner._policy_for_state(state) == selected
    merged = campaign._campaign_segment_end_state(state, healer().to_dict(), execution="return-home")
    assert merged[FLIGHT_EVIDENCE_KEY] == marker
    assert not flight_retry_pending(marker, spell=FlightSpell("fly", 48), boot_id="boot",
                                    level=18, now=now + timedelta(seconds=601))
    assert not flight_retry_pending(marker, spell=FlightSpell("fly", 49), boot_id="boot", level=18)
    assert not flight_retry_pending(marker, spell=FlightSpell("fly", 48), boot_id="new-boot", level=18)


@pytest.mark.parametrize("confirmed,active", [(True, True), (False, True), (True, False), (False, False)])
def test_only_confirmed_live_flight_clears_funding_not_shop_hazards(confirmed, active):
    state = healer().to_dict()
    state.update({campaign._FLIGHT_FUNDING_REQUIRED_KEY: True, campaign._FLIGHT_FUNDING_RETRY_KEY: True,
                  campaign._MAGIC_SHOP_ROUTE_BLOCKED_KEY: True,
                  campaign._PROVISION_FUNDING_REQUIRED_KEY: True,
                  FLIGHT_EVIDENCE_KEY: {"status": "confirmed" if confirmed else "unavailable"}})
    if active:
        state["affects"] = [[{"name": "fly", "duration": 21}]]
    result = campaign._apply_flight_funding_state_transition(state, state, execution="cast-flight", funding_completed=False)
    assert (campaign._FLIGHT_FUNDING_RETRY_KEY not in result) == (confirmed and active)
    assert result[campaign._MAGIC_SHOP_ROUTE_BLOCKED_KEY]
    assert result[campaign._PROVISION_FUNDING_REQUIRED_KEY]


def test_dispatch_passes_observed_skill_state_into_the_dedicated_runner(monkeypatch):
    captured = {}

    class FakeRunner:
        def __init__(self, character, path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return "fixture-result"

    monkeypatch.setattr(campaign, "StarterBotRunner", FakeRunner)
    state = {**healer().to_dict(), "campaign_known_skill_levels": {"fly": 48},
             "campaign_known_skills": ["fly"]}
    result = asyncio.run(campaign._run_policy_segment(
        mage_spec(), Path("profile.yaml"), campaign._CAST_FLIGHT_POLICY, current_state=state,
    ))
    assert result == "fixture-result"
    assert captured["prepare_learned_flight"]
    assert captured["known_skill_levels"]["fly"] == 48
    assert "magic_shop_research" not in captured


def test_preconnection_interruption_preserves_the_durable_attempt(tmp_path, monkeypatch):
    runner, state, _ = campaign_fixture(monkeypatch)
    spec = replace(runner.spec.character, database=tmp_path / "runs.sqlite3")
    runner.spec = replace(runner.spec, character=spec)

    class Interrupted(BaseException):
        pass

    async def interrupt_before_connect(*args):
        assert args[0].max_runtime == 60
        with RunStorage(spec.database) as reader:
            checkpoint = reader.get_latest_campaign_checkpoint(campaign_id)
            restored = json.loads(checkpoint["state_json"])
            assert restored[FLIGHT_EVIDENCE_KEY]["status"] == "pending"
            assert runner._policy_for_state(restored).execution != "cast-flight"
        raise Interrupted()

    runner.segment_runner = interrupt_before_connect
    with RunStorage(spec.database) as storage:
        campaign_id = storage.create_campaign(name="fixture", config_path=tmp_path / "campaign.yaml",
                                              character_profile_path=tmp_path / "character.yaml", target_level=100)
        with pytest.raises(Interrupted):
            asyncio.run(runner._run_starter(storage, campaign_id, state,
                                           {"command_count": 0, "duration_seconds": 0},
                                           campaign._CAST_FLIGHT_POLICY))


def test_new_flight_report_inherits_the_campaign_reboot_for_retry_scope(monkeypatch):
    runner, state, selected = campaign_fixture(monkeypatch)
    current = healer().to_dict()
    current[FLIGHT_EVIDENCE_KEY] = {
        "spell": "fly", "proficiency": 48, "level": 18, "boot_id": None,
        "status": "unavailable", "attempted_at": datetime.now(timezone.utc).isoformat(),
    }
    merged = campaign._campaign_segment_end_state(state, current, execution="cast-flight")
    assert merged[FLIGHT_EVIDENCE_KEY]["boot_id"] == "boot"
    assert runner._policy_for_state(merged) == selected


@pytest.mark.parametrize("spell", ["fly", "levitation"])
def test_self_flight_is_navigation_not_combat(spell):
    assert classify_decision(f"cast '{spell}' self", "prepare learned flight", "tutorial").category == "navigation"


def test_offensive_cast_keeps_its_combat_classification():
    assert classify_decision("cast 'burning hands' #42", "damage target", "field").category == "combat"
