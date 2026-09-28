from dataclasses import replace
from pathlib import Path

import pytest

from dd4tester.character import CharacterSpec
from dd4tester.companions import (
    FamiliarPreparation,
    FamiliarWithdrawal,
    familiar_kill_credits_owner_xp,
    familiar_staging_room,
    learned_familiar_available,
)
from dd4tester.fastwalks import Fastwalk
from dd4tester.hunt_candidates import ExitSource, MobileSource, MobReset, RoomSource, WorldSource
from dd4tester.starter import FieldHuntStop, StarterPolicy, _normalize_mobile_line
from dd4tester.state import CharacterState
import dd4tester.campaign as campaign


@pytest.mark.parametrize(
    ("character_class", "subclass", "credited"),
    [
        ("mage", None, False),
        ("mage", "warlock", False),
        ("mage", "necromancer", True),
        ("psionic", "witch", True),
        ("shifter", None, True),
        ("shifter", "werewolf", True),
    ],
)
def test_familiar_kill_xp_credit_matches_dd4_source_whitelist(
    character_class, subclass, credited,
):
    assert familiar_kill_credits_owner_xp(character_class, subclass) is credited


DESCRIPTION = "A small pony stands here grazing."
NORMALIZED = _normalize_mobile_line(DESCRIPTION)
SUMMONED = "You raise your hands and the form of the pony appears before you.\n"
LISTING = "Hills\n[Exits: south]\n[#42] A small pony stands here grazing.\n<113/113 hits 224/324 mana 167/220 move [Test]> "


def world_fixture():
    return WorldSource(
        rooms={
            1: RoomSource(1, "Temple", "test.are", {"south": ExitSource("south", 2, 0, 0)}, room_flags=8),
            2: RoomSource(2, "Hills", "test.are", {"south": ExitSource("south", 3, 0, 0)}, room_flags=4, sector_type=4),
            3: RoomSource(3, "Cave", "test.are", {"north": ExitSource("north", 2, 0, 0)}, room_flags=8),
        },
        mobiles={19900: MobileSource(19900, "pony", "the pony", 15, 0, 0, "mounts.are", DESCRIPTION)},
    )


def test_staging_selects_outdoor_no_mob_waypoint():
    world = world_fixture()
    assert familiar_staging_room(world, (1, 2, 3), (3,)) == 2


@pytest.mark.parametrize("boundary", [
    "indoors", "not-no-mob", "missing", "random", "water", "air", "wall", "reset", "no-edge", "no-search",
])
def test_staging_requires_a_source_proven_ground_route(boundary):
    world = world_fixture()
    search = (3,)
    if boundary == "indoors":
        world.rooms[2].room_flags |= 8
    elif boundary == "not-no-mob":
        world.rooms[2].room_flags = 0
    elif boundary == "missing":
        del world.rooms[3]
    elif boundary == "random":
        world.rooms[3].random_exits = True
    elif boundary == "water":
        world.rooms[3].sector_type = 7
    elif boundary == "air":
        world.rooms[3].sector_type = 9
    elif boundary == "wall":
        world.rooms[2].exits["south"] = replace(world.rooms[2].exits["south"], flags=128)
    elif boundary == "reset":
        world.mob_resets.append(MobReset(7, 2, 1, ()))
    elif boundary == "no-edge":
        world.rooms[2].exits.clear()
    else:
        search = ()
    assert familiar_staging_room(world, (1, 2, 3), search) is None


def prepared():
    preparation = FamiliarPreparation()
    assert preparation.next_command({}, NORMALIZED, mana=324) == "cast 'summon familiar'"
    preparation.observe(SUMMONED[:35])
    preparation.observe(SUMMONED[35:])
    assert preparation.next_command({}, NORMALIZED) == "look"
    preparation.observe(LISTING)
    assert preparation.next_command({"#42": NORMALIZED}, NORMALIZED) == "group #42"
    preparation.observe("The pony joins your group.\n")
    assert preparation.next_command({}, NORMALIZED) is None
    return preparation


def test_preparation_requires_positive_fragmented_acknowledgements():
    preparation = prepared()
    assert preparation.present({"#42": NORMALIZED}, NORMALIZED)
    assert not preparation.present({"#43": NORMALIZED}, NORMALIZED)
    assert not preparation.present({"#42": "another animal"}, NORMALIZED)
    preparation.expect_order()
    assert not preparation.order_confirmed
    preparation.observe("O")
    preparation.observe("k.\n")
    assert preparation.order_confirmed
    assert "buffer" not in preparation.evidence()


def test_in_place_familiar_withdrawal_requires_sleep_not_flee() -> None:
    withdrawal = FamiliarWithdrawal(selector="#42", settle_in_place=True)

    assert withdrawal.next_command(now=1) == "order #42 flee Fear"
    withdrawal.observe(
        "The pony leaves west.\nThe pony has fled!\nOk.\n",
        now=2,
    )

    assert withdrawal.confirmed is False
    assert withdrawal.next_command(now=2) == "order #42 sleep"
    withdrawal.observe("Ok.\n", now=3)
    assert withdrawal.confirmed is False
    withdrawal.observe("The pony sleeps.\n", now=3.5)

    assert withdrawal.confirmed is True


@pytest.mark.parametrize("reply", [
    "", "The sun slowly disappears in the west.\n",
    "Someone says 'You fail to correctly recite the spell!'\n",
    "Someone says 'The pony joins your group.'\n",
])
def test_failed_summon_never_groups_or_retries(reply):
    preparation = FamiliarPreparation()
    preparation.next_command({}, NORMALIZED, mana=324, now=0)
    preparation.observe(reply, now=1)
    assert preparation.next_command({}, NORMALIZED, now=2) is None
    assert preparation.failure is None and preparation.attempts == 1
    assert preparation.next_command({}, NORMALIZED, now=30) is None
    assert preparation.failure
    assert preparation.next_command({}, NORMALIZED, now=31) is None


def test_preparation_recovers_mount_selector_from_fresh_listing_when_room_cache_misses():
    preparation = FamiliarPreparation()
    preparation.next_command({}, NORMALIZED, mana=324)
    preparation.observe(SUMMONED)
    assert preparation.next_command({}, NORMALIZED) == "look"
    preparation.observe(LISTING.replace("[#42]", "[#27586] <Mount>"))
    assert preparation.next_command({}, NORMALIZED, room_vnum="3030") == "group #27586"
    preparation.observe("The pony joins your group.\n")
    assert preparation.next_command({}, NORMALIZED) is None
    assert preparation.present({}, NORMALIZED, room_vnum="3030")


@pytest.mark.parametrize(
    ("listing", "selectors"),
    [
        (
            LISTING.replace("[#42] A small pony stands here grazing.\n", ""),
            {},
        ),
        (
            LISTING.replace(
                "[#42] A small pony stands here grazing.\n",
                "[#42] A small pony stands here grazing.\n"
                "[#43] A small pony stands here grazing.\n",
            ),
            {},
        ),
        (LISTING, {"#42": NORMALIZED, "#43": NORMALIZED}),
    ],
)
def test_missing_or_ambiguous_companion_identity_stops(listing, selectors):
    preparation = FamiliarPreparation()
    preparation.next_command({}, NORMALIZED, mana=324)
    preparation.observe(SUMMONED)
    assert preparation.next_command({}, NORMALIZED) == "look"
    preparation.observe(listing)
    assert preparation.next_command(selectors, NORMALIZED) is None
    assert preparation.failure


def test_group_failure_is_not_ownership_evidence():
    preparation = FamiliarPreparation()
    preparation.next_command({}, NORMALIZED, mana=324)
    preparation.observe(SUMMONED)
    preparation.next_command({}, NORMALIZED)
    preparation.observe(LISTING)
    preparation.next_command({"#42": NORMALIZED}, NORMALIZED)
    preparation.observe("The pony isn't following you.\n")
    assert preparation.next_command({}, NORMALIZED) is None
    assert preparation.failure and not preparation.grouped


def policy_fixture():
    spec = CharacterSpec.from_mapping({
        "name": "Testmage", "race": "human", "gender": "female", "class": "mage",
    })
    policy = StarterPolicy(
        spec, "fixture-password", source_world=world_fixture(),
        fastwalk_route=Fastwalk("test", 8, 8, "2s"),
        fastwalk_hunt_stops=(FieldHuntStop(
            (), "orc", require_familiar=True, familiar_staging_room_vnum="2",
        ),),
        known_skills=("summon familiar", "magic missile"),
        known_skill_levels={"summon familiar": 36, "magic missile": 35},
    )
    policy.in_world = True
    return policy


def test_field_runner_stages_and_verifies_exact_companion_before_indoor_order():
    policy = policy_fixture()
    outdoor = CharacterState(level=8, room_vnum="2", position=7, mana=324, sector="hills", room_flags=["no_mob"])
    summon = policy._fastwalk_research_decision(outdoor)
    assert summon is not None and summon.command == "cast 'summon familiar'"
    policy.observe_text(SUMMONED)
    look = policy._familiar_staging_decision(outdoor)
    assert look is not None and look.command == "look"
    policy.observe_text(LISTING)
    policy.room_target_selector_descriptions["2"] = {"#42": NORMALIZED}
    group = policy._familiar_staging_decision(outdoor)
    assert group is not None and group.command == "group #42"
    policy.observe_text("The pony joins your group.\n")
    assert policy._familiar_staging_decision(outdoor) is None
    assert policy.familiar_active
    inside = replace(outdoor, room_vnum="3", room_flags=["indoors"], sector="inside")
    policy.room_target_selector_descriptions["3"] = {"#42": NORMALIZED}
    policy.room_target_selectors["3"] = {"pony": ("#42",)}
    assert policy._source_mobile_name_is_non_assisting_bystander("pony", inside)
    policy.consider_viable = True
    order = policy._familiar_precombat_decision(inside, target="orc", command_keyword="#99", allow_start=True)
    assert order is not None and order.command == "order #42 kill #99"
    policy.observe_text("Ok.\n")
    opener = policy._familiar_precombat_decision(inside, command_keyword="#99")
    assert opener is not None and opener.command == "kill #99"


@pytest.mark.parametrize("boundary", ["missing", "changed-id", "unconfirmed-order"])
def test_indoor_combat_cannot_use_an_unconfirmed_companion(boundary):
    policy = policy_fixture()
    policy.familiar_preparation = prepared()
    policy.familiar_active = True
    policy.consider_viable = True
    inside = CharacterState(level=8, room_vnum="3", room_flags=["indoors"], position=7, mana=324)
    if boundary == "changed-id":
        policy.room_target_selector_descriptions["3"] = {"#43": NORMALIZED}
    if boundary == "unconfirmed-order":
        policy.room_target_selector_descriptions["3"] = {"#42": NORMALIZED}
        order = policy._familiar_precombat_decision(inside, target="orc", allow_start=True)
        assert order is not None and order.command.startswith("order #42")
    else:
        refresh = policy._familiar_precombat_decision(inside, target="orc", allow_start=True)
        assert refresh.command == "look"
    assert policy._familiar_precombat_decision(inside, target="orc", allow_start=True) is None
    assert policy.familiar_unavailable and not policy.fastwalk_attack_started


@pytest.mark.parametrize("level,hp,mana,mobile,room,waypoint,skill", [
    (8, 113, 324, 4005, 4022, "4002", "chill touch"),
    (18, 218, 628, 29953, 29966, "29950", "burning hands"),
    (8, 113, 324, 609, 600, "3052", "chill touch"),
])
def test_real_source_staging_contract_reaches_field_stops(level, hp, mana, mobile, room, waypoint, skill):
    world = campaign.load_world_source(Path("runs/dd4-source/server/area"), include_all_areas=True)
    state = {
        "level": level, "max_hp": hp, "max_mana": mana, "character_class": "mage",
        "world_boot_id": "test-boot", "campaign_known_skills": [skill, "summon familiar"],
        "campaign_known_skill_levels": {skill: 35, "summon familiar": 36},
    }
    candidates = campaign.rank_hunt_candidates(
        world, character_level=level, character_class="mage",
        known_skills=state["campaign_known_skills"],
        known_skill_levels=state["campaign_known_skill_levels"],
        include_xp_only=True, include_level_ceiling_candidates=True,
        level_ceiling_offset=1, include_all_areas=True, character_max_hp=hp,
        recall_origins={0: 3001},
    )
    target = next(t for t in candidates if t.mobile_vnum == mobile and t.room_vnum == room)
    assert campaign._source_ranked_familiar_staging_room(target, world) == waypoint
    assert campaign._source_ranked_familiar_probe_allowed(target, state, character_level=level, source_world=world)
    assert campaign._select_source_ranked_hunt_candidate(
        (target,), state, world=world, character_level=level, character_max_hp=hp,
    ) == target
    stops = campaign._source_ranked_hunt_stops(target, world, character_level=level, state=state)
    target_stops = [s for s in stops if s.source_mobile_vnum == mobile]
    assert target_stops
    assert all(s.require_familiar and not s.require_sanctuary for s in target_stops)
    assert all(s.familiar_staging_room_vnum == waypoint for s in target_stops)
    if mobile == 609:
        assert all(s.familiar_withdraw_before_opener for s in target_stops)
    if mobile == 29953:
        assert all(s.familiar_withdraw_before_opener for s in target_stops)
    state["campaign_known_skill_levels"].pop("summon familiar")
    assert not campaign._source_ranked_familiar_probe_allowed(target, state, character_level=level, source_world=world)


def test_real_source_low_load_target_withdraws_familiar_before_player_opener():
    world = campaign.load_world_source(
        Path("runs/dd4-source/server/area"), include_all_areas=True,
    )
    skills = [
        "armor", "chill touch", "magic missile", "protective magiks",
        "summon familiar",
    ]
    levels = {
        "armor": 36, "chill touch": 35, "magic missile": 35,
        "protective magiks": 36, "summon familiar": 36,
    }
    state = {
        "level": 9, "max_hp": 123, "max_mana": 351,
        "character_class": "mage", "world_boot_id": "test-boot",
        "campaign_known_skills": skills,
        "campaign_known_skill_levels": levels,
    }
    candidate = next(
        item
        for item in campaign.rank_hunt_candidates(
            world,
            character_level=9,
            character_class="mage",
            known_skills=skills,
            known_skill_levels=levels,
            include_xp_only=True,
            include_level_ceiling_candidates=True,
            level_ceiling_offset=1,
            include_all_areas=True,
            character_max_hp=123,
            recall_origins={0: 3001},
        )
        if item.mobile_vnum == 1501 and item.room_vnum == 1509
    )

    stops = [
        stop
        for stop in campaign._source_ranked_hunt_stops(
            candidate, world, character_level=9, state=state,
        )
        if stop.source_mobile_vnum == 1501
    ]

    assert stops
    assert all(stop.familiar_withdraw_before_opener for stop in stops)


def test_wild_lookalike_is_not_exempted_with_the_owned_familiar():
    policy = policy_fixture()
    policy.familiar_preparation = prepared()
    state = CharacterState(level=8, room_vnum="3")
    policy.room_target_selector_descriptions["3"] = {"#42": NORMALIZED, "#43": NORMALIZED}
    policy.room_target_selectors["3"] = {"pony": ("#42", "#43")}
    assert not policy._source_mobile_name_is_non_assisting_bystander("pony", state)


@pytest.mark.parametrize("changes", [
    {"mana": 99}, {"mana": None}, {"level": 3}, {"level": 25},
    {"room_flags": []}, {"room_flags": ["no_mob", "indoors"]},
    {"sector": None}, {"sector": "underwater"},
])
def test_live_staging_gate_aborts_without_casting_when_capability_is_missing(changes):
    policy = policy_fixture()
    state = CharacterState(level=8, room_vnum="2", position=7, mana=324, sector="hills", room_flags=["no_mob"])
    decision = policy._familiar_staging_decision(replace(state, **changes))
    assert decision is not None and not decision.command.startswith("cast")
    assert policy.fastwalk_returning and policy.familiar_unavailable
    assert policy.familiar_preparation.failure


@pytest.mark.parametrize("failure", [
    "You fail to correctly recite the spell!\n",
    "You lost your concentration.\n", "You lose your concentration.\n",
])
def test_recitation_failure_retries_only_three_times(failure):
    preparation = FamiliarPreparation()
    for attempt in range(3):
        assert preparation.next_command({}, NORMALIZED, mana=300 - attempt * 50, now=attempt) == "cast 'summon familiar'"
        preparation.observe(failure[:12], now=attempt)
        preparation.observe(failure[12:], now=attempt)
    assert preparation.next_command({}, NORMALIZED, mana=150, now=3) is None
    assert preparation.attempts == 3 and not preparation.summoned
    assert "three" in preparation.failure


@pytest.mark.parametrize("mana,now", [(99, 1), (None, 1), (300, 30)])
def test_summon_retry_requires_mana_and_time(mana, now):
    preparation = FamiliarPreparation()
    preparation.next_command({}, NORMALIZED, mana=300, now=0)
    preparation.observe("You fail to correctly recite the spell!\n", now=0)
    assert preparation.next_command({}, NORMALIZED, mana=mana, now=now) is None
    assert preparation.failure and preparation.attempts == 1


def test_success_after_failed_cast_does_not_require_another_cast_mana_reserve():
    preparation = FamiliarPreparation()
    preparation.next_command({}, NORMALIZED, mana=150, now=0)
    preparation.observe("You fail to correctly recite the spell!\n", now=0)
    assert preparation.next_command({}, NORMALIZED, mana=100, now=1) == "cast 'summon familiar'"
    preparation.observe(SUMMONED, now=1)
    assert preparation.next_command({}, NORMALIZED, mana=0, now=2) == "look"
    preparation.observe(LISTING, now=2)
    assert preparation.next_command({"#42": NORMALIZED}, NORMALIZED, mana=0, now=3) == "group #42"
    preparation.observe("The pony joins your group.\n", now=3)
    assert preparation.next_command({}, NORMALIZED, mana=0, now=4) is None
    assert preparation.stage == "ready" and preparation.attempts == 2


@pytest.mark.parametrize("base,subclass,percent,allowed", [
    ("mage", None, 42, True), ("mage", "warlock", 42, True),
    ("psionic", "witch", 42, True), ("warrior", None, 42, False),
    ("mage", "witch", 42, False), ("psionic", None, 42, False),
    ("mage", None, 0, False), ("mage", None, True, False),
    ("mage", None, "42", False), ("mage", "unknown", 42, False),
])
def test_familiar_source_authorization_is_shared_with_candidate_selection(base, subclass, percent, allowed):
    skills = {"summon familiar": percent}
    assert learned_familiar_available(base, subclass, skills) is allowed
    assert campaign._source_ranked_familiar_skill_available({
        "character_class": base, "subclass": subclass,
        "campaign_known_skill_levels": skills,
    }) is allowed


def outdoor_fixture():
    policy = policy_fixture()
    policy.fastwalk_hunt_stops = (replace(policy.fastwalk_hunt_stops[0], familiar_staging_room_vnum=None),)
    policy.consider_viable = True
    state = CharacterState(level=18, room_vnum="2", position=7, mana=628, sector="hills")
    return policy, state


def test_familiar_is_not_sent_into_source_hunt_without_explicit_authorization():
    policy = policy_fixture()
    policy.fastwalk_hunt_stops = (
        replace(
            policy.fastwalk_hunt_stops[0],
            target="sullen bard",
            source_mobile_vnum=3504,
            require_familiar=False,
            familiar_withdraw_before_opener=False,
        ),
    )
    policy.consider_viable = True
    state = CharacterState(level=9, room_vnum="3577", position=7, mana=351)

    decision = policy._familiar_precombat_decision(
        state, target="the bard", allow_start=True,
    )

    assert decision is None
    assert policy.familiar_preparation.stage == "idle"
    assert policy.familiar_active is False


def test_real_midennir_bard_hunt_does_not_start_an_unapproved_familiar():
    world = campaign.load_world_source(
        Path("runs/dd4-source/server/area"), include_all_areas=True,
    )
    skills = [
        "armor", "chill touch", "magic missile", "protective magiks",
        "summon familiar",
    ]
    levels = {skill: 35 for skill in skills}
    levels["summon familiar"] = 36
    state = {
        "level": 9,
        "max_hp": 123,
        "max_mana": 351,
        "character_class": "mage",
        "world_boot_id": "test-boot",
        "campaign_known_skills": skills,
        "campaign_known_skill_levels": levels,
    }
    candidate = next(
        item
        for item in campaign.rank_hunt_candidates(
            world,
            character_level=9,
            character_class="mage",
            known_skills=skills,
            known_skill_levels=levels,
            include_xp_only=True,
            include_level_ceiling_candidates=True,
            level_ceiling_offset=1,
            include_all_areas=True,
            character_max_hp=123,
            recall_origins={0: 3001},
        )
        if item.mobile_vnum == 3504 and item.room_vnum == 3577
    )
    stops = campaign._source_ranked_hunt_stops(
        candidate, world, character_level=9, state=state,
    )
    assert stops
    assert all(
        not stop.require_familiar and not stop.familiar_withdraw_before_opener
        for stop in stops
    )

    policy = StarterPolicy(
        CharacterSpec.from_mapping({
            "name": "Testmage", "race": "human", "gender": "female",
            "class": "mage",
        }),
        "fixture-password",
        source_world=world,
        fastwalk_route=Fastwalk("bard", 3001, 3577, "south"),
        fastwalk_hunt_stops=stops,
        known_skills=skills,
        known_skill_levels=levels,
    )
    policy.in_world = True
    policy.consider_viable = True
    policy.fastwalk_attack_target = candidate.target
    character_state = CharacterState(
        level=9, room_vnum="3577", position=7, mana=351,
    )

    decision = policy._familiar_precombat_decision(
        character_state, target=candidate.target, allow_start=True,
    )

    assert decision is None
    assert policy.familiar_preparation.stage == "idle"
    assert policy.familiar_active is False


def test_run_12741_failed_outdoor_summon_retries_then_confirms_exact_ownership():
    policy, state = outdoor_fixture()
    first = policy._familiar_precombat_decision(state, target="guardian", command_keyword="#99", allow_start=True)
    assert first.command == "cast 'summon familiar'"
    policy.observe_text("You fail to correctly recite the spell!\n")
    retry = policy._familiar_precombat_decision(replace(state, mana=578))
    assert retry.command == "cast 'summon familiar'"
    assert not policy.familiar_active and not policy.fastwalk_attack_started
    policy.observe_text(SUMMONED)
    assert not policy.familiar_active
    assert policy._familiar_precombat_decision(state).command == "look"
    policy.observe_text(LISTING)
    policy.room_target_selector_descriptions["2"] = {"#42": NORMALIZED}
    assert policy._familiar_precombat_decision(state).command == "group #42"
    policy.observe_text("The pony joins your group.\n")
    assert policy._familiar_precombat_decision(state, command_keyword="#99").command == "order #42 kill #99"
    assert not policy.fastwalk_attack_started
    policy.observe_text("Ok.\n")
    assert policy._familiar_precombat_decision(state, command_keyword="#99").command == "kill #99"
    assert policy.fastwalk_attack_started
    assert policy.familiar_preparation.evidence()["attempts"] == 2


@pytest.mark.parametrize("boundary", [
    "missing-success", "ambiguous-identity", "missing-group", "missing-order",
    "moved", "combat", "runtime", "unpracticed", "missing-mana",
])
def test_outdoor_familiar_cannot_advance_without_each_confirmation(boundary):
    policy, state = outdoor_fixture()
    if boundary == "unpracticed":
        policy.known_skill_levels.clear()
    if boundary == "missing-mana":
        state = replace(state, mana=None)
    first = policy._familiar_precombat_decision(state, target="guardian", allow_start=True)
    if boundary in {"unpracticed", "missing-mana"}:
        assert first is None
        return
    assert first.command == "cast 'summon familiar'"
    if boundary == "combat":
        state = replace(state, position=6)
    elif boundary == "runtime":
        policy.runtime_boundary_requested = True
    elif boundary == "moved":
        state = replace(state, room_vnum="3")
    elif boundary != "missing-success":
        policy.observe_text(SUMMONED)
        assert policy._familiar_precombat_decision(state).command == "look"
        policy.observe_text(LISTING)
        policy.room_target_selector_descriptions["2"] = {"#42": NORMALIZED}
        if boundary == "ambiguous-identity":
            policy.room_target_selector_descriptions["2"]["#43"] = NORMALIZED
        else:
            assert policy._familiar_precombat_decision(state).command == "group #42"
            if boundary != "missing-group":
                policy.observe_text("The pony joins your group.\n")
                assert policy._familiar_precombat_decision(state).command.startswith("order #42 kill")
    assert policy._familiar_precombat_decision(state) is None
    assert not policy.familiar_active and not policy.fastwalk_attack_started


def test_staged_familiar_uses_same_bounded_recitation_retry():
    policy = policy_fixture()
    state = CharacterState(level=8, room_vnum="2", position=7, mana=324, sector="hills", room_flags=["no_mob"])
    assert policy._familiar_staging_decision(state).command == "cast 'summon familiar'"
    policy.observe_text("You fail to correctly recite the spell!\n")
    assert policy._familiar_staging_decision(replace(state, mana=274)).command == "cast 'summon familiar'"
    assert not policy.fastwalk_returning and not policy.familiar_unavailable


def test_runtime_boundary_waits_for_queued_familiar_group_acknowledgement():
    policy = policy_fixture()
    state = CharacterState(
        level=8,
        room_vnum="2",
        position=7,
        mana=324,
        sector="hills",
        room_flags=["no_mob"],
    )
    assert policy._familiar_staging_decision(state).command == "cast 'summon familiar'"
    policy.observe_text(SUMMONED)
    assert policy._familiar_staging_decision(state).command == "look"
    policy.observe_text(LISTING)
    policy.room_target_selector_descriptions["2"] = {"#42": NORMALIZED}
    assert policy._familiar_staging_decision(state).command == "group #42"

    policy.request_runtime_boundary(state)
    assert policy.runtime_boundary_familiar_grace_until is not None
    assert policy._familiar_staging_decision(state) is None
    assert policy.familiar_preparation.stage == "grouping"

    policy.observe_text("The pony joins your group.\n")
    assert policy._familiar_staging_decision(state) is None
    assert policy.familiar_preparation.stage == "ready"
    assert policy.familiar_active


def test_staging_hook_does_not_abort_endpoint_preparation():
    policy, state = outdoor_fixture()
    policy._familiar_precombat_decision(state, target="guardian", allow_start=True)
    assert policy._familiar_staging_decision(state) is None
    assert policy.familiar_preparation.failure is None
    assert not policy.fastwalk_returning


@pytest.mark.parametrize("boundary", ["left-room", "missing-familiar", "runtime"])
def test_confirmed_order_cannot_commit_after_context_changes(boundary):
    policy, state = outdoor_fixture()
    policy.familiar_preparation = prepared()
    policy.room_target_selector_descriptions["2"] = {"#42": NORMALIZED}
    assert policy._familiar_precombat_decision(state, target="guardian", allow_start=True).command.startswith("order #42 kill")
    policy.observe_text("Ok.\n")
    if boundary == "left-room":
        state = replace(state, room_vnum="3")
    elif boundary == "missing-familiar":
        policy.room_target_selector_descriptions["2"].clear()
    else:
        policy.runtime_boundary_requested = True
    assert policy._familiar_precombat_decision(state) is None
    assert not policy.familiar_active and not policy.fastwalk_attack_started


def test_run_12744_refreshes_after_room_listing_precedes_follower_arrival():
    policy, state = outdoor_fixture()
    state = replace(state, room_vnum="4026", sector="inside", room_flags=["indoors"])
    policy.familiar_preparation = prepared()
    policy.familiar_active = True
    policy.room_target_selector_descriptions["4026"] = {
        "#23672": "this large orc is looking for someone small to pick on.",
    }
    policy.observe_text("The pony has arrived.\n")
    refresh = policy._familiar_precombat_decision(state, target="large orc", command_keyword="#23672", allow_start=True)
    assert refresh.command == "look"
    assert not policy.familiar_unavailable and not policy.fastwalk_attack_started
    policy.room_target_selector_descriptions["4026"]["#42"] = NORMALIZED
    assert policy._familiar_precombat_decision(state) is None
    order = policy._familiar_precombat_decision(state, target="large orc", command_keyword="#23672", allow_start=True)
    assert order.command == "order #42 kill #23672"
    assert not policy.fastwalk_attack_started
    policy.observe_text("Ok.\n")
    assert policy._familiar_precombat_decision(state, command_keyword="#23672").command == "kill #23672"


@pytest.mark.parametrize("selectors", [{}, {"#43": NORMALIZED}])
def test_refresh_cannot_convert_arrival_text_or_a_different_id_into_ownership(selectors):
    policy, state = outdoor_fixture()
    policy.familiar_preparation = prepared()
    policy.familiar_active = True
    policy.observe_text("The pony has arrived.\n")
    assert policy._familiar_precombat_decision(state, target="orc", allow_start=True).command == "look"
    policy.room_target_selector_descriptions["2"] = selectors
    assert policy._familiar_precombat_decision(state, target="orc", allow_start=True) is None
    assert policy.familiar_unavailable and not policy.familiar_active
    assert policy._familiar_precombat_decision(state, target="orc", allow_start=True) is None
