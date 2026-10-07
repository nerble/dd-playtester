from dataclasses import replace

import pytest

from dd4tester.excavation import (
    DigObservation, HoardDigSession, identify_hoard_trap_effect,
    maximum_hoard_direct_damage, shop_digger_level_bounds,
    tool_dig_budget,
)
from dd4tester.hunt_candidates import ITEM_DONOT_RANDOMISE, ObjectSource


SHOVEL = ObjectSource(3604, "shovel", "a shovel", 6, (25, 16, 39, 83), 0)
PROMPT = "<666/666 hits 261/261 mana 482/482 move [Plains]> "
IDENTITY = (10001, 309, 586)


def budget(**changes):
    options = dict(
        sector_type=2, race="dwarf", level=29, observed_tool_level=10,
        strength=30, constitution=25, dexterity=16, swiftness=5,
        enhanced_swiftness_percent=0,
    )
    options.update(changes)
    return tool_dig_budget(SHOVEL, **options)


def observed(**changes):
    return replace(DigObservation(1, IDENTITY, 309, 3604, 666, 482, False, 0, True, True, budget()), **changes)


def session():
    return HoardDigSession(budget(), quest_identity=IDENTITY, minimum_hp=400, return_movement=30)


def unearthed_session():
    digging = session()
    assert digging.poll(observed(), now=0).command == "dig"
    digging.observe("With a final effortful thrust, you unearth something!" + PROMPT)
    assert digging.poll(observed(sequence=2), now=4).status == "unearthed"
    return digging


def listed(sequence=4, description="a coin of Serenos"):
    return {
        "room_vnum": str(IDENTITY[1]),
        "sequence": 1,
        "state_revision": sequence,
        "render_complete": True,
        "targeted_lines": [
            {"target_id": "58601", "description": description},
        ],
        "unkeyed_lines": [],
    }


def inventory(quantity=0, description="a coin of Serenos"):
    items = [] if quantity == 0 else [{
        "quan": str(quantity), "short_desc": description,
    }]
    return [[items]]


@pytest.mark.parametrize("sector,digs,movement", [(2, 5, 184), (0, 8, 946), (1, 9, 1224)])
def test_tool_budget_includes_load_and_use_fuzz(sector, digs, movement):
    result = budget(sector_type=sector)
    assert result.maximum_digs == digs
    assert result.maximum_dig_commands == digs + 3
    assert result.maximum_movement == movement
    assert result.maximum_wait_seconds == result.maximum_wait_pulses / 4


def test_shop_digger_level_bound_accounts_for_stock_fuzz_and_buy_clone():
    spade = ObjectSource(
        3393, "spade", "a spade", 6, (36, 3, 9, 160), 100,
        level=1,
    )
    assert shop_digger_level_bounds(spade) == (1, 2)

    result = tool_dig_budget(
        spade, sector_type=1, race="dwarf", level=29,
        observed_tool_level=None, source_tool_level_bounds=(1, 2),
        strength=30, constitution=25, dexterity=16, swiftness=5,
        enhanced_swiftness_percent=0,
    )
    assert result.tool_vnum == 3393

    with pytest.raises(ValueError, match="maximum level is usable"):
        tool_dig_budget(
            spade, sector_type=1, race="dwarf", level=1,
            observed_tool_level=None, source_tool_level_bounds=(1, 2),
            strength=30, constitution=25, dexterity=16, swiftness=5,
            enhanced_swiftness_percent=0,
        )


def test_non_randomized_shop_digger_has_exact_prototype_level():
    tool = ObjectSource(
        3604, "shovel", "a shovel", 6, (25, 16, 39, 83), 0,
        level=25, extra_flags=ITEM_DONOT_RANDOMISE,
    )
    assert shop_digger_level_bounds(tool) == (25, 25)


@pytest.mark.parametrize("changes", [
    {"sector_type": 6}, {"sector_type": 9}, {"sector_type": 13},
    {"swiftness": 50000}, {"swiftness": None}, {"strength": True},
    {"observed_tool_level": 30}, {"dexterity": 32}, {"constitution": 0},
    {"depth": 201},
    {"enhanced_swiftness_percent": None}, {"enhanced_swiftness_percent": 101},
])
def test_unknown_or_illegal_digging_inputs_are_not_estimates(changes):
    with pytest.raises(ValueError):
        budget(**changes)


def test_race_affects_budget_and_slow_is_applied_after_racial_wait_bonus():
    dwarf = budget(sector_type=0)
    human = budget(sector_type=0, race="human")
    assert dwarf.maximum_movement < human.maximum_movement
    assert dwarf.maximum_digs < human.maximum_digs
    assert budget(sector_type=0, slow=True).maximum_wait_pulses > dwarf.maximum_wait_pulses
    assert budget(sector_type=0, haste=True).maximum_wait_pulses < dwarf.maximum_wait_pulses


def test_room_wide_physical_trap_uses_full_positive_armor_class():
    assert maximum_hoard_direct_damage(29, 100) == 390
    assert maximum_hoard_direct_damage(29, -17) == 286
    assert maximum_hoard_direct_damage(29, -1000) == 174
    with pytest.raises(ValueError):
        maximum_hoard_direct_damage(29, 50000)


@pytest.mark.parametrize(("kind", "message"), [
    ("fire", "A fireball shoots out of the hoard and hits you!"),
    ("cold", "A blast of frost from the hoard hits you!"),
    ("acid", "A blast of acid erupts from the hoard, burning your skin!"),
    ("energy", "A pulse of energy from the hoard zaps you!"),
    ("blunt", "You are hit by a blunt object from the hoard!"),
    ("pierce", "You set off a trap and are pierced through the chest!"),
    ("slash", "You just got slashed by a trap!"),
    ("poison", "You are struck by a small dart... your blood begins to burn!"),
    ("snare", "You are entangled in a snare--you cannot move!"),
    ("curse", "You feel unclean."),
    ("hex", "You feel unbelievably dirty."),
    ("spirit", "{CA furious spirit guardian materialises from thin air!{x"),
])
def test_identifies_source_emitted_hoard_trap_effects(kind, message):
    assert identify_hoard_trap_effect("You hear a strange noise...\n" + message) == kind


def test_trap_effect_message_without_trigger_is_not_hoard_evidence():
    assert identify_hoard_trap_effect("You feel unclean.") is None


def test_ambiguous_trap_response_is_not_misclassified():
    response = (
        "You hear a strange noise...\n"
        "You are struck by a small dart...\n"
        "A furious spirit guardian materialises from thin air!"
    )
    assert identify_hoard_trap_effect(response) is None


def test_unidentified_trap_stops_without_granting_recovery_permission():
    digging = session()
    assert digging.poll(observed(), now=0).command == "dig"
    digging.observe("You hear a strange noise...\nAn unfamiliar effect occurs." + PROMPT)

    step = digging.poll(observed(sequence=2), now=2)

    assert step.status == "stopped"
    assert step.trap_kind == "unknown"
    assert digging.confirm_trap_recovery(
        observed(sequence=3, trap_recovery_verified=True),
    ).status == "stopped"
    assert digging.audit()["trap_effects"] == ((2, "unknown"),)


def test_wire_swiftness_already_contains_dex_and_skill_bonus():
    skilled = budget(sector_type=0, dexterity=30, swiftness=25, enhanced_swiftness_percent=80)
    unskilled = budget(sector_type=0, dexterity=30, swiftness=5)
    assert skilled.maximum_wait_pulses == unskilled.maximum_wait_pulses == 18


def test_dig_is_response_driven_and_unearthing_does_not_claim_pickup():
    digging = session()
    assert digging.poll(observed(), now=0).command == "dig"
    digging.observe("You dig into the earth with a shovel...")
    assert digging.poll(observed(sequence=2, movement=459), now=2).command is None
    digging.observe(PROMPT)
    assert digging.poll(observed(sequence=2, movement=459), now=2).command == "dig"
    digging.observe(PROMPT + "With a final effortful thrust, you unearth something!" + PROMPT)
    assert digging.poll(observed(sequence=3, movement=436), now=4).status == "unearthed"
    assert digging.commands == 2
    assert digging.poll(observed(sequence=4), now=20).command is None


def test_quest_object_pickup_uses_room_selector_and_inventory_quantity_delta():
    digging = unearthed_session()
    pending = digging.prepare_quest_object_pickup(
        sequence=4,
        quest_object_vnum=IDENTITY[2],
        source_object_description="a coin of Serenos",
        source_description_vnums=(IDENTITY[2],),
        current_room_vnum=IDENTITY[1],
        room_listing=listed(),
        inventory_items=inventory(2),
    )
    acquired = digging.confirm_quest_object_acquired(
        sequence=5,
        quest_object_vnum=IDENTITY[2],
        source_object_description="a coin of Serenos",
        source_description_vnums=(IDENTITY[2],),
        inventory_items=inventory(3),
    )

    assert pending.status == "pickup_pending"
    assert pending.command == "get #58601"
    assert acquired.status == "object_acquired"
    assert digging.audit()["quest_object_acquired"] is True
    assert digging.audit()["quest_object_selector"] == "#58601"
    assert digging.audit()["quest_object_baseline_count"] == 2


@pytest.mark.parametrize(
    ("quest_object_vnum", "source_description_vnums", "description", "lines", "inventory_items"),
    [
        (1777, (1777,), "a coin of Serenos", [{"target_id": "58601", "description": "a coin of Serenos"}], inventory()),
        (586, (586, 587), "a coin of Serenos", [{"target_id": "58601", "description": "a coin of Serenos"}], inventory()),
        (586, (586,), "a silver coin", [{"target_id": "58601", "description": "a silver coin"}], inventory()),
        (586, (586,), "a coin of Serenos", [], inventory()),
        (586, (586,), "a coin of Serenos", [{"target_id": "0", "description": "a coin of Serenos"}], inventory()),
        (586, (586,), "a coin of Serenos", [
            {"target_id": "58601", "description": "a coin of Serenos"},
            {"target_id": "58602", "description": "a coin of Serenos"},
        ], inventory()),
        (586, (586,), "a coin of Serenos", [{"target_id": "58601", "description": "a coin of Serenos"}], [[{"short_desc": "a coin of Serenos"}]]),
    ],
)
def test_quest_object_acquisition_rejects_wrong_or_missing_evidence(
    quest_object_vnum, source_description_vnums, description, lines, inventory_items,
):
    digging = unearthed_session()

    room_listing = listed(sequence=4, description=description)
    room_listing["targeted_lines"] = lines
    step = digging.prepare_quest_object_pickup(
        sequence=4,
        quest_object_vnum=quest_object_vnum,
        source_object_description="a coin of Serenos",
        source_description_vnums=source_description_vnums,
        current_room_vnum=IDENTITY[1],
        room_listing=room_listing,
        inventory_items=inventory_items,
    )

    assert step.status in {"stopped", "unearthed"}
    assert digging.audit()["quest_object_acquired"] is False


def test_hoard_pickup_requires_the_character_to_remain_in_the_hoard_room():
    digging = unearthed_session()

    step = digging.prepare_quest_object_pickup(
        sequence=4,
        quest_object_vnum=IDENTITY[2],
        source_object_description="a coin of Serenos",
        source_description_vnums=(IDENTITY[2],),
        current_room_vnum=3001,
        room_listing=listed(),
        inventory_items=inventory(),
    )

    assert step.status == "stopped"
    assert "ground listing or source evidence" in step.reason


def test_large_total_movement_budget_pauses_for_recovery_between_digs():
    spade = ObjectSource(3393, "spade", "a spade", 6, (36, 3, 9, 160), 0)
    spade_budget = tool_dig_budget(
        spade, sector_type=1, race="dwarf", level=29,
        observed_tool_level=1, strength=30, constitution=25, dexterity=16,
        swiftness=5, enhanced_swiftness_percent=0,
    )
    digging = HoardDigSession(
        spade_budget, quest_identity=IDENTITY, minimum_hp=400,
        return_movement=30,
    )

    assert spade_budget.maximum_movement > 400
    assert digging.poll(
        observed(tool_vnum=3393, current_budget=spade_budget, movement=456),
        now=0,
    ).command == "dig"
    digging.observe("You dig into the earth with a spade..." + PROMPT)
    assert digging.poll(
        observed(
            sequence=2, tool_vnum=3393, current_budget=spade_budget,
            movement=253,
        ),
        now=9,
    ).command == "dig"
    digging.observe("You dig into the earth with a spade..." + PROMPT)
    pause = digging.poll(
        observed(
            sequence=3, tool_vnum=3393, current_budget=spade_budget,
            movement=50,
        ),
        now=18,
    )
    assert pause.status == "recovery_required"
    assert pause.command is None
    assert digging.commands == 2
    assert digging.audit()["movement_recovery_pauses"] == 1

    # Recovery is performed by the outer policy only after its live safety
    # check; a fresh state with the reserve restored can resume this session.
    assert digging.poll(
        observed(
            sequence=4, tool_vnum=3393, current_budget=spade_budget,
            movement=233,
        ),
        now=25,
    ).command == "dig"


def test_no_command_queue_while_lagging_or_waiting_for_fresh_state():
    digging = session()
    digging.poll(observed(), now=0)
    digging.observe("You dig into the earth with a shovel..." + PROMPT)
    assert digging.poll(observed(sequence=2), now=0.1).command is None
    assert digging.poll(observed(), now=2).command is None
    assert digging.poll(observed(), now=20).status == "stopped"
    assert digging.commands == 1


@pytest.mark.parametrize("text", [
    "You're too exhausted to dig.",
    "You dig into the earth... but get the feeling you're wasting your time.",
])
def test_refusal_and_futility_stop_without_another_dig(text):
    digging = session()
    digging.poll(observed(), now=0)
    for chunk in (text[:12], text[12:]):
        digging.observe(chunk)
    assert digging.poll(observed(sequence=2), now=2).status == "stopped"
    digging.observe("With a final effortful thrust, you unearth something!" + PROMPT)
    assert digging.poll(observed(sequence=3), now=3).status == "stopped"
    assert digging.commands == 1


def test_trap_charge_requires_explicit_fresh_recovery_before_another_dig():
    digging = session()
    assert digging.poll(observed(), now=0).command == "dig"
    digging.observe(
        "You hear a strange noise...\n"
        "You are struck by a small dart... your blood begins to burn!" + PROMPT
    )
    step = digging.poll(observed(sequence=2), now=2)
    assert step.status == "trap_recovery_required"
    assert step.trap_kind == "poison"
    assert digging.commands == 1
    assert digging.poll(observed(sequence=3), now=3).command is None
    assert digging.confirm_trap_recovery(
        observed(sequence=3, trap_recovery_verified=True),
    ).status == "ready"
    assert digging.poll(
        observed(sequence=3, trap_recovery_verified=True), now=3,
    ).command is None
    assert digging.poll(observed(sequence=4), now=4).command == "dig"
    audit = digging.audit()
    assert audit["trap_sequences"] == (2,)
    assert audit["trap_effects"] == ((2, "poison"),)
    assert audit["trap_recovery_sequences"] == (3,)


def test_three_trap_charges_fit_the_bounded_completion_budget():
    small_budget = budget(depth=1)
    digging = HoardDigSession(
        small_budget, quest_identity=IDENTITY, minimum_hp=400,
        return_movement=30,
    )

    current = observed(current_budget=small_budget)
    assert digging.poll(current, now=0).command == "dig"
    sequence = 2
    now = 2.0
    for trap_number in range(1, 4):
        digging.observe(
            "You hear a strange noise...\n"
            "You feel unclean." + PROMPT
        )
        assert digging.poll(
            observed(sequence=sequence, current_budget=small_budget), now=now,
        ).status == "trap_recovery_required"
        sequence += 1
        assert digging.confirm_trap_recovery(
            observed(
                sequence=sequence,
                current_budget=small_budget,
                trap_recovery_verified=True,
            ),
        ).status == "ready"
        assert digging.poll(
            observed(
                sequence=sequence,
                current_budget=small_budget,
                trap_recovery_verified=True,
            ),
            now=now + 0.5,
        ).command is None
        sequence += 1
        now += 2
        assert digging.poll(
            observed(sequence=sequence, current_budget=small_budget), now=now,
        ).command == "dig"
        sequence += 1
        now += 2

    assert digging.commands == small_budget.maximum_dig_commands
    digging.observe(_SUCCESS + PROMPT)
    assert digging.poll(
        observed(sequence=sequence, current_budget=small_budget), now=now,
    ).status == "unearthed"
    assert digging.audit()["trap_pops"] == 3
    assert len(digging.audit()["trap_recovery_sequences"]) == 3


@pytest.mark.parametrize("changes", [
    {"room_vnum": 310}, {"tool_vnum": 99}, {"quest_active": False},
    {"quest_identity": (10001, 309, 587)}, {"hp": 399}, {"movement": 29},
    {"in_combat": True}, {"occupants": 1}, {"standing": False},
    {"hp": float("nan")}, {"quest_active": "yes"}, {"occupants": -1},
    {"current_budget": None},
])
def test_changed_state_stops_before_dig(changes):
    digging = session()
    assert digging.poll(observed(**changes), now=0).status == "stopped"
    assert digging.commands == 0


def test_source_budget_closes_silent_absence_even_without_futility_text():
    digging = session()
    for index in range(5):
        result = digging.poll(observed(sequence=index + 1, movement=482 - index * 23), now=index * 2)
        assert result.command == "dig"
        digging.observe("You dig into the earth with a shovel..." + PROMPT)
    assert digging.poll(observed(sequence=6, movement=367), now=10).status == "stopped"
    assert digging.commands == 5


@pytest.mark.parametrize("reply", [
    "Someone says 'With a final effortful thrust, you unearth something!'",
    "You dig into the earth with another shovel...",
])
def test_quoted_or_wrong_tool_reply_is_not_progress(reply):
    digging = session()
    digging.poll(observed(), now=0)
    digging.observe(reply + PROMPT)
    assert digging.poll(observed(sequence=2), now=2).command is None
    assert digging.poll(observed(sequence=3), now=20).status == "stopped"
    assert digging.commands == 1


def test_response_overflow_is_a_persistable_failure_not_a_buffer_rewind():
    digging = session()
    digging.poll(observed(), now=0)
    digging.observe("x" * 8193)
    assert digging.poll(observed(sequence=2), now=2).status == "stopped"
    audit = digging.audit()
    assert audit["commands"] == 1
    assert audit["quest_identity"] == IDENTITY
    assert audit["quest_object_acquired"] is False
    assert "buffer" in audit["reason"]


def test_changed_stats_or_buffs_do_not_continue_with_an_old_budget():
    digging = session()
    digging.poll(observed(), now=0)
    digging.observe("You dig into the earth with a shovel..." + PROMPT)
    slower = budget(slow=True)
    assert digging.poll(observed(sequence=2, current_budget=slower), now=2).status == "stopped"
    assert digging.commands == 1


def test_trap_recovery_requires_exact_current_observations():
    digging = session()
    digging.poll(observed(), now=0)
    digging.observe(
        "You hear a strange noise...\nYou feel unclean." + PROMPT
    )
    assert digging.poll(observed(sequence=2), now=2).status == "trap_recovery_required"
    assert digging.confirm_trap_recovery(
        observed(sequence=3, trap_recovery_verified=True, occupants=1),
    ).status == "trap_recovery_required"
    assert digging.confirm_trap_recovery(
        observed(sequence=3, trap_recovery_verified=True, room_vnum=310),
    ).status == "stopped"


def test_checkpoint_resume_requires_a_newer_observation_at_a_safe_boundary():
    digging = session()
    assert digging.poll(observed(), now=0).command == "dig"
    digging.observe("You dig into the earth with a shovel..." + PROMPT)
    assert digging.poll(
        observed(sequence=2, movement=30), now=2,
    ).status == "recovery_required"

    restored = HoardDigSession.from_checkpoint(digging.checkpoint())

    assert restored.poll(observed(sequence=2), now=4).status == "waiting"
    resumed = restored.poll(observed(sequence=3), now=4)
    assert resumed.command == "dig"
    assert restored.commands == 2


def acquire_quest_object(digging):
    assert digging.prepare_quest_object_pickup(
        sequence=4,
        quest_object_vnum=IDENTITY[2],
        source_object_description="a coin of Serenos",
        source_description_vnums=(IDENTITY[2],),
        current_room_vnum=IDENTITY[1],
        room_listing=listed(),
        inventory_items=inventory(0),
    ).command == "get #58601"
    return digging.confirm_quest_object_acquired(
        sequence=5,
        quest_object_vnum=IDENTITY[2],
        source_object_description="a coin of Serenos",
        source_description_vnums=(IDENTITY[2],),
        inventory_items=inventory(1),
    )


def test_hoard_object_checkpoint_round_trips_and_reads_v1():
    acquired = unearthed_session()
    assert acquire_quest_object(acquired).status == "object_acquired"

    restored = HoardDigSession.from_checkpoint(acquired.checkpoint())
    assert restored.stage == "object_acquired"
    assert restored.audit()["quest_object_acquired"] is True
    assert restored.audit()["quest_object_selector"] == "#58601"
    assert restored.audit()["quest_object_baseline_count"] == 0

    legacy = unearthed_session().checkpoint()
    legacy["schema_version"] = 1
    legacy.pop("unearthed_sequence")
    legacy.pop("quest_object_selector")
    legacy.pop("quest_object_acquired_sequence")
    restored_legacy = HoardDigSession.from_checkpoint(legacy)
    assert restored_legacy.stage == "unearthed"
    assert restored_legacy._unearthed_sequence == 2

    old_acquired = acquired.checkpoint()
    old_acquired["schema_version"] = 2
    old_acquired.pop("quest_object_baseline_count")
    old_acquired.pop("quest_object_pickup_sequence")
    restored_old_acquired = HoardDigSession.from_checkpoint(old_acquired)
    assert restored_old_acquired.stage == "stopped"
    assert restored_old_acquired.audit()["quest_object_acquired"] is False
    assert "quantity delta" in restored_old_acquired.reason


def test_pickup_checkpoint_never_reissues_and_waits_for_inventory_delta():
    digging = unearthed_session()
    pending = digging.prepare_quest_object_pickup(
        sequence=4,
        quest_object_vnum=IDENTITY[2],
        source_object_description="a coin of Serenos",
        source_description_vnums=(IDENTITY[2],),
        current_room_vnum=IDENTITY[1],
        room_listing=listed(),
        inventory_items=inventory(1),
    )
    assert pending.command == "get #58601"

    restored = HoardDigSession.from_checkpoint(digging.checkpoint())
    assert restored.stage == "pickup_pending"
    assert restored.poll(observed(sequence=5), now=20).command is None
    assert restored.confirm_quest_object_acquired(
        sequence=5,
        quest_object_vnum=IDENTITY[2],
        source_object_description="a coin of Serenos",
        source_description_vnums=(IDENTITY[2],),
        inventory_items=inventory(1),
    ).status == "pickup_pending"
    assert restored.confirm_quest_object_acquired(
        sequence=6,
        quest_object_vnum=IDENTITY[2],
        source_object_description="a coin of Serenos",
        source_description_vnums=(IDENTITY[2],),
        inventory_items=inventory(1),
    ).status == "pickup_pending"
    assert restored.poll(observed(sequence=7), now=30).command is None


def test_pickup_confirmation_rejects_more_than_one_matching_item():
    digging = unearthed_session()
    assert digging.prepare_quest_object_pickup(
        sequence=4,
        quest_object_vnum=IDENTITY[2],
        source_object_description="a coin of Serenos",
        source_description_vnums=(IDENTITY[2],),
        current_room_vnum=IDENTITY[1],
        room_listing=listed(),
        inventory_items=inventory(1),
    ).command == "get #58601"

    step = digging.confirm_quest_object_acquired(
        sequence=5,
        quest_object_vnum=IDENTITY[2],
        source_object_description="a coin of Serenos",
        source_description_vnums=(IDENTITY[2],),
        inventory_items=inventory(3),
    )

    assert step.status == "stopped"
    assert "exactly one" in step.reason


def test_hoard_object_checkpoint_rejects_inconsistent_selector_sequence():
    acquired = unearthed_session()
    assert acquire_quest_object(acquired).status == "object_acquired"
    checkpoint = acquired.checkpoint()
    checkpoint["quest_object_acquired_sequence"] = checkpoint["quest_object_pickup_sequence"]

    with pytest.raises(ValueError, match="quest-object evidence"):
        HoardDigSession.from_checkpoint(checkpoint)


def test_checkpoint_during_an_unanswered_dig_never_replays_the_command():
    digging = session()
    assert digging.poll(observed(), now=0).command == "dig"

    restored = HoardDigSession.from_checkpoint(digging.checkpoint())

    assert restored.poll(observed(sequence=2), now=20).status == "stopped"
    assert "reconcile recorded events" in restored.reason
    assert restored.commands == 1


def test_checkpoint_without_a_live_observation_cannot_start_excavation():
    restored = HoardDigSession.from_checkpoint(session().checkpoint())

    assert restored.poll(observed(), now=0).status == "stopped"
    assert "repeat the source and live preflight" in restored.reason
    assert restored.commands == 0


def test_trap_checkpoint_requires_recovery_again_after_restart():
    digging = session()
    assert digging.poll(observed(), now=0).command == "dig"
    digging.observe(
        "You hear a strange noise...\nYou feel unclean." + PROMPT
    )
    assert digging.poll(observed(sequence=2), now=2).status == "trap_recovery_required"
    restored = HoardDigSession.from_checkpoint(digging.checkpoint())

    assert restored.poll(observed(sequence=3), now=4).status == "trap_recovery_required"
    assert restored.confirm_trap_recovery(
        observed(sequence=3, trap_recovery_verified=True),
    ).status == "ready"
    assert restored.poll(
        observed(sequence=3, trap_recovery_verified=True), now=4,
    ).command is None
    assert restored.poll(observed(sequence=4), now=4).command == "dig"


def test_checkpoint_rejects_counters_beyond_the_source_budget():
    digging = session()
    checkpoint = digging.checkpoint()
    checkpoint["commands"] = budget().maximum_dig_commands + 1

    with pytest.raises(ValueError, match="source excavation limits"):
        HoardDigSession.from_checkpoint(checkpoint)


@pytest.mark.parametrize("field", ["reason", "unexpected"])
def test_checkpoint_rejects_missing_or_unknown_schema_fields(field):
    checkpoint = session().checkpoint()
    if field == "reason":
        checkpoint.pop(field)
    else:
        checkpoint[field] = True

    with pytest.raises(ValueError, match="unsupported hoard excavation checkpoint"):
        HoardDigSession.from_checkpoint(checkpoint)
