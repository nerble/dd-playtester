from dataclasses import replace

import pytest

from dd4tester.character import CharacterSpec
from dd4tester.companions import FamiliarPreparation
from dd4tester.fastwalks import route_named
from dd4tester.hunt_candidates import MobileSource, WorldSource
from dd4tester.observations import GameEvent
from dd4tester.starter import BotDecision, FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


DESCRIPTION = "The lemming smithy busily hammers away at a new pickaxe."
TARGET = "lemming smithy"


ORC_DESCRIPTION = "This orc is frothing around the mouth.  Better stay away."


def orc_encounter():
    policy = StarterPolicy(
        CharacterSpec.from_mapping({
            "name": "Testmage", "race": "human", "gender": "female", "class": "mage",
        }), "fixture-password", fastwalk_route=route_named("moria"),
        fastwalk_attack_target="the orc",
        fastwalk_hunt_stops=(FieldHuntStop(
            (), "the orc", source_mobile_vnum=4004,
            source_mobile_room_description=ORC_DESCRIPTION,
            exact_target=True, require_isolated=True,
            maximum_pursuit_steps=1, pursuit_room_vnums=("4029",),
        ),),
        source_mobile_targets={" ".join(ORC_DESCRIPTION.lower().split()): ("the orc",)},
        source_mobile_vnums_by_target_room={"the orc": {"4028": (4004,)}},
    )
    policy.in_world = policy.prompt_ready = True
    policy.current_room = "4028"
    policy.fastwalk_hunt_looked = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    state = CharacterState(
        level=8, hp=113, max_hp=113, mana=324, max_mana=324,
        move=98, max_move=220, position=7, room_vnum="4028",
        room_name="The smelly tunnel", exits={"n": "4029", "s": "4027"},
    )
    return policy, state


def orc_listing(policy, state, selectors):
    policy.after_command(BotDecision("look", "refresh the observed room"))
    policy.observe_text(
        "The smelly tunnel\n[Exits: north south]\n"
        + "\n".join(f"[{selector}] {ORC_DESCRIPTION}" for selector in selectors)
        + "\n<113/113 hits 324/324 mana 98/220 move [Moria]>\n"
    )
    policy.observe_events([GameEvent("room_entered", "text", {
        "vnum": "4028", "name": "The smelly tunnel",
    })], state)


def test_run_12774_prefers_remaining_orc_after_fresh_crowd_recheck():
    policy, state = orc_encounter()
    orc_listing(policy, state, ("#23632", "#2763"))
    policy.observe_text("The orc leaves north.\n")
    assert policy.fastwalk_pursuit_direction == "north"

    orc_listing(policy, state, ("#23632",))
    decision = policy._fastwalk_hunt_plan_decision(state)

    assert policy.fastwalk_pursuit_direction is None
    assert decision.command == "consider #23632"
    assert not policy.fastwalk_attack_started
    assert policy.fastwalk_pursuit_steps == 0


def test_departure_alone_does_not_reuse_cached_remaining_selector():
    policy, state = orc_encounter()
    orc_listing(policy, state, ("#23632", "#2763"))
    policy.observe_text("The orc leaves north.\n")
    assert policy.fastwalk_pursuit_direction == "north"


def test_remaining_instance_does_not_inherit_an_old_positive_consider():
    policy, state = orc_encounter()
    orc_listing(policy, state, ("#23632", "#2763"))
    policy.observe_text("The orc leaves north.\n")
    policy.consider_target = "the orc"
    policy.consider_target_selector = "#2763"
    policy.consider_viable = True
    orc_listing(policy, state, ("#23632",))

    assert policy.consider_viable is None
    assert policy._fastwalk_hunt_plan_decision(state).command == "consider #23632"


def test_wrong_source_description_cannot_cancel_pursuit():
    policy, state = orc_encounter()
    orc_listing(policy, state, ("#23632", "#2763"))
    policy.observe_text("The orc leaves north.\n")
    stop = policy.fastwalk_hunt_stops[0]
    policy.fastwalk_hunt_stops = (replace(
        stop, source_mobile_room_description="A different orc waits here.",
    ),)
    orc_listing(policy, state, ("#23632",))

    assert policy.fastwalk_pursuit_direction == "north"


@pytest.mark.parametrize("boundary", ["absent", "combat", "crowd", "low-health"])
def test_remaining_target_keeps_pursuit_and_survival_boundaries(boundary):
    policy, state = orc_encounter()
    orc_listing(policy, state, ("#23632", "#2763"))
    policy.observe_text("The orc leaves north.\n")
    if boundary == "combat":
        policy.fastwalk_attack_started = True
    elif boundary == "low-health":
        state = replace(state, hp=10)
    selectors = () if boundary == "absent" else ("#23632",)
    if boundary == "crowd":
        selectors = ("#23632", "#2763")
    orc_listing(policy, state, selectors)
    decision = policy._fastwalk_hunt_plan_decision(state)
    if boundary in {"absent", "combat"}:
        assert decision.command == "north"
    elif boundary == "low-health":
        assert decision.command == "recall"
    else:
        assert not decision.command.startswith(("kill", "cast", "consider"))
        assert policy.fastwalk_crowded


def encounter():
    spec = CharacterSpec.from_mapping({
        "name": "Testmage", "race": "human", "gender": "female", "class": "mage",
    })
    stop = FieldHuntStop(
        (), TARGET, source_mobile_vnum=29953,
        source_mobile_room_description=DESCRIPTION,
        maximum_pursuit_steps=1, pursuit_room_vnums=("29964",),
        exact_target=True, require_isolated=True,
    )
    policy = StarterPolicy(
        spec, "fixture-password", fastwalk_route=route_named("moria"),
        fastwalk_hunt_stops=(stop,), fastwalk_attack_target=TARGET,
        source_mobile_vnums_by_target_room={TARGET: {"29966": (29953,)}},
    )
    policy.in_world = True
    policy.current_room = "29966"
    policy.world_boot_id = "fixture-boot"
    policy.fastwalk_attack_started = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    policy.fastwalk_hunt_looked = True
    policy.room_target_selectors["29966"] = {TARGET: ("#18435",)}
    policy.room_target_selector_descriptions["29966"] = {"#18435": DESCRIPTION.lower()}
    state = CharacterState(
        level=18, hp=218, max_hp=218, mana=444, max_mana=628,
        move=265, max_move=320, room_vnum="29966", position=7,
        exits={"w": "29964"},
    )
    return policy, state, stop


def gmcp_enemy(policy, state, *, vnum=29953, source="gmcp", duplicate=False):
    enemy = {
        "name": "the lemming smithy", "level": "14", "hp": "154",
        "maxhp": "274", "isnpc": str(vnum), "long_desc": DESCRIPTION,
    }
    policy.observe_events([GameEvent("enemies_changed", source, {
        "package": "Char.Enemies", "value": [[enemy, enemy] if duplicate else [enemy]],
    })], state)


def flee_and_follow(policy, state):
    # Run 12736: the sentinel fled west after burning hands, with no player HP loss.
    policy.observe_text("The lemming smithy leaves west.\nThe lemming smithy has fled!\n")
    decision = policy._fastwalk_hunt_plan_decision(state)
    assert decision is not None and decision.command == "west"
    policy.current_room = "29964"
    policy.room_target_counts["29964"] = {TARGET: 1}
    policy.room_target_selectors["29964"] = {TARGET: ("#18435",)}
    policy.room_target_selector_descriptions["29964"] = {"#18435": DESCRIPTION.lower()}
    return replace(state, room_vnum="29964", exits={"e": "29966"})


def test_live_sentinel_flee_replay_preserves_identity_but_still_considers():
    policy, state, stop = encounter()
    gmcp_enemy(policy, state)
    assert policy.observed_field_target is not None
    destination = flee_and_follow(policy, state)
    assert policy._source_target_reachability_issue(destination, stop, TARGET) is None
    decision = policy._consider_fastwalk_target(destination)
    assert decision.command == "consider #18435"
    assert not policy.fastwalk_hunt_stop_skipped
    assert policy.fastwalk_pursuit_identity_outcomes == [{
        "selector": "#18435", "source_mobile_vnum": 29953,
        "from_room": "29966", "to_room": "29964", "stop_index": 0, "step": 1,
    }]


@pytest.mark.parametrize("boundary", [
    "missing-gmcp", "text-only", "wrong-vnum", "duplicate-enemies", "ambiguous-selector",
])
def test_flee_requires_a_unique_live_gmcp_binding(boundary):
    policy, state, stop = encounter()
    if boundary == "ambiguous-selector":
        policy.room_target_selectors["29966"][TARGET] = ("#18435", "#18436")
    if boundary != "missing-gmcp":
        gmcp_enemy(policy, state, vnum=1 if boundary == "wrong-vnum" else 29953,
                   source="text" if boundary == "text-only" else "gmcp",
                   duplicate=boundary == "duplicate-enemies")
    # A source-derived field value alone must not authorize pursuit identity.
    policy.active_target_mobile_vnum = 29953
    policy.fastwalk_emergency_recall_pending = False
    policy.fastwalk_abort_reason = None
    destination = flee_and_follow(policy, state)
    assert policy._source_target_reachability_issue(destination, stop, TARGET)
    assert not policy.fastwalk_pursuit_identity_outcomes


@pytest.mark.parametrize("boundary", [
    "new-id", "new-room", "new-boot", "new-level", "new-stop", "expired",
    "too-many-steps", "ambiguous-selector", "changed-description", "unknown-exit",
])
def test_pursuit_identity_is_short_lived_and_exact(boundary):
    policy, state, stop = encounter()
    gmcp_enemy(policy, state)
    if boundary == "unknown-exit":
        state = replace(state, exits={})
        policy.fastwalk_hunt_stops = (replace(stop, pursuit_room_vnums=()),)
    destination = flee_and_follow(policy, state)
    if boundary == "new-id":
        policy.room_target_selectors["29964"][TARGET] = ("#99",)
    elif boundary == "new-room":
        policy.current_room = "29965"
    elif boundary == "new-boot":
        policy.world_boot_id = "new-boot"
    elif boundary == "new-level":
        destination = replace(destination, level=19)
    elif boundary == "new-stop":
        policy.fastwalk_hunt_stop_index = 1
    elif boundary == "expired":
        policy.fleeing_field_target = replace(policy.fleeing_field_target, observed_at=0)
    elif boundary == "too-many-steps":
        policy.fastwalk_pursuit_steps = 2
    elif boundary == "ambiguous-selector":
        policy.room_target_selectors["29964"][TARGET] = ("#18435", "#99")
    elif boundary == "changed-description":
        policy.room_target_selector_descriptions["29964"]["#18435"] = "a different smithy"
    assert policy._source_target_reachability_issue(destination, stop, TARGET)
    assert not policy.fastwalk_pursuit_identity_outcomes


def test_crowd_gate_still_applies_after_live_pursuit_identification():
    policy, state, stop = encounter()
    gmcp_enemy(policy, state)
    destination = flee_and_follow(policy, state)
    policy.room_target_counts["29964"]["a dangerous guard"] = 1
    decision = policy._consider_fastwalk_target(destination)
    assert not decision.command.startswith("kill")
    assert policy.fastwalk_crowded and policy.fastwalk_hunt_stop_skipped


def test_empty_enemy_packet_before_flee_does_not_erase_observed_identity():
    policy, state, stop = encounter()
    gmcp_enemy(policy, state)
    policy.observe_events([GameEvent("enemies_changed", "gmcp", {"value": []})], state)
    destination = flee_and_follow(policy, state)
    assert policy._source_target_reachability_issue(destination, stop, TARGET) is None


def test_a_new_policy_cannot_restore_instance_ownership():
    first, state, stop = encounter()
    gmcp_enemy(first, state)
    destination = flee_and_follow(first, state)
    policy, _, _ = encounter()
    policy.current_room = "29964"
    policy.room_target_selectors = first.room_target_selectors
    policy.room_target_selector_descriptions = first.room_target_selector_descriptions
    assert policy._source_target_reachability_issue(destination, stop, TARGET)


@pytest.mark.parametrize("acknowledged", [True, False])
def test_same_fleeing_target_requires_a_new_confirmed_companion_order(acknowledged):
    policy, state, stop = encounter()
    description = "A small pony stands here grazing."
    policy.source_world = WorldSource(mobiles={19900: MobileSource(
        19900, "pony", "the pony", 15, 0, 0, "mounts.are", description,
    )})
    policy.known_skills.add("summon familiar")
    policy.known_skill_levels["summon familiar"] = 42
    policy.familiar_active = True
    policy.familiar_preparation = FamiliarPreparation(
        stage="ready", selector="#23665", summoned=True, grouped=True,
        order_confirmed=True,
    )
    policy.familiar_ordered_target = TARGET
    gmcp_enemy(policy, state)
    destination = flee_and_follow(policy, state)
    assert policy.familiar_ordered_target is None
    policy.room_target_selector_descriptions["29964"]["#23665"] = description.lower()
    policy.consider_viable = True
    order = policy._familiar_precombat_decision(
        destination, target=TARGET, command_keyword="#18435", allow_start=True,
    )
    assert order.command == "order #23665 kill #18435"
    if acknowledged:
        policy.observe_text("Ok.\n")
    attack = policy._familiar_precombat_decision(destination, command_keyword="#18435")
    if acknowledged:
        assert attack.command == "kill #18435"
    else:
        assert attack is None and policy.familiar_unavailable
