from dataclasses import replace
import json
from types import SimpleNamespace

import pytest

import dd4tester.campaign as campaign
from dd4tester.character import CharacterSpec
from dd4tester.equipment import GearCatalog
from dd4tester.fastwalks import route_named
from dd4tester.hunt_candidates import ACT_AGGRESSIVE, AFF_HIDE, AFF_INVISIBLE, HuntCandidate, MobileSource, ObjectSource, WorldSource
from dd4tester.state import CharacterState
from dd4tester.starter import BotDecision, FieldHuntStop, StarterPolicy


def candidate(vnum):
    return HuntCandidate(
        "caution", 1, "test.are", vnum, "a target", "target", 45,
        100, "Target room", (), 1, 1, 0, (), 0, 0, (),
    )


@pytest.mark.parametrize("hidden", [True, False])
def test_dynamic_carrier_visibility_uses_selected_mobile_not_generic_policy(monkeypatch, hidden):
    runner = campaign.CampaignRunner.__new__(campaign.CampaignRunner)
    runner._source_world = WorldSource(mobiles={1: MobileSource(
        1, "target", "a target", 45, 0, 0, "test.are", affected_flags=AFF_HIDE if hidden else 0,
    )})
    runner._gear_catalog = None
    runner._emit_progress = lambda _: None
    selected = candidate(1)
    runner._selected_source_consumable_candidate = selected
    policy = replace(campaign._SOURCE_RANKED_SANCTUARY_ALTERNATE_POLICY,
        policy_id=campaign._source_ranked_sanctuary_maintenance_policy_id(selected, character_level=45),
        source_mobile_vnums=(999,))
    detection_carrier = SimpleNamespace(mobile_vnum=2)
    monkeypatch.setattr(campaign, "_has_campaign_food", lambda *a, **kw: True)
    monkeypatch.setattr(campaign, "_campaign_needs_healer_recovery", lambda _: False)
    monkeypatch.setattr(campaign, "_select_source_consumable_candidate", lambda *a, **kw: (detection_carrier, (4558,)))
    observed = state()
    preparation = runner._prepare_hunt_visibility(observed, policy)
    if hidden:
        assert preparation.execution == "source-ranked-detect-hidden-reserve"
        assert observed["campaign_visibility_preparation_target"]["mobile_vnums"] == [1]
        assert runner._selected_source_consumable_candidate is detection_carrier
    else:
        assert preparation is None
        assert runner._selected_source_consumable_candidate is selected


def state():
    return {
        "level": 45, "room_vnum": "3054", "room_flags": ["safe", "healing"],
        "hp": 1000, "max_hp": 1000, "affects": [],
        campaign._SOURCE_REVISION_KEY: "source-1",
    }


@pytest.mark.parametrize("flag,effect", [(AFF_HIDE, "detect hidden"), (AFF_INVISIBLE, "detect invis")])
def test_generic_hunt_requires_current_detection(flag, effect):
    world = WorldSource(mobiles={1: MobileSource(
        1, "target", "a target", 45, 0, 0, "test.are", affected_flags=flag,
    )})
    policy = replace(campaign._SOURCE_RANKED_HUNT_POLICY, source_mobile_vnums=(1,))
    observed = state()
    preparation = campaign._hunt_visibility_preparation_policy(policy, observed, world)
    assert preparation is not None
    assert preparation.execution != "source-ranked-hunt"
    observed["affects"] = [[{"name": effect, "duration": "10"}]]
    assert campaign._hunt_visibility_preparation_policy(policy, observed, world) is None


@pytest.mark.parametrize("duration,ready", [(0, False), (1, False), (2, True), (20, True), (-1, True), (None, True)])
def test_invisible_hidden_hunt_renews_short_detection(duration, ready):
    world = WorldSource(mobiles={1: MobileSource(
        1, "target", "a target", 45, 0, 0, "test.are",
        affected_flags=AFF_HIDE | AFF_INVISIBLE,
    )})
    policy = replace(campaign._SOURCE_RANKED_HUNT_POLICY, source_mobile_vnums=(1,))
    observed = state()
    detect_invis = {"name": "detect invis"}
    if duration is not None:
        detect_invis["duration"] = str(duration)
    observed["affects"] = [[
        {"name": "detect hidden", "duration": "11"}, detect_invis,
    ]]
    preparation = campaign._hunt_visibility_preparation_policy(policy, observed, world)
    if ready:
        assert preparation is None
    else:
        assert preparation.execution == "buy-see-invisible"


def test_detection_readiness_does_not_match_effect_prose():
    assert not campaign._has_route_ready_detect_invisibility([
        {"name": "other", "gives": "detect invis", "duration": "20"},
    ])


@pytest.mark.parametrize("duration,ready", [(0, False), (1, False), (2, True), (-1, True)])
def test_detection_shop_waits_at_healer_for_short_spell(duration, ready):
    policy = StarterPolicy(
        CharacterSpec.from_mapping({
            "name": "Tester", "race": "human", "gender": "male", "class": "warrior",
        }),
        "password", magic_shop_research=True, magic_shop_buy_see_invisible=True,
    )
    observed = CharacterState(
        room_vnum="3054", position=7,
        affects=[[{"name": "detect invis", "duration": str(duration)}]],
    )
    assert policy._magic_shop_research_decision(observed) is None
    assert policy.magic_shop_step == int(ready)
    assert policy.magic_shop_see_invisible_verified is ready
    assert not policy.failure


def test_short_detection_at_shop_does_not_waste_a_potion():
    policy = StarterPolicy(
        CharacterSpec.from_mapping({
            "name": "Tester", "race": "human", "gender": "male", "class": "warrior",
        }),
        "password", magic_shop_research=True, magic_shop_buy_see_invisible=True,
    )
    observed = CharacterState(
        room_vnum="3033", position=7,
        affects=[[{"name": "detect invis", "duration": "1"}]],
    )
    assert policy._magic_shop_see_invisible_shop_decision(observed) is None
    assert policy.magic_shop_see_invisible_step == 0
    assert not policy.magic_shop_see_invisible_verified
    assert not policy.failure


def test_visibility_capacity_keeps_pending_cleanup_despite_new_free_slot(monkeypatch):
    monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: 100.0)
    policy = StarterPolicy(
        CharacterSpec.from_mapping({
            "name": "Tester", "race": "human", "gender": "male", "class": "warrior",
        }), "password", magic_shop_research=True,
        magic_shop_buy_see_invisible=True, gear_catalog=GearCatalog({}),
    )
    policy.in_world = policy.prompt_ready = True
    observed = CharacterState(
        room_vnum="3054", room_flags=["healing"], position=7,
        stats={"carry_num": 39, "maxcarry_num": 40},
    )
    recovery = policy._recovery_session
    capacity = recovery.carrying_capacity
    recovery.required_loot_capacity_relief_limit = 1
    capacity.complete = False
    capacity.step, capacity.keyword, capacity.attempts = 1, "potpie", 1
    capacity.initial_count, capacity.maximum_count = 40, 40
    reply = recovery.loot_capacity_reply
    reply.begin("drop potpie", now=100.0)
    reply.observe("You drop a big pot pie.", now=100.0)
    handled, decision = policy._magic_shop_see_invisible_capacity_potion_decision(observed)
    assert handled and decision is None
    assert not capacity.complete
    assert reply.command == "drop potpie"

    reply.observe("\n", now=100.0)
    handled, decision = policy._magic_shop_see_invisible_capacity_potion_decision(observed)
    assert handled and decision.command == "sacrifice potpie"
    assert not capacity.complete
    reply.observe("You sacrifice a big pot pie to Brutus.\n", now=100.0)
    handled, decision = policy._magic_shop_see_invisible_capacity_potion_decision(observed)
    assert handled and decision.command == "inventory"
    reply.observe("Your backpack contains:\na water skin\nYou are carrying 39/40 items.\n", now=100.0)
    assert policy._magic_shop_see_invisible_capacity_potion_decision(observed) == (False, None)
    assert capacity.complete
    assert reply.command is None
    assert capacity.attempts == 1
    assert recovery.required_loot_capacity_relief_limit == 1


def test_existing_flight_does_not_skip_unprepared_detect_invisibility():
    policy = StarterPolicy(
        CharacterSpec.from_mapping({
            "name": "Tester", "race": "human", "gender": "male", "class": "warrior",
        }),
        "password", magic_shop_research=True, magic_shop_buy_fly=True,
        magic_shop_buy_see_invisible=True, magic_shop_continue_to_fastwalk=True,
        gear_catalog=GearCatalog({}),
    )
    policy.magic_shop_flight_snapshot_requested = True
    policy.fastwalk_required_loot_capacity_preflight_complete = True
    observed = CharacterState(
        level=1, room_vnum="3054", position=7,
        affects=[[{"name": "fly", "duration": "20"}]],
    )
    decision = policy._magic_shop_research_decision(observed)
    assert decision is not None
    assert decision.command == "south"
    assert not policy.magic_shop_see_invisible_verified
    assert policy.magic_shop_continue_to_fastwalk


def test_final_bound_circuit_prepares_hidden_sibling_without_rebinding_target():
    first, sibling = candidate(1), candidate(2)
    observed = state()
    record = campaign._source_ranked_candidate_record(first, character_level=45, source_revision="source-1")
    record["circuit"] = [campaign._source_ranked_candidate_record(
        sibling, character_level=45, source_revision="source-1",
    )]
    observed[campaign._SOURCE_RANKED_CANDIDATE_KEY] = record
    observed["campaign_source_resource_reserves"] = {"detect hidden": {"object_vnum": 4558}}
    runner = campaign.CampaignRunner.__new__(campaign.CampaignRunner)
    runner._source_world = WorldSource(mobiles={
        1: MobileSource(1, "target", "a target", 45, 0, 0, "test.are"),
        2: MobileSource(2, "other", "another target", 45, 0, 0, "test.are", affected_flags=AFF_HIDE),
    })
    runner._gear_catalog = GearCatalog({})
    policy = replace(campaign._SOURCE_RANKED_HUNT_POLICY, policy_id=campaign._source_ranked_policy_id(first, character_level=45))
    preparation = runner._prepare_hunt_visibility(observed, policy)
    assert preparation is not None
    assert preparation.execution == "return-home"
    assert observed[campaign._SOURCE_RANKED_CANDIDATE_KEY] is record


def carried_detection_plan():
    observed = state()
    item = ObjectSource(
        4558, "potion inky black", "an inky black potion", 10, (13, 0, 0, 0), 0,
        value_strings=("13", "detect hidden", "infravision", ""),
    )
    observed["inventory"] = [[{"short_desc": item.short_description, "quan": "1"}]]
    observed["campaign_source_resource_reserves"] = {"detect hidden": {
        "object_vnum": 4558, "object_description": "inky black potion",
        "mode": "potion", "command": "quaff", "command_keyword": "black",
        "spell": "detect hidden", "charges_remaining": 1, "consumes_object": True,
    }}
    target = candidate(1)
    observed[campaign._SOURCE_RANKED_CANDIDATE_KEY] = campaign._source_ranked_candidate_record(
        target, character_level=45, source_revision="source-1",
    )
    world = WorldSource(objects={4558: item}, mobiles={1: MobileSource(
        1, "target", "a target", 45, 0, 0, "test.are", affected_flags=AFF_HIDE,
    )})
    runner = campaign.CampaignRunner.__new__(campaign.CampaignRunner)
    runner._source_world = world
    runner._gear_catalog = GearCatalog(world.objects)
    runner.progress_callback = None
    policy = replace(campaign._SOURCE_RANKED_HUNT_POLICY,
                     policy_id=campaign._source_ranked_policy_id(target, character_level=45))
    return observed, runner, policy


@pytest.mark.parametrize("needs_invis", [False, True])
def test_carried_detection_continues_hunt_without_inventing_live_affect(needs_invis):
    observed, runner, policy = carried_detection_plan()
    if needs_invis:
        runner._source_world.mobiles[1] = replace(
            runner._source_world.mobiles[1], affected_flags=AFF_HIDE | AFF_INVISIBLE,
        )
    preparation = runner._prepare_hunt_visibility(observed, policy)
    if needs_invis:
        assert preparation.execution == "buy-see-invisible"
    else:
        assert preparation is None
    assert observed["affects"] == []
    assert observed["campaign_source_resource_reserves"]["detect hidden"]["charges_remaining"] == 1


@pytest.mark.parametrize("bad", [
    "empty", "unknown", "boolean_vnum", "wrong_mode", "wrong_command",
    "wrong_spell", "wrong_description", "not_consumable", "not_carried", "ambiguous",
    "wrong_keyword", "wrong_effect", "requires_hold",
])
def test_carried_detection_plan_requires_exact_source_and_inventory(bad):
    observed, runner, _policy = carried_detection_plan()
    record = observed["campaign_source_resource_reserves"]["detect hidden"]
    changes = {
        "empty": ("charges_remaining", 0), "unknown": ("object_vnum", 99999),
        "boolean_vnum": ("object_vnum", True), "wrong_mode": ("mode", "staff"),
        "wrong_command": ("command", "eat"), "wrong_spell": ("spell", "sanctuary"),
        "wrong_description": ("object_description", "another potion"),
        "not_consumable": ("consumes_object", False),
        "wrong_keyword": ("command_keyword", "quaff black\nsay unsafe"),
        "wrong_effect": ("effect", "sanctuary"), "requires_hold": ("requires_hold", True),
    }
    if bad in changes:
        key, value = changes[bad]
        record[key] = value
    elif bad == "not_carried":
        observed["inventory"] = []
    else:
        item = runner._source_world.objects[4558]
        runner._gear_catalog = GearCatalog({4558: item, 999: replace(item, vnum=999)})
    assert not campaign._carried_detect_hidden_preparation_available(
        observed, runner._source_world, runner._gear_catalog,
    )


def prepared_hunt():
    observed = state()
    observed["world_boot_id"] = "boot-1"
    observed["affects"] = [[{"name": "detect hidden", "duration": "10"}]]
    target = candidate(1)
    policy_id = campaign._source_ranked_policy_id(target, character_level=45)
    observed[campaign._SOURCE_RANKED_CANDIDATE_KEY] = campaign._source_ranked_candidate_record(
        target, character_level=45, source_revision="source-1",
    )
    observed["campaign_visibility_preparation_target"] = {
        "boot_id": "boot-1", "level": 45, "source_revision": "source-1",
        "policy_id": policy_id, "mobile_vnums": [1],
    }
    world = WorldSource(mobiles={1: MobileSource(
        1, "target", "a target", 45, 0, 0, "test.are", affected_flags=AFF_HIDE,
    )})
    return observed, target, policy_id, world


@pytest.mark.parametrize("mismatch", [None, "boot_id", "level", "source_revision", "policy_id", "status", "effect"])
def test_prepared_hunt_hint_requires_current_matching_visibility(mismatch):
    observed, _target, policy_id, world = prepared_hunt()
    if mismatch == "effect":
        observed["affects"] = []
    elif mismatch:
        observed["campaign_visibility_preparation_target"][mismatch] = (
            "dispatched" if mismatch == "status" else "different"
        )
    result = campaign._prepared_visibility_hunt_policy_id(observed, world)
    assert result == (policy_id if mismatch is None else None)


@pytest.mark.parametrize("accepted", [False, True])
def test_prepared_hunt_reenters_exact_selector_before_ordinary_search(monkeypatch, accepted):
    observed, target, policy_id, world = prepared_hunt()
    runner = campaign.CampaignRunner.__new__(campaign.CampaignRunner)
    runner._source_world = world
    runner._selected_source_ranked_circuit = ()
    runner._selected_source_ranked_candidate = None
    calls = []

    def select(_state, **kwargs):
        calls.append(kwargs.get("required_policy_id"))
        return target if accepted else None

    monkeypatch.setattr(runner, "_select_source_ranked_candidate_uncached", select)
    monkeypatch.setattr(runner, "_emit_progress", lambda _message: None)
    result = runner._select_source_ranked_candidate(observed)
    assert calls == ([policy_id] if accepted else [policy_id, None])
    assert result is (target if accepted else None)
    assert observed["campaign_visibility_preparation_target"]["status"] == (
        "selected" if accepted else "unavailable"
    )


@pytest.mark.parametrize("source_level,levels,expected", [
    (44, (42, 46), False),
    (45, (43, 47), True),
    (46, (44, 48), True),
    (50, (48, 52), True),
    (51, (49, 53), False),
])
def test_passive_lucky_consider_accounts_for_source_level_fuzz(source_level, levels, expected):
    target = replace(
        candidate(1), level=source_level, estimated_level_range=levels,
    )
    world = WorldSource(mobiles={1: MobileSource(
        1, "target", "a target", source_level, 0, 0, "test.are",
    )})
    assert campaign._source_ranked_passive_singleton_lucky_consider_allowed(
        target, character_level=45, source_world=world,
    ) is expected


@pytest.mark.parametrize("hazard", ["special", "program", "aggressive", "crowd"])
def test_passive_lucky_fuzz_does_not_relax_source_hazards(hazard):
    target = replace(candidate(1), estimated_level_range=(43, 47))
    mobile = MobileSource(1, "target", "a target", 45, 0, 0, "test.are")
    if hazard == "special":
        target = replace(target, specials=("spec_cast_psionicist",))
    elif hazard == "program":
        mobile = replace(mobile, programs=("greet_prog",))
    elif hazard == "aggressive":
        mobile = replace(mobile, act_flags=ACT_AGGRESSIVE)
    else:
        target = replace(target, source_spawn_limit=2)
    assert not campaign._source_ranked_passive_singleton_lucky_consider_allowed(
        target, character_level=45, source_world=WorldSource(mobiles={1: mobile}),
    )


@pytest.mark.parametrize("latest_lucky", [False, True])
@pytest.mark.parametrize("accepts_lucky", [False, True])
def test_lucky_repair_uses_newest_linked_visit_not_merged_list_order(latest_lucky, accepts_lucky):
    observed, target, policy_id, world = prepared_hunt()
    if accepts_lucky:
        target = replace(target, estimated_level_range=(43, 47))
    observed["campaign_research_results"] = {policy_id: {
        "boot_id": "boot-1", "observed": True, "consider_viable": False,
        "completed_kill": False, "viable": False,
    }}
    end = {
        "world_boot_id": "boot-1", "campaign_source_revision": "source-1",
        "dead": False, "in_combat": False,
    }
    segments = [{
        "id": identifier, "run_id": identifier, "phase": policy_id,
        "end_state_json": json.dumps(end),
    } for identifier in (20, 10)]
    calls = []

    class Events:
        def list_recent_events(self, run_id, *, limit):
            calls.append(run_id)
            assert limit == 512
            return [{
                "kind": "game_event", "payload_json": json.dumps({
                    "type": "room_listing_observed", "data": {"room_vnum": "100"},
                }),
            }, {
                "kind": "command", "payload_json": json.dumps({"command": "consider #1"}),
            }, {
                "kind": "response", "payload_json": json.dumps({"text": (
                    "A target says 'Do you feel lucky, punk?'. Also, he is much healthier than you."
                    if latest_lucky else "A target laughs at you mercilessly."
                )}),
            }]

    repaired = campaign._repair_source_ranked_lucky_consider_history(
        observed, segments, storage=Events(), source_world=world,
        ranked_candidates=(target,),
    )
    assert calls == [20]
    assert repaired["campaign_research_results"][policy_id]["consider_viable"] is (
        latest_lucky and accepts_lucky
    )


@pytest.mark.parametrize("negative_consider", [False, True])
def test_dispatch_preserves_fresh_plain_economic_route_but_not_negative_consider(monkeypatch, negative_consider):
    observed, target, policy_id, world = prepared_hunt()
    target = replace(target, status="reject", autonomy_rejections=(
        "an economic special mobile can reach the route",
    ))
    observed[campaign._SOURCE_RANKED_CANDIDATE_KEY] = campaign._source_ranked_candidate_record(
        target, character_level=45, source_revision="source-1",
    )
    observed["campaign_research_results"] = {policy_id: {
        "consider_viable": not negative_consider,
    }}
    runner = campaign.CampaignRunner.__new__(campaign.CampaignRunner)
    runner.segment_runner = None
    runner._source_world = world
    runner._selected_source_ranked_candidate = None
    runner._selected_source_ranked_circuit = ()
    runner._source_ranked_protection_retry_selected_policy_id = None
    monkeypatch.setattr(campaign, "_current_dd4_source_revision", lambda: "source-1")
    monkeypatch.setattr(campaign, "_source_ranked_mirror_realm_gardener_transit_allowed", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(runner, "_select_source_ranked_candidate", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(runner, "_select_ground_progression_fallback", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(runner, "_emit_progress", lambda _message: None)
    policy = replace(campaign._SOURCE_RANKED_HUNT_POLICY, policy_id=policy_id)
    result = runner._bind_source_ranked_policy_candidate(observed, policy)
    assert (result.execution == "source-ranked-hunt") is not negative_consider


@pytest.mark.parametrize("generic", [False, True])
def test_invisibility_purchase_failure_does_not_close_visible_registered_siblings(generic):
    world = WorldSource(mobiles={
        1: MobileSource(1, "target", "a target", 45, 0, 0, "test.are"),
        2: MobileSource(
            2, "other", "another target", 45, 0, 0, "test.are",
            affected_flags=AFF_INVISIBLE,
        ),
    })
    observed = state()
    observed[campaign._MAGIC_SHOP_SEE_INVISIBLE_FAILED_KEY] = True
    policy = replace(
        campaign._SOURCE_RANKED_HUNT_POLICY if generic
        else campaign._VAMPIRE_CATACOMBS_LEVEL_41_44_POLICY,
        source_mobile_vnums=(1, 2),
    )
    preparation = campaign._hunt_visibility_preparation_policy(policy, observed, world)
    assert preparation is not None
    if generic:
        assert preparation.execution is None
        assert preparation.source_mobile_vnums == (1, 2)
    else:
        assert preparation.execution == policy.execution
        assert preparation.source_mobile_vnums == (1,)


@pytest.mark.parametrize("carried", [False, True])
def test_blocked_invisibility_does_not_start_hidden_resource_loop(monkeypatch, carried):
    observed = state()
    observed[campaign._MAGIC_SHOP_SEE_INVISIBLE_FAILED_KEY] = True
    observed["campaign_source_resource_reserves"] = (
        {"detect hidden": {"object_vnum": 4558}} if carried else {}
    )
    runner = campaign.CampaignRunner.__new__(campaign.CampaignRunner)
    runner._source_world = WorldSource(mobiles={1: MobileSource(
        1, "target", "a target", 45, 0, 0, "test.are",
        affected_flags=AFF_HIDE | AFF_INVISIBLE,
    )})
    monkeypatch.setattr(campaign, "_select_source_consumable_candidate", lambda *_args, **_kwargs: pytest.fail(
        "must not acquire detection for a target with an unavailable independent prerequisite",
    ))
    preparation = runner._prepare_hunt_visibility(observed, replace(
        campaign._VAMPIRE_CATACOMBS_LEVEL_41_44_POLICY, source_mobile_vnums=(1,),
    ))
    assert preparation is not None
    assert preparation.execution is None
    assert preparation.status == "unavailable"


def test_expired_detection_does_not_record_absence():
    world = WorldSource(mobiles={1: MobileSource(
        1, "target", "a target", 45, 0, 0, "test.are", affected_flags=AFF_HIDE,
    )})
    stop = FieldHuntStop((), "a target", source_mobile_vnum=1, source_reset_room_vnum="100", source_policy_id="source-ranked-hunt-test-1-100-45")
    policy = StarterPolicy(
        CharacterSpec.from_mapping({
            "name": "Tester", "race": "human", "gender": "male", "class": "warrior",
        }),
        "password", source_world=world, fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(stop,),
    )
    policy.current_room = "100"
    decision = policy._fastwalk_hunt_plan_decision(CharacterState(
        level=45, room_vnum="100", hp=1000, max_hp=1000, position=7,
    ))
    assert decision is not None
    assert policy.fastwalk_abort_reason == "source detection prerequisite missing: detect hidden"
    assert not policy.fastwalk_target_absent
    assert not policy.fastwalk_source_absent_sightings


@pytest.mark.parametrize("command", ["flee", "recall"])
def test_withdrawal_keeps_exact_identity_until_xp_loss_arrives(command):
    stop = FieldHuntStop(
        (), "a target", source_mobile_vnum=1, source_reset_room_vnum="100",
        source_policy_id="source-ranked-hunt-test-1-100-45",
    )
    policy = StarterPolicy(
        CharacterSpec.from_mapping({
            "name": "Tester", "race": "human", "gender": "male", "class": "warrior",
        }),
        "password", fastwalk_route=route_named("ambush"), fastwalk_hunt_stops=(stop,),
    )
    policy.in_world = True
    policy.combat_active = True
    policy.active_target = "a target"
    policy.fastwalk_attack_target = "a target"
    policy.fastwalk_attack_started = True
    observed = CharacterState(
        level=45, room_vnum="100", hp=300, max_hp=1000, position=6,
        enemies=[[{"name": "a target", "isnpc": "1", "level": "45"}]],
    )
    policy.after_command(BotDecision(command, "withdraw at the own-health floor"), observed)
    assert policy._combat_session.pending_withdrawal is not None
    policy._combat_session.observe_xp_loss({"xp": 1405, "partial_xp": 966})
    assert policy._combat_session.source_losses[-1]["mobile_vnum"] == 1
    assert policy._combat_session.source_losses[-1]["partial_xp"] == 966
