import asyncio
from pathlib import Path

import dd4tester.campaign as campaign_module
import dd4tester.starter as starter_module

from dd4tester.character import CharacterSpec
from dd4tester.hunt_candidates import load_world_source, rank_hunt_candidates
from dd4tester.hunt_candidates import ITEM_STAFF, ObjectSource
from dd4tester.observations import GameEvent
from dd4tester.ota_arena import (
    OTA_ARENA_ENTRY_ROUTE,
    OTA_ARENA_EXIT_ROUTE,
    OTA_ARENA_TARGETS,
    ota_arena_token_terms_present,
)
from dd4tester.starter import StarterPolicy
from dd4tester.equipment import GearCatalog
from dd4tester.fastwalks import Fastwalk
from dd4tester.state import CharacterState


SOURCE = Path("runs/dd4-source/server/area")


def _spec() -> CharacterSpec:
    return CharacterSpec(
        name="ArenaTest",
        password_env="DD4TESTER_PASSWORD",
        host="localhost",
        port=4000,
        race="human",
        gender="neutral",
        character_class="warrior",
        subclass="knight",
        title="the Walking Bug Report",
        description="A careful test character.",
        timeout=2.0,
        max_commands=100,
        max_runtime=30.0,
        database=Path("runs/test-ota.sqlite3"),
        transcript_dir=Path("transcripts"),
    )


def test_ota_arena_plan_has_five_source_targets_and_exit_route() -> None:
    world = load_world_source(SOURCE, include_all_areas=True)

    assert len(OTA_ARENA_TARGETS) == 5
    assert OTA_ARENA_ENTRY_ROUTE[-1] == "south"
    assert OTA_ARENA_EXIT_ROUTE == (
        "east", "east", "south", "east", "east", "north"
    )
    for target in OTA_ARENA_TARGETS:
        mobile = world.mobiles[target.mobile_vnum]
        token = world.objects[target.token_vnum]
        assert target.room_vnum in {
            reset.room_vnum
            for reset in world.mob_resets
            if reset.mobile_vnum == target.mobile_vnum
        }
        assert any(
            term.casefold() in token.keywords.casefold()
            for term in target.token_terms[1:]
        )
        assert mobile.programs == ()

    gatekeeper = world.mobiles[27357]
    gate_program = next(
        program
        for program in gatekeeper.programs
        if program.trigger == "all_greet_prog"
    )
    favour_conditions = tuple(
        command
        for command in gate_program.commands
        if command.startswith("if carrying($n) == ")
    )
    assert favour_conditions == tuple(
        f"if carrying($n) == {target.token_vnum}"
        for target in OTA_ARENA_TARGETS
    )
    assert "mptransfer $n 27278" in gate_program.commands


def test_ota_arena_accepts_only_the_two_source_forced_transfers() -> None:
    world = load_world_source(SOURCE, include_all_areas=True)
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        ota_arena_research=True,
        source_world=world,
    )
    policy.fastwalk_route = object()  # proves the handoff clears the old route

    assert policy._ota_arena_forced_arrival(
        source_room_vnum="27243",
        destination_room_vnum="27227",
    )
    assert policy.ota_arena_stage == "target"
    assert policy.fastwalk_route is None
    assert not policy._ota_arena_forced_arrival(
        source_room_vnum="27243",
        destination_room_vnum="27228",
    )


def test_ota_arena_recovery_from_room_27225_uses_exact_first_route_step() -> None:
    world = load_world_source(SOURCE, include_all_areas=True)
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        ota_arena_research=True,
        ota_arena_start_in_circuit=True,
        source_world=world,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.ota_arena_where_observed = True

    decision = policy._ota_arena_decision(
        CharacterState(level=39, room_vnum="27225", room_name="Arena Floor")
    )

    assert decision is not None
    assert decision.command == "west"


def test_ota_arena_consider_requires_exact_live_source_identity() -> None:
    world = load_world_source(SOURCE, include_all_areas=True)
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        ota_arena_research=True,
        ota_arena_start_in_circuit=True,
        source_world=world,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.ota_arena_where_observed = True
    policy.enemy_snapshot_room = "27224"
    policy.enemy_snapshot_stale = False
    mobile = world.mobiles[27352]
    state = CharacterState(
        level=39,
        room_vnum="27224",
        room_name="Arena Floor",
        enemies=[
            [
                {
                    "name": mobile.short_description,
                    "long_desc": mobile.room_description,
                    "level": "40",
                    "isnpc": "27352",
                }
            ]
        ],
    )

    decision = policy._ota_arena_decision(state)

    assert decision is not None
    assert decision.command == "consider kaerl"
    assert policy.consider_target == mobile.short_description
    assert ota_arena_token_terms_present(
        ["a favour of the Kaer'l"], OTA_ARENA_TARGETS[0]
    )


def test_ota_arena_activates_sanctuary_before_shared_combat() -> None:
    world = load_world_source(SOURCE, include_all_areas=True)
    staff = ObjectSource(
        19173,
        "staff bard",
        "Staff of the Bard",
        ITEM_STAFF,
        (30, 10, 10, 0),
        0,
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        ota_arena_research=True,
        ota_arena_start_in_circuit=True,
        source_world=world,
        gear_catalog=GearCatalog({staff.vnum: staff}),
        verified_source_resources={
            "sanctuary": {
                "effect": "sanctuary",
                "object_vnum": staff.vnum,
                "object_description": "Staff of the Bard",
                "spell": "sanctuary",
                "command": "brandish",
                "mode": "staff",
                "requires_hold": True,
                "consumes_object": False,
                "consumes_charge": True,
                "command_keyword": "bard",
                "charges_remaining": 9,
            }
        },
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.ota_arena_where_observed = True
    policy.enemy_snapshot_room = "27224"
    policy.enemy_snapshot_stale = False
    policy.consider_target = "a Kaer'l gladiator"
    policy.consider_target_selector = "#15776"
    policy.consider_viable = True
    state = CharacterState(
        level=39,
        room_vnum="27224",
        room_name="Arena Floor",
        hp=927,
        max_hp=927,
        mana=531,
        max_mana=531,
        position=7,
        inventory=[{"quan": 1, "short_desc": "Staff of the Bard"}],
        affects=[],
        enemies=[[
            {
                "name": "a Kaer'l gladiator",
                    "long_desc": world.mobiles[27352].room_description,
                "level": "39",
                "hp": "1426",
                "maxhp": "1488",
                "isnpc": "27352",
                    "selector": "#15776",
            }
        ]],
    )

    hold = policy._ota_arena_decision(state)
    assert hold is not None
    assert hold.command == "hold bard"
    assert policy.combat_active is False

    policy.observe_text("You hold Staff of the Bard.")
    assert policy._gear_decision(state) is None
    brandish = policy._ota_arena_decision(state)
    assert brandish is not None
    assert brandish.command == "brandish"
    assert policy.combat_active is False
    assert policy._gear_decision(state) is None

    policy.observe_text("You brandish the Staff of the Bard.")
    assert policy.source_resource_effect_acknowledged == "sanctuary"
    assert policy._ota_arena_decision(state) is None
    active = policy._ota_arena_decision(
        CharacterState(**{**state.__dict__, "affects": [{"name": "sanctuary"}]})
    )
    assert active is not None
    assert active.command == "kill #15776"
    assert policy.combat_active is True


def test_ota_arena_uses_bounded_no_reserve_fallback_inside_circuit() -> None:
    world = load_world_source(SOURCE, include_all_areas=True)
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        ota_arena_research=True,
        ota_arena_start_in_circuit=True,
        ota_arena_allow_unprotected_fallback=True,
        source_world=world,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.ota_arena_where_observed = True
    policy.enemy_snapshot_room = "27224"
    policy.enemy_snapshot_stale = False
    policy.consider_target = "a Kaer'l gladiator"
    policy.consider_target_selector = "#15776"
    policy.consider_viable = True
    state = CharacterState(
        level=39,
        room_vnum="27224",
        room_name="Arena Floor",
        hp=927,
        max_hp=927,
        mana=531,
        max_mana=531,
        position=7,
        inventory=[],
        affects=[],
        enemies=[[
            {
                "name": "a Kaer'l gladiator",
                "long_desc": world.mobiles[27352].room_description,
                "level": "40",
                "hp": "1426",
                "maxhp": "1488",
                "isnpc": "27352",
                "selector": "#15776",
            }
        ]],
    )

    decision = policy._ota_arena_decision(state)

    assert decision is not None
    assert decision.command == "kill #15776"
    assert policy.combat_active is True
    assert any(
        "no-reserve health gate" in marker
        for marker in policy.fastwalk_route_hazards
    )


def test_ota_arena_can_refresh_sanctuary_during_the_same_fight() -> None:
    world = load_world_source(SOURCE, include_all_areas=True)
    staff = ObjectSource(
        19173,
        "staff bard",
        "Staff of the Bard",
        ITEM_STAFF,
        (30, 10, 10, 0),
        0,
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        ota_arena_research=True,
        ota_arena_start_in_circuit=True,
        source_world=world,
        gear_catalog=GearCatalog({staff.vnum: staff}),
        verified_source_resources={
            "sanctuary": {
                "effect": "sanctuary",
                "object_vnum": staff.vnum,
                "object_description": "Staff of the Bard",
                "spell": "sanctuary",
                "command": "brandish",
                "mode": "staff",
                "requires_hold": True,
                "consumes_object": False,
                "consumes_charge": True,
                "command_keyword": "bard",
                "charges_remaining": 2,
            }
        },
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.ota_arena_stage = "target"
    policy.combat_active = True
    policy.active_target = "a Kaer'l gladiator"
    policy.active_target_selector = "#15776"
    policy.active_target_mobile_vnum = 27352
    policy.sanctuary_potion_target = "a kaer'l gladiator"
    state = CharacterState(
        level=39,
        room_vnum="27224",
        room_name="Arena Floor",
        hp=700,
        max_hp=927,
        mana=400,
        max_mana=531,
        position=7,
        in_combat=True,
        combat_target="a Kaer'l gladiator",
        inventory=[{"quan": 1, "short_desc": "Staff of the Bard"}],
        affects=[],
    )

    hold = policy._combat_pouch_potion_decision(state)
    assert hold is not None
    assert hold.command == "hold bard"

    policy.observe_text("You hold Staff of the Bard.")
    brandish = policy._combat_pouch_potion_decision(state)
    assert brandish is not None
    assert brandish.command == "brandish"

    policy.observe_text("You brandish the Staff of the Bard.")
    policy.source_resource_effect_snapshot_requested = True
    policy.observe_events(
        [GameEvent("affects_changed", "gmcp", {"value": [[]]})],
        state,
    )
    assert policy.source_resource_effect_acknowledged is None
    assert "sanctuary" not in policy.failed_source_resource_effects

    refresh_hold = policy._combat_pouch_potion_decision(state)
    assert refresh_hold is not None
    assert refresh_hold.command == "hold bard"


def test_ota_arena_combat_is_not_classified_as_magic_shop_utility() -> None:
    world = load_world_source(SOURCE, include_all_areas=True)
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        ota_arena_research=True,
        ota_arena_start_in_circuit=True,
        magic_shop_research=True,
        source_world=world,
    )

    assert policy._is_noncombat_utility_run is False


def test_ota_arena_exit_is_gated_until_all_five_favours_are_receipted() -> None:
    world = load_world_source(SOURCE, include_all_areas=True)
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        ota_arena_research=True,
        source_world=world,
    )
    policy.ota_arena_stage = "exit"
    policy.ota_arena_target_index = len(OTA_ARENA_TARGETS)
    policy.ota_arena_token_receipts = [
        {"token_vnum": target.token_vnum}
        for target in OTA_ARENA_TARGETS[:-1]
    ]
    state = CharacterState(
        level=39,
        room_vnum="27240",
        room_name="Ota'ar Dar Arena Floor Entrance/Exit",
        room_flags=["no_recall"],
    )

    assert policy._ota_arena_favours_incomplete(state) is True
    assert policy._arena_completion_route_decision(state) is None
    assert policy._arena_exit_decision(state, "leave").command == "look"


def test_ota_arena_policy_failure_cannot_release_a_captive_without_favours() -> None:
    world = load_world_source(SOURCE, include_all_areas=True)
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        ota_arena_research=True,
        ota_arena_start_in_circuit=True,
        source_world=world,
    )
    policy.return_home = True
    policy.ota_arena_stage = "target"
    state = CharacterState(
        level=39,
        room_vnum="27240",
        room_name="Ota'ar Dar Arena Floor Entrance/Exit",
        room_flags=["no_recall"],
    )

    decision = policy._ota_arena_abort_decision(
        state,
        "the exact gladiator target was not visible",
    )

    assert decision is not None
    assert decision.command == "look"
    assert policy.ota_arena_research is True
    assert policy.ota_arena_stage == "target"
    assert policy.return_home is False
    assert policy.deferred_failure is None
    assert policy._ota_arena_favours_incomplete(state) is True
    assert any(
        marker.startswith("arena captive hold:")
        for marker in policy.fastwalk_route_hazards
    )


def test_ota_arena_adopts_generic_route_when_gladiators_still_hold_the_gate() -> None:
    world = load_world_source(SOURCE, include_all_areas=True)
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        source_world=world,
        title_configured=True,
        description_configured=True,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.return_home = True
    policy.done = True
    state = CharacterState(
        level=39,
        room_vnum="27240",
        room_name="Ota'ar Dar Arena Floor Entrance/Exit",
        room_flags=["no_recall"],
    )

    assert policy._ota_arena_favours_incomplete(state) is True
    decision = policy.next_decision(state)
    assert decision is not None
    assert decision.command == "where kaerl"
    assert policy.ota_arena_research is True
    assert policy.ota_arena_stage == "target"
    assert policy.ota_arena_target_index == 0
    assert policy.done is False
    assert policy.return_home is False
    assert policy._ota_arena_all_favours_collected() is False


def test_ota_arena_ignores_favour_receipts_from_an_old_reboot() -> None:
    world = load_world_source(SOURCE, include_all_areas=True)
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        ota_arena_research=True,
        source_world=world,
    )
    policy.world_boot_id = "boot-current"
    policy.ota_arena_stage = "exit"
    policy.ota_arena_target_index = len(OTA_ARENA_TARGETS)
    policy.ota_arena_token_receipts = [
        {"token_vnum": target.token_vnum, "boot_id": "boot-old"}
        for target in OTA_ARENA_TARGETS
    ]
    state = CharacterState(
        level=39,
        room_vnum="27240",
        room_name="Ota'ar Dar Arena Floor Entrance/Exit",
        room_flags=["no_recall"],
    )

    assert policy._ota_arena_favours_incomplete(state) is True
    assert policy._ota_arena_all_favours_collected() is False
    assert policy._arena_exit_decision(state, "leave").command == "look"


def test_ota_arena_thirst_does_not_force_exit_during_favour_combat() -> None:
    world = load_world_source(SOURCE, include_all_areas=True)
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        ota_arena_research=True,
        ota_arena_start_in_circuit=True,
        source_world=world,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.ota_arena_where_observed = True
    policy.combat_active = True
    policy.active_target = "a Kaer'l gladiator"
    policy.active_target_selector = "#15776"
    policy.active_target_level = 39
    policy.active_target_mobile_vnum = 27352
    policy.needs_drink = True
    policy.return_home = False
    state = CharacterState(
        level=39,
        room_vnum="27224",
        room_name="Arena Floor",
        hp=900,
        max_hp=927,
        mana=500,
        max_mana=531,
        move=500,
        max_move=583,
        position=7,
        in_combat=True,
        combat_target="a Kaer'l gladiator",
        affects=[{"name": "sanctuary"}],
        enemies=[[
            {
                "name": "a Kaer'l gladiator",
                "level": "39",
                "isnpc": "27352",
                "selector": "#15776",
            }
        ]],
    )

    decision = policy.next_decision(state)

    assert decision is None or decision.command not in {"flee", "recall", "up"}


def test_ota_arena_recovers_in_place_before_the_next_favour() -> None:
    world = load_world_source(SOURCE, include_all_areas=True)
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        ota_arena_research=True,
        ota_arena_start_in_circuit=True,
        source_world=world,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.ota_arena_where_observed = True
    state = CharacterState(
        level=39,
        room_vnum="27224",
        room_name="Arena Floor",
        hp=300,
        max_hp=927,
        position=7,
    )

    decision = policy._ota_arena_decision(state)

    assert decision is not None
    assert decision.command == "sleep"


def test_ota_arena_hands_active_combat_to_shared_controller() -> None:
    world = load_world_source(SOURCE, include_all_areas=True)
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        ota_arena_research=True,
        ota_arena_start_in_circuit=True,
        source_world=world,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.ota_arena_where_observed = True
    policy.combat_active = True

    decision = policy._ota_arena_decision(
        CharacterState(
            level=39,
            room_vnum="27224",
            room_name="Arena Floor",
            in_combat=True,
            combat_target="a Kaer'l gladiator",
        )
    )

    assert decision is None


def test_ota_arena_in_circuit_resume_reenters_from_healer_when_outside() -> None:
    world = load_world_source(SOURCE, include_all_areas=True)
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        ota_arena_research=True,
        ota_arena_start_in_circuit=True,
        fastwalk_route=Fastwalk(
            name="ota-arena-entry",
            minimum_level=1,
            maximum_level=100,
            notation="south",
            route_origin_room_vnum=3001,
        ),
        source_world=world,
    )
    policy.in_world = True
    policy.prompt_ready = True

    decision = policy._ota_arena_decision(
        CharacterState(level=39, room_vnum="3054", room_name="By the Temple Altar")
    )

    assert decision is None
    assert policy.ota_arena_stage == "entry"


def test_ota_arena_return_home_does_not_plan_from_healer() -> None:
    world = load_world_source(SOURCE, include_all_areas=True)
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        ota_arena_research=True,
        ota_arena_start_in_circuit=True,
        source_world=world,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.return_home = True

    decision = policy._ota_arena_decision(
        CharacterState(level=39, room_vnum="3054", room_name="Healer's Room")
    )

    assert decision is None
    assert policy.fastwalk_abort_reason is None


def test_ota_arena_reconnect_accepts_live_water_breathing_affect() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        magic_shop_research=True,
        magic_shop_buy_water_breathing=True,
    )
    policy.in_world = True

    policy.next_decision(
        CharacterState(
            level=39,
            room_vnum="27225",
            room_name="Arena Floor",
            affects=[{"name": "breathe water", "duration": "11"}],
        )
    )

    assert policy.magic_shop_water_breathing_verified is True
    assert policy.magic_shop_water_breathing_step == 8


def test_ota_arena_in_circuit_resume_transfers_route_ownership_inside() -> None:
    world = load_world_source(SOURCE, include_all_areas=True)
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        ota_arena_research=True,
        ota_arena_start_in_circuit=True,
        fastwalk_route=Fastwalk(
            name="ota-arena-entry",
            minimum_level=1,
            maximum_level=100,
            notation="south",
            route_origin_room_vnum=3001,
        ),
        source_world=world,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.ota_arena_where_observed = True

    policy._ota_arena_decision(
        CharacterState(level=39, room_vnum="27224", room_name="Arena Floor")
    )

    assert policy.fastwalk_route is None


def test_ota_arena_profile_prepares_water_breathing_before_entry(monkeypatch) -> None:
    captured = {}

    class FakeRunner:
        def __init__(self, *args, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return "fake-result"

    monkeypatch.setattr(starter_module, "load_character_spec", lambda path: _spec())
    monkeypatch.setattr(starter_module, "load_world_source", lambda *args, **kwargs: object())
    monkeypatch.setattr(starter_module, "current_source_directory", lambda: SOURCE)
    monkeypatch.setattr(starter_module, "StarterBotRunner", FakeRunner)

    result = asyncio.run(
        starter_module.run_ota_arena_research_profile("dorrik.yaml")
    )

    assert result == "fake-result"
    assert captured["magic_shop_research"] is True
    assert captured["magic_shop_buy_fly"] is False
    assert captured["magic_shop_buy_water_breathing"] is True
    assert captured["magic_shop_continue_to_fastwalk"] is True
    assert captured["allow_bounded_city_shop_transit"] is True
    assert captured["verified_source_resources"]["sanctuary"] == {
        "effect": "sanctuary",
        "object_vnum": 19173,
        "object_description": "Staff of the Bard",
        "spell": "sanctuary",
        "command": "brandish",
        "mode": "staff",
        "requires_hold": True,
        "consumes_object": False,
        "consumes_charge": True,
        "command_keyword": "bard",
        "charges_remaining": 10,
    }
    assert captured["fastwalk_route"].recall_after_loot is True


def _arena_campaign_candidate(world):
    raw = next(
        candidate
        for candidate in rank_hunt_candidates(
            world,
            character_level=39,
            include_xp_only=True,
            include_below_band=False,
            character_max_hp=937,
            character_alignment=1000,
            include_level_ceiling_candidates=True,
            level_ceiling_offset=5,
            include_all_areas=True,
        )
        if candidate.mobile_vnum == 27358 and candidate.room_vnum == 27278
    )
    return campaign_module._source_ranked_ota_arena_candidate(
        raw,
        world,
        {
            "currencies": {
                "platinum": 0,
                "gold": 1,
                "silver": 0,
                "copper": 0,
            }
        },
        character_level=39,
    )


def _arena_revalidation_state(policy_id: str) -> dict:
    return {
        "level": 39,
        "max_hp": 937,
        "hp": 937,
        "room_vnum": "3054",
        "world_boot_id": "boot-current",
        "campaign_source_revision": "test-source",
        "character_class": "warrior",
        "subclass": "knight",
        "alignment": 1000,
        "currencies": {
            "platinum": 0,
            "gold": 1,
            "silver": 0,
            "copper": 0,
        },
        "affects": [{"name": "fly"}],
        # Other same-boot hunts have losses.  The arena repair is still
        # eligible because its own exact policy has no loss record.
        "xp_loss_observed": True,
        "campaign_xp_loss_total": 140848,
        "xp_loss_total": 1000,
        "campaign_source_ranked_retry_exhausted_policy": policy_id,
        "campaign_source_ranked_retry_exhausted_boot": "boot-current",
        "campaign_research_results": {
            policy_id: {
                "boot_id": "boot-current",
                "fatal_failure": True,
                "observed": True,
                "completed_kill": False,
                "viable": False,
            }
        },
    }


def test_ota_arena_favour_gate_revalidation_is_one_shot() -> None:
    world = load_world_source(SOURCE, include_all_areas=True)
    candidate = _arena_campaign_candidate(world)
    policy_id = campaign_module._source_ranked_policy_id(
        candidate,
        character_level=39,
    )
    state = _arena_revalidation_state(policy_id)

    receipt = campaign_module._source_ranked_ota_arena_favour_gate_revalidation_receipt(
        candidate,
        state,
        character_level=39,
        source_world=world,
    )

    assert receipt is not None
    assert receipt["revision"] == campaign_module._OTAAR_ARENA_FAVOUR_GATE_REVALIDATION_REVISION
    assert receipt["status"] == "pending"
    state[campaign_module._OTAAR_ARENA_FAVOUR_GATE_REVALIDATION_KEY] = receipt
    assert (
        campaign_module._source_ranked_candidate_blocked_by_protection_recovery(
            candidate,
            state,
            character_level=39,
            character_max_hp=937,
            source_world=world,
        )
        is False
    )

    state[campaign_module._OTAAR_ARENA_FAVOUR_GATE_REVALIDATION_KEY] = {
        **receipt,
        "status": "attempted",
        "attempted": True,
    }
    assert (
        campaign_module._source_ranked_candidate_blocked_by_protection_recovery(
            candidate,
            state,
            character_level=39,
            character_max_hp=937,
            source_world=world,
        )
        is True
    )


def test_ota_arena_favour_gate_revalidation_closes_without_a_kill() -> None:
    world = load_world_source(SOURCE, include_all_areas=True)
    candidate = _arena_campaign_candidate(world)
    policy_id = campaign_module._source_ranked_policy_id(
        candidate,
        character_level=39,
    )
    state = _arena_revalidation_state(policy_id)
    receipt = campaign_module._source_ranked_ota_arena_favour_gate_revalidation_receipt(
        candidate,
        state,
        character_level=39,
        source_world=world,
    )
    assert receipt is not None
    previous = {
        **state,
        campaign_module._OTAAR_ARENA_FAVOUR_GATE_REVALIDATION_KEY: {
            **receipt,
            "status": "attempted",
            "attempted": True,
        },
    }
    current = {
        **state,
        "campaign_objective_kills": [],
    }

    merged = campaign_module._campaign_segment_end_state(
        previous,
        current,
        execution="source-ranked-hunt",
        policy_id=policy_id,
    )

    marker = merged[campaign_module._OTAAR_ARENA_FAVOUR_GATE_REVALIDATION_KEY]
    assert marker["status"] == "closed"
    assert marker["outcome"] == "no_kill"


def test_ota_arena_allows_only_the_bounded_old_higue_transit_fight() -> None:
    world = load_world_source(SOURCE, include_all_areas=True)
    mobile = world.mobiles[27106]
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=Fastwalk(
            "source-ranked Ota'ar arena favour circuit",
            1,
            100,
            "south",
            route_bounded_transit_special_mobile_vnums=(27106,),
            route_bounded_transit_special_room_vnums=("27148",),
        ),
    )
    policy.source_world = world
    policy.current_room = "27148"
    state = CharacterState(
        level=39,
        hp=937,
        max_hp=937,
        room_vnum="27148",
        enemies=[[{
            "name": mobile.short_description,
            "level": "29",
            "isnpc": "27106",
            "long_desc": mobile.room_description,
        }]],
    )

    enemies = policy._current_room_enemy_records(state)
    assert policy._source_mobile_route_transit_special_is_bounded(
        enemies[0], state
    )
    assert policy._source_plain_transit_attacker_is_admitted(state, enemies)

    state.hp = 187
    assert not policy._source_mobile_route_transit_special_is_bounded(
        enemies[0], state
    )

    state.hp = 937
    state.enemies[0][0]["isnpc"] = "27115"
    assert not policy._source_plain_transit_attacker_is_admitted(
        state,
        policy._current_room_enemy_records(state),
    )


def test_ota_arena_special_transit_bypasses_early_route_hazard_dispatch() -> None:
    world = load_world_source(SOURCE, include_all_areas=True)
    mobile = world.mobiles[27106]
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=Fastwalk(
            "source-ranked Ota'ar arena favour circuit",
            1,
            100,
            "south",
            route_hard_hazard_targets=("Old Higue",),
            route_bounded_transit_special_mobile_vnums=(27106,),
            route_bounded_transit_special_room_vnums=("27134",),
        ),
        source_world=world,
        title_configured=True,
        description_configured=True,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.current_room = "27134"
    state = CharacterState(
        level=39,
        hp=937,
        max_hp=937,
        mana=531,
        max_mana=531,
        move=539,
        max_move=583,
        position=7,
        area="Shadowsea",
        room_vnum="27134",
        room_flags=["no_recall"],
        enemies=[[{
            "name": mobile.short_description,
            "level": "29",
            "hp": "650",
            "maxhp": "650",
            "isnpc": "27106",
            "long_desc": mobile.room_description,
        }]],
    )

    decision = policy.next_decision(state)

    assert decision is None
    assert policy.fastwalk_abort_reason is None
    assert policy.fastwalk_plain_transit_fight_active is True
    assert policy.active_target == mobile.short_description
