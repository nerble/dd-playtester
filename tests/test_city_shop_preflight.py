from dataclasses import replace
from pathlib import Path

import pytest

from dd4tester.character import CharacterSpec
from dd4tester.starter import StarterPolicy
from dd4tester.state import CharacterState
from dd4tester.visibility import learned_invisibility_mana_cost


@pytest.mark.parametrize("base,subclass", [
    ("mage", None), ("mage", "warlock"), ("cleric", "druid"),
    ("thief", "ninja"), ("psionic", "witch"), ("brawler", "monk"),
])
def test_invisibility_authorized_source_paths(base, subclass):
    assert learned_invisibility_mana_cost(base, subclass, {"invis": 30}) == 15


@pytest.mark.parametrize("base,subclass", [
    ("warrior", None), ("brawler", None), ("shifter", None),
    ("mage", "monk"), ("cleric", "warlock"), ("unknown", None),
])
def test_observed_invisibility_does_not_authorize_unknown_class_paths(base, subclass):
    assert learned_invisibility_mana_cost(base, subclass, {"invis": 99}) is None


@pytest.mark.parametrize("value", [None, 0, -1, 101, "40", True, 40.0])
def test_invisibility_requires_positive_numeric_practice(value):
    assert learned_invisibility_mana_cost("mage", None, {"invis": value}) is None


@pytest.mark.parametrize("proficiency,cost", [(1, 44), (30, 15), (40, 5), (99, 5)])
def test_invisibility_source_mana_formula(proficiency, cost):
    assert learned_invisibility_mana_cost("mage", None, {"invis": proficiency}) == cost


def test_invisibility_registry_matches_audited_prerequisite_files():
    root = Path("runs/dd4-source/server/src")
    for name in ("mage", "cleric", "thief", "psionic", "monk"):
        text = (root / "pre_reqs" / f"pre_req-{name}.c").read_text()
        assert "{&gsn_invis," in text
    const = (root / "const.c").read_text()
    assert "spell_invis, 5, 1," in const


@pytest.fixture
def shop(monkeypatch):
    clock = [100.0]
    monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: clock[0])
    policy = StarterPolicy(
        CharacterSpec.from_mapping({
            "name": "Testmage", "race": "human", "gender": "female", "class": "mage",
        }), "fixture-password", magic_shop_research=True, magic_shop_buy_fly=True,
        title_configured=True, description_configured=True,
    )
    policy.in_world = policy.prompt_ready = True
    state = CharacterState(
        level=8, hp=113, max_hp=113, mana=324, max_mana=324,
        move=220, max_move=220, room_vnum="3054", room_name="By the Temple Altar",
        position=7, area="Midgaard",
    )
    return policy, state, clock


def locate(policy, state, location):
    decision = policy.next_decision(state)
    assert decision is not None and decision.command == "where drunk"
    policy.after_command(decision)
    policy.observe_text(
        f"You detect the presence of:\nThe drunk                    {location}\n"
        "\n<113/113 hits 324/324 mana 220/220 move [Midgaard]>"
    )
    policy.prompt_ready = True


def wait_and_wake(policy, state, clock, *, already_awake=False):
    wait = policy.next_decision(state)
    assert wait is not None and wait.command == "sleep"
    assert policy.magic_shop_route_blocked_by_drunk
    policy.after_command(wait)
    sleeping = replace(state, position=4)
    clock[0] += 11.9
    assert policy.next_decision(sleeping) is None
    clock[0] += .1
    if not already_awake:
        wake = policy.next_decision(sleeping)
        assert wake is not None and wake.command == "stand"
        assert policy.magic_shop_route_blocked_by_drunk
        policy.after_command(wake)
    policy.prompt_ready = True


@pytest.mark.parametrize("already_awake", [False, True])
def test_run_12771_rechecks_without_invented_invisibility(shop, already_awake):
    policy, state, clock = shop
    locate(policy, state, "Main Street")
    wait_and_wake(policy, state, clock, already_awake=already_awake)
    locate(policy, state, "Grubby Inn")

    depart = policy.next_decision(state)
    assert depart is not None and depart.command == "south"
    assert policy.city_shop_route_wait_attempts == 1
    assert not policy.magic_shop_invisibility_attempted
    assert not policy.magic_shop_route_blocked_by_drunk


def test_persistent_hazard_stops_after_three_rechecks(shop):
    policy, state, clock = shop
    for _ in range(3):
        locate(policy, state, "Main Street")
        wait_and_wake(policy, state, clock)
    locate(policy, state, "Main Street")

    save = policy.next_decision(state)
    assert save is not None and save.command == "save"
    assert policy.city_shop_route_wait_attempts == 3
    assert policy.city_shop_route_wait_due is None
    assert policy.magic_shop_route_blocked_by_drunk
    assert not policy.magic_shop_purchase_failed


def test_runtime_boundary_interrupts_city_wait(shop):
    policy, state, clock = shop
    locate(policy, state, "Main Street")
    policy.after_command(policy.next_decision(state))
    policy.request_runtime_boundary()

    assert policy.city_shop_route_wait_due is None
    wake = policy.next_decision(replace(state, position=4))
    assert wake is not None and wake.command == "stand"
    assert policy.magic_shop_route_blocked_by_drunk


@pytest.mark.parametrize("changes", [
    {"mana": None}, {"mana": 14}, {"position": 4}, {"position": None},
    {"in_combat": True}, {"enemies": [[{"name": "the drunk", "hp": "20"}]]},
])
def test_practiced_invisibility_retains_resource_and_position_gates(shop, changes):
    policy, state, clock = shop
    policy.known_skill_levels["invis"] = 30
    assert not policy._can_cast_travel_invisibility(replace(state, **changes))


def test_known_name_without_practice_cannot_cast(shop):
    policy, state, clock = shop
    policy.known_skills.add("invis")
    assert not policy._can_cast_travel_invisibility(state)
    assert policy._midgaard_city_shop_preflight_decision(
        state, operation="Magic Shop travel",
    ).command == "where drunk"


def test_cast_does_not_clear_route_without_active_affect(shop):
    policy, state, clock = shop
    policy.known_skill_levels["invis"] = 30
    cast = policy._midgaard_city_shop_preflight_decision(state, operation="shop")
    assert cast.command == "cast invis"
    assert not policy.magic_shop_drunk_preflight_complete
    assert policy._midgaard_city_shop_preflight_decision(
        state, operation="shop",
    ).command == "where drunk"
