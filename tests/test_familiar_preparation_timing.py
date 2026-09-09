from dataclasses import replace

import pytest

from dd4tester import campaign
from dd4tester.companions import FamiliarPreparation
from dd4tester.state import CharacterState
from test_companions import LISTING, NORMALIZED, SUMMONED, outdoor_fixture, policy_fixture


TICK = "\nThe sun slowly disappears in the west.\n<113/113 hits 324/324 mana 167/220 move [Moria]> "


@pytest.fixture
def clock(monkeypatch):
    value = [0.0]
    monkeypatch.setattr("dd4tester.companions.time.monotonic", lambda: value[0])
    return value


def test_run_12815_world_tick_does_not_fail_or_repeat_a_pending_summon(clock):
    policy = policy_fixture()
    state = CharacterState(level=8, room_vnum="2", position=7, hp=113, max_hp=113,
                           mana=324, max_mana=324, move=151, max_move=220,
                           sector="hills", room_flags=["no_mob"])
    assert policy._fastwalk_research_decision(state).command == "cast 'summon familiar'"
    # Real events 8019852, 8019854, 8019865: a tick precedes the cast reply.
    clock[0] = 0.25
    policy.observe_text(TICK)
    assert policy._fastwalk_research_decision(state) is None
    assert policy.familiar_preparation.failure is None
    assert policy.familiar_preparation.attempts == 1
    assert policy.fastwalk_outbound_index == 0 and not policy.fastwalk_returning
    clock[0] = 1.11
    policy.observe_text(SUMMONED)
    assert policy._fastwalk_research_decision(replace(state, mana=224)).command == "look"
    policy.observe_text(LISTING)
    policy.room_target_selector_descriptions["2"] = {"#42": NORMALIZED}
    assert policy._fastwalk_research_decision(state).command == "group #42"
    policy.observe_text(TICK)
    assert policy._fastwalk_research_decision(state) is None
    assert not policy.familiar_active
    policy.observe_text("The pony joins your group.\n")
    assert policy._familiar_staging_decision(state) is None
    assert policy.familiar_active and policy.familiar_preparation.attempts == 1


def test_outdoor_pending_summon_waits_instead_of_recalling_or_attacking(clock):
    policy, state = outdoor_fixture()
    policy.fastwalk_attack_target = policy.consider_target = "orc"
    assert policy._consider_fastwalk_target(state).command == "cast 'summon familiar'"
    policy.observe_text(TICK)
    assert policy._consider_fastwalk_target(state) is None
    assert policy.familiar_preparation.pending and not policy.fastwalk_returning
    assert not policy.fastwalk_attack_started


@pytest.mark.parametrize("stage", ["summoning", "identifying", "grouping"])
def test_preparation_silence_expires_without_a_new_prompt_or_retry(clock, stage):
    policy = policy_fixture()
    policy.login_authenticated = True
    policy.familiar_preparation = FamiliarPreparation(stage=stage, attempts=1, deadline=30)
    policy.prompt_ready = False
    state = CharacterState(level=8, room_vnum="2", position=7, hp=113, max_hp=113,
                           mana=324, sector="hills", room_flags=["no_mob"])
    clock[0] = 30
    policy.next_decision(state)
    assert policy.familiar_preparation.failure
    assert policy.prompt_ready
    decision = policy._familiar_staging_decision(state)
    assert decision.command == "recall"
    assert policy.familiar_preparation.attempts == 1


@pytest.mark.parametrize("reply", [SUMMONED, "The pony joins your group.\n"])
def test_late_preparation_acknowledgement_cannot_restore_ownership(clock, reply):
    prep = FamiliarPreparation(stage="summoning" if reply == SUMMONED else "grouping",
                               deadline=30, attempts=1)
    clock[0] = 30
    prep.observe(reply)
    assert prep.failure and not prep.summoned and not prep.grouped
    assert prep.next_command({"#42": NORMALIZED}, NORMALIZED, mana=324) is None


def test_identification_requires_fresh_complete_listing_not_an_old_tick_prompt(clock):
    prep = FamiliarPreparation(stage="summoning", summoned=True, attempts=1, deadline=30)
    assert prep.next_command({}, NORMALIZED) == "look"
    prep.observe(TICK)
    assert prep.next_command({"#42": NORMALIZED}, NORMALIZED) is None
    head, prompt = LISTING.split("<", 1)
    prep.observe(head)
    assert prep.listing_started and not prep.listing_complete
    assert prep.next_command({"#42": NORMALIZED}, NORMALIZED) is None
    prep.observe("<" + prompt)
    assert prep.next_command({"#42": NORMALIZED}, NORMALIZED) == "group #42"


def test_long_complete_room_listing_retains_its_header_proof_with_a_bounded_buffer(clock):
    prep = FamiliarPreparation(stage="identifying", deadline=30, attempts=1)
    prep.observe(LISTING.replace("[#42]", "A long room description.\n" * 200 + "[#42]"))
    assert prep.listing_complete and len(prep.buffer) <= 2000
    assert prep.next_command({"#42": NORMALIZED}, NORMALIZED) == "group #42"


@pytest.mark.parametrize("reply", [
    "You don't have enough mana.\n", "You can't summon a familiar indoors.\n",
    "You can't summon a familiar underwater.\n",
])
def test_source_summon_refusals_end_preparation_without_waiting(clock, reply):
    prep = FamiliarPreparation()
    prep.next_command({}, NORMALIZED, mana=324)
    prep.observe(reply)
    assert prep.failure and not prep.pending and prep.attempts == 1


@pytest.mark.parametrize("boundary", ["runtime", "combat"])
def test_pending_preparation_does_not_hold_emergency_authorities(clock, boundary):
    policy = policy_fixture()
    state = CharacterState(level=8, room_vnum="2", position=7, hp=113, max_hp=113,
                           mana=324, sector="hills", room_flags=["no_mob"])
    policy.familiar_preparation = FamiliarPreparation(stage="summoning", deadline=30, attempts=1)
    if boundary == "runtime":
        policy.runtime_boundary_requested = True
    else:
        state.in_combat, state.position, policy.combat_active = True, 6, True
    assert policy._familiar_staging_decision(state) is None
    # The pending preparation never consumes or resets the global boundary.
    assert policy.runtime_boundary_requested if boundary == "runtime" else policy.combat_active
    assert policy.familiar_preparation.attempts == 1


@pytest.mark.parametrize("reason", [
    "summon familiar was not positively confirmed",
    "familiar group ownership was not positively confirmed",
    "familiar preparation exceeded its confirmation deadline",
    "summon familiar exhausted three recitation attempts",
    "insufficient observed mana for summon familiar",
])
def test_temporary_preparation_failure_keeps_the_normal_retry_budget(reason):
    policy_id = "source-ranked-hunt-moria-4005-4022-8"
    result = {"observed": False, "viable": False, "route_hazard": reason, "boot_id": "test-boot"}
    state = {
        "level": 8, "world_boot_id": "test-boot",
        "campaign_policy_revision": campaign._CAMPAIGN_POLICY_REVISION,
        "campaign_research_results": {policy_id: result},
    }
    repaired = campaign._refresh_policy_revision(state)
    assert repaired["campaign_research_results"][policy_id] == {**result, "retryable_failure": True}
    assert "retryable_failure" not in result
    for remaining in [2, 1]:
        repaired = campaign._clear_absent_research_results(repaired, except_policy_id="")
        repaired = campaign._refresh_policy_revision(repaired)
        assert repaired[campaign._RESEARCH_ABSENCE_COOLDOWN_KEY][policy_id] == remaining
        assert repaired["campaign_research_results"][policy_id]["route_hazard"] == reason
    repaired = campaign._clear_absent_research_results(repaired, except_policy_id="")
    repaired = campaign._refresh_policy_revision(repaired)
    assert policy_id not in repaired.get("campaign_research_results", {})


@pytest.mark.parametrize("boundary", [
    "fatal", "negative-consider", "real-refusal", "identity", "completed", "unrelated-policy",
])
def test_preparation_retry_classification_preserves_stronger_evidence(boundary):
    policy_id = "source-ranked-hunt-moria-4005-4022-8"
    result = {"route_hazard": "summon familiar was not positively confirmed", "boot_id": "test-boot"}
    if boundary == "fatal":
        result["fatal_failure"] = True
    elif boundary == "negative-consider":
        result["consider_viable"] = False
    elif boundary == "real-refusal":
        result["route_hazard"] = "summon familiar was explicitly refused"
    elif boundary == "identity":
        result["route_hazard"] = "summoned familiar identity is missing or ambiguous"
    elif boundary == "completed":
        result["completed_kill"] = True
    else:
        policy_id = "another-policy"
    state = {"campaign_research_results": {policy_id: result}}
    assert campaign._repair_retryable_dynamic_route_hazards(state) is state
