import pytest

from dd4tester.character import CharacterSpec
from dd4tester.fastwalks import route_named
from dd4tester.starter import FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState
from dd4tester.equipment import GearCatalog
from dd4tester.hunt_candidates import ObjectSource
from dd4tester.starter import _capacity_relief_inventory_keyword


def _policy(monkeypatch) -> StarterPolicy:
    spec = CharacterSpec.from_mapping({
        "name": "CapacityTest", "race": "human", "gender": "female",
        "class": "warrior", "subclass": None, "title": "",
    })
    policy = StarterPolicy(
        spec, "test-password", fastwalk_route=route_named("moria"),
        fastwalk_hunt_stops=(FieldHuntStop(
            (), None, required_items=("grain",), allow_below_band_for_required_loot=True,
        ),),
    )
    policy.in_world = policy.prompt_ready = True
    monkeypatch.setattr("dd4tester.starter._capacity_relief_inventory_keyword",
                        lambda *_args, **_kwargs: "junk")
    return policy


def _state(count: int) -> CharacterState:
    return CharacterState(room_vnum="3054", position=7,
                          stats={"carry_num": count, "maxcarry_num": 38})


def _acknowledge_disposal(policy: StarterPolicy, state: CharacterState) -> None:
    policy.observe_text("You drop the junk.\n")
    handled, decision = policy._fastwalk_required_loot_capacity_preflight_decision(state)
    assert handled and decision.command == "sacrifice junk"
    policy.observe_text("You sacrifice the junk to God.\n")
    handled, decision = policy._fastwalk_required_loot_capacity_preflight_decision(state)
    assert handled and decision.command == "inventory"
    policy.observe_text(f"Your backpack contains:\nYou are carrying {state.stats['carry_num']}/38 items.")


@pytest.mark.parametrize("count,budget", ((37, 0), (38, 1), (39, 2), (45, 8)))
def test_loot_cleanup_budget_includes_initial_overload(monkeypatch, count, budget) -> None:
    policy = _policy(monkeypatch)
    handled, decision = policy._fastwalk_required_loot_capacity_preflight_decision(_state(count))
    assert policy._recovery_session.required_loot_capacity_relief_limit == budget
    assert handled is bool(budget)
    assert (decision.command if decision else None) == ("drop junk" if budget else None)


def test_overloaded_loot_preflight_allows_two_acknowledged_discards(monkeypatch) -> None:
    policy = _policy(monkeypatch)
    _, first = policy._fastwalk_required_loot_capacity_preflight_decision(_state(39))
    assert first.command == "drop junk"
    _acknowledge_disposal(policy, _state(38))
    _, second = policy._fastwalk_required_loot_capacity_preflight_decision(_state(38))
    assert second.command == "drop junk"
    assert policy._recovery_session.required_loot_capacity_relief_limit == 2
    _acknowledge_disposal(policy, _state(37))
    handled, decision = policy._fastwalk_required_loot_capacity_preflight_decision(_state(37))
    assert not handled and decision is None
    assert policy.fastwalk_required_loot_capacity_preflight_complete


def test_unchanged_capacity_never_expands_fixed_cleanup_budget(monkeypatch) -> None:
    policy = _policy(monkeypatch)
    for _ in range(2):
        _, decision = policy._fastwalk_required_loot_capacity_preflight_decision(_state(39))
        assert decision.command == "drop junk"
        _acknowledge_disposal(policy, _state(39))
    handled, decision = policy._fastwalk_required_loot_capacity_preflight_decision(_state(39))
    assert handled
    assert decision is None or not decision.command.startswith("drop ")
    assert policy._recovery_session.required_loot_capacity_relief_limit == 2
    assert policy.fastwalk_required_loot_capacity_relief_attempts == 2


def test_cleanup_rejects_excessive_deficit_without_discard(monkeypatch) -> None:
    policy = _policy(monkeypatch)
    handled, decision = policy._fastwalk_required_loot_capacity_preflight_decision(_state(46))
    assert handled
    assert decision is None or not decision.command.startswith("drop ")
    assert policy.fastwalk_required_loot_capacity_relief_attempts == 0


def test_cleanup_waits_for_drop_acknowledgement(monkeypatch) -> None:
    policy = _policy(monkeypatch)
    policy._fastwalk_required_loot_capacity_preflight_decision(_state(39))
    policy.observe_text("The healer smiles.")
    handled, decision = policy._fastwalk_required_loot_capacity_preflight_decision(_state(38))
    assert handled and decision is None
    assert not policy.fastwalk_required_loot_capacity_preflight_complete


def test_cleanup_retains_delayed_drop_after_healer_chatter(monkeypatch) -> None:
    clock = [100.0]
    monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: clock[0])
    policy = _policy(monkeypatch)
    policy._fastwalk_required_loot_capacity_preflight_decision(_state(39))
    policy.observe_text("The Healer utters the word 'Edahs'.\n")
    handled, decision = policy._fastwalk_required_loot_capacity_preflight_decision(_state(39))
    assert handled and decision is None
    assert not policy.midgaard_logout_pending
    clock[0] = 100.2
    policy.observe_text("You drop the junk.\n")
    handled, decision = policy._fastwalk_required_loot_capacity_preflight_decision(_state(38))
    assert handled and decision.command == "sacrifice junk"
    assert policy._recovery_session.loot_capacity_reply.command == "sacrifice junk"


def test_cleanup_timeout_is_visible_before_prompt_gate(monkeypatch) -> None:
    clock = [100.0]
    monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: clock[0])
    policy = _policy(monkeypatch)
    policy._fastwalk_required_loot_capacity_preflight_decision(_state(39))
    policy.prompt_ready = False
    clock[0] = 105.0
    policy.next_decision(_state(39))
    assert "reply exceeded five seconds" in policy.deferred_failure
    assert policy._recovery_session.loot_capacity_reply.command is None


def test_capacity_relief_preserves_last_water_vessels_and_gear() -> None:
    flask = ObjectSource(202, "flask glass", "a colorless flask", 17, (250, 50, 0, 0), 10)
    skin = ObjectSource(1, "buffalo skin", "a buffalo water skin", 17, (100, 100, 0, 0), 10)
    catalog = GearCatalog({202: flask, 1: skin})
    assert _capacity_relief_inventory_keyword(
        ["a colorless flask", "a colorless flask", "a buffalo water skin"], catalog,
    ) == "flask"
    assert _capacity_relief_inventory_keyword(["a colorless flask", "a buffalo water skin"], catalog) is None
    assert _capacity_relief_inventory_keyword(["a colorless flask", "a colorless flask"], catalog) is None


def test_capacity_relief_accepts_only_all_water_skin_variants() -> None:
    flask = ObjectSource(202, "flask glass", "a colorless flask", 17, (250, 50, 0, 0), 10)
    skin = ObjectSource(1, "buffalo skin", "a buffalo water skin", 17, (100, 100, 0, 0), 10)
    variant = ObjectSource(2, "buffalo skin", "a buffalo water skin", 17, (25, 25, 0, 0), 10)
    inventory = ["a colorless flask", "a colorless flask", "a buffalo water skin"]
    assert _capacity_relief_inventory_keyword(inventory, GearCatalog({202: flask, 1: skin, 2: variant})) == "flask"
    poisoned = ObjectSource(2, "buffalo skin", "a buffalo water skin", 17, (25, 25, 0, 1), 10)
    assert _capacity_relief_inventory_keyword(inventory, GearCatalog({202: flask, 1: skin, 2: poisoned})) is None


def test_capacity_relief_rejects_unknown_carried_keyword_collisions() -> None:
    flask = ObjectSource(202, "flask glass", "a colorless flask", 17, (250, 50, 0, 0), 10)
    skin = ObjectSource(1, "buffalo skin", "a buffalo water skin", 17, (100, 100, 0, 0), 10)
    inventory = ["a colorless flask", "a colorless flask", "a buffalo water skin", "an unknown flask"]
    assert _capacity_relief_inventory_keyword(inventory, GearCatalog({202: flask, 1: skin})) is None


@pytest.mark.parametrize("liquid", (1, 2, 7))
def test_capacity_relief_can_dispose_of_duplicate_ordinary_alcohol_vessels(liquid) -> None:
    carafe = ObjectSource(30249, "carafe", "a carafe", 17, (8, 8, liquid, 0), 1)
    skin = ObjectSource(1, "buffalo skin", "a buffalo water skin", 17, (100, 100, 0, 0), 10)
    catalog = GearCatalog({30249: carafe, 1: skin})
    assert _capacity_relief_inventory_keyword(
        ["a carafe", "a carafe", "a buffalo water skin"], catalog,
    ) == "carafe"
    assert _capacity_relief_inventory_keyword(["a carafe", "a buffalo water skin"], catalog) == "carafe"
    assert _capacity_relief_inventory_keyword(["a carafe", "a carafe"], catalog) is None


def test_capacity_relief_uses_a_source_alternative_when_glass_is_ambiguous() -> None:
    glass = ObjectSource(30250, "glass shot shotglass", "a shot glass", 17, (2, 2, 7, 0), 1)
    flask = ObjectSource(202, "flask glass", "a colorless flask", 17, (250, 50, 0, 0), 10)
    skin = ObjectSource(1, "buffalo skin", "a buffalo water skin", 17, (100, 100, 0, 0), 10)
    catalog = GearCatalog({30250: glass, 202: flask, 1: skin})
    assert _capacity_relief_inventory_keyword(
        ["a shot glass", "a shot glass", "a colorless flask", "a buffalo water skin"], catalog,
    ) == "shot"


def test_capacity_relief_rejects_prefix_collisions_and_unknown_inventory() -> None:
    glass = ObjectSource(30250, "glass shot", "a shot glass", 17, (2, 2, 7, 0), 1)
    flask = ObjectSource(202, "flask glass", "a colorless flask", 17, (250, 50, 0, 0), 10)
    collision = ObjectSource(3, "shotgun", "a shotgun", 8, (0, 0, 0, 0), 1)
    catalog = GearCatalog({30250: glass, 202: flask, 3: collision})
    assert _capacity_relief_inventory_keyword(
        ["a shot glass", "a colorless flask", "a shotgun"], catalog,
    ) is None
    assert _capacity_relief_inventory_keyword(
        ["a shot glass", "a colorless flask", "an unknown item"], catalog,
    ) is None


def test_capacity_relief_keeps_poisoned_or_ambiguous_alcohol_vessels() -> None:
    carafe = ObjectSource(30249, "carafe", "a carafe", 17, (8, 8, 2, 0), 1)
    poisoned = ObjectSource(30251, "carafe", "a carafe", 17, (8, 8, 2, 1), 1)
    skin = ObjectSource(1, "buffalo skin", "a buffalo water skin", 17, (100, 100, 0, 0), 10)
    inventory = ["a carafe", "a carafe", "a buffalo water skin"]
    assert _capacity_relief_inventory_keyword(inventory, GearCatalog({30251: poisoned, 1: skin})) is None
    assert _capacity_relief_inventory_keyword(
        inventory, GearCatalog({30249: carafe, 30251: poisoned, 1: skin}),
    ) is None


def test_last_nonwater_vessel_cleanup_requires_separate_safe_water_and_unique_keyword() -> None:
    carafe = ObjectSource(30249, "carafe", "a carafe", 17, (8, 8, 2, 0), 1)
    skin = ObjectSource(1, "buffalo skin", "a buffalo water skin", 17, (100, 100, 0, 0), 10)
    assert _capacity_relief_inventory_keyword(["a carafe"], GearCatalog({30249: carafe})) is None
    collision = ObjectSource(2, "carafe drinking", "a drinking tool", 8, (0, 0, 0, 0), 1)
    catalog = GearCatalog({30249: carafe, 1: skin, 2: collision})
    assert _capacity_relief_inventory_keyword(
        ["a carafe", "a buffalo water skin", "a drinking tool"], catalog,
    ) is None


def test_last_water_vessel_prototype_stays_protected_with_another_water_source() -> None:
    flask = ObjectSource(202, "flask glass", "a colorless flask", 17, (250, 50, 0, 0), 10)
    skin = ObjectSource(1, "buffalo skin", "a buffalo water skin", 17, (100, 100, 0, 0), 10)
    assert _capacity_relief_inventory_keyword(
        ["a colorless flask", "a buffalo water skin"], GearCatalog({202: flask, 1: skin}),
    ) is None


def test_pending_failed_field_logout_has_one_recovery_owner(monkeypatch) -> None:
    policy = _policy(monkeypatch)
    policy.return_home = policy.fastwalk_returning = policy.midgaard_logout_pending = True
    policy.audit_combat_pouch = False
    policy.stage = "tutorial"
    policy.gear_catalog = None
    state = CharacterState(
        room_vnum="3054", position=7, hp=100, max_hp=100, mana=100, max_mana=100,
        move=89, max_move=100,
    )
    decision = policy.next_decision(state)
    assert decision.command == "sleep"
    state.position = 4
    policy.prompt_ready = True
    assert policy.next_decision(state) is None
    assert policy.waiting_for_heal
    assert not policy.saved
    state.move = 90
    policy.prompt_ready = True
    assert policy.next_decision(state).command == "stand"
    state.position = 7
    policy.prompt_ready = True
    assert policy.next_decision(state).command == "save"


def test_pending_logout_never_skips_wounded_recovery(monkeypatch) -> None:
    policy = _policy(monkeypatch)
    policy.return_home = policy.fastwalk_returning = policy.midgaard_logout_pending = True
    policy.audit_combat_pouch = False
    policy.stage = "tutorial"
    policy.gear_catalog = None
    state = CharacterState(
        room_vnum="3054", position=7, hp=94, max_hp=100, mana=100, max_mana=100,
        move=100, max_move=100,
    )
    assert policy.next_decision(state).command == "sleep"
    state.position = 4
    policy.prompt_ready = True
    assert policy.next_decision(state) is None
    assert not policy.saved


def test_cleanup_fresh_state_must_catch_up_within_five_seconds(monkeypatch) -> None:
    clock = [100.0]
    monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: clock[0])
    policy = _policy(monkeypatch)
    policy.fastwalk_required_loot_capacity_relief_step = 4
    reply = policy._recovery_session.loot_capacity_reply
    reply.begin("inventory", now=100)
    policy.observe_text("Your backpack contains:\nYou are carrying 37/38 items.\n")
    handled, decision = policy._fastwalk_required_loot_capacity_preflight_decision(_state(38))
    assert handled and decision is None
    clock[0] = 105.0
    policy._fastwalk_required_loot_capacity_preflight_decision(_state(38))
    assert "fresh state within five seconds" in policy.deferred_failure
    assert reply.command is None


def test_flight_uses_same_confirmed_overload_cleanup_before_shop_travel(monkeypatch) -> None:
    policy = _policy(monkeypatch)
    policy.fastwalk_route = None
    policy.magic_shop_research = policy.magic_shop_buy_fly = True
    policy.fastwalk_required_loot_capacity_preflight_complete = False
    state = _state(39)
    decision = policy._magic_shop_research_decision(state)
    assert decision.command == "drop junk"
    assert policy._recovery_session.carrying_capacity.limit == 2
    policy.observe_text("The healer smiles.\n")
    assert policy._magic_shop_research_decision(state) is None
    assert not policy.midgaard_logout_pending
    policy.observe_text("You drop the junk.\n")
    assert policy._magic_shop_research_decision(_state(38)).command == "sacrifice junk"
    policy.observe_text("You sacrifice the junk to God.\n")
    assert policy._magic_shop_research_decision(_state(38)).command == "inventory"
    policy.observe_text("Your backpack contains:\nYou are carrying 38/38 items.\n")
    assert policy._magic_shop_research_decision(_state(38)).command == "drop junk"


def test_capacity_controller_is_the_single_owner(monkeypatch) -> None:
    policy = _policy(monkeypatch)
    controller = policy._recovery_session.carrying_capacity
    policy.fastwalk_required_loot_capacity_relief_step = 3
    policy.required_loot_capacity_relief_keyword = "junk"
    assert controller.step == 3 and controller.keyword == "junk"
    assert "fastwalk_required_loot_capacity_relief_step" not in policy.__dict__
    assert policy._recovery_session.loot_capacity_reply is controller.reply


def test_healer_carrying_cleanup_never_dispatches_in_field(monkeypatch) -> None:
    policy = _policy(monkeypatch)
    state = _state(39)
    state.room_vnum = "3033"
    handled, decision = policy._healer_carrying_capacity_preflight_decision(state, required_slots=1)
    assert handled and (decision is None or not decision.command.startswith("drop "))
    assert policy._recovery_session.carrying_capacity.attempts == 0
    assert "healer gate" in policy._recovery_session.carrying_capacity.failure


def test_flight_capacity_failure_is_not_a_funds_failure(monkeypatch) -> None:
    policy = _policy(monkeypatch)
    policy.magic_shop_research = policy.magic_shop_buy_fly = True
    policy.observe_text("You can't carry that many items.\n")
    assert policy._recovery_session.flight_purchase_failure_reason == "capacity"
    policy.observe_text("You can't afford that.\n")
    policy.observe_text("You can't carry that many items.\n")
    assert policy._recovery_session.flight_purchase_failure_reason == "funds"
