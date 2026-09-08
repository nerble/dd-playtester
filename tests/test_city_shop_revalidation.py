import asyncio
from copy import deepcopy
from dataclasses import replace

import pytest

from dd4tester import campaign
from dd4tester.character import CharacterSpec
from dd4tester.starter import StarterPolicy
from dd4tester.state import CharacterState


def probe_policy():
    policy = StarterPolicy(
        CharacterSpec.from_mapping({
            "name": "Testmage", "race": "human", "gender": "female", "class": "mage",
        }), "fixture-password", return_home=True, world_time_probe=True,
        recheck_city_shop_route=True, title_configured=True, description_configured=True,
    )
    policy.in_world = policy.login_authenticated = policy.prompt_ready = True
    policy.world_boot_id = "fixture-boot"
    state = CharacterState(
        level=8, hp=113, max_hp=113, mana=324, max_mana=324,
        move=220, max_move=220, position=7, room_vnum="3054",
        room_name="By the Temple Altar", room_flags=["safe", "healing"],
    )
    return policy, state


def start_locator(policy, state):
    time = policy.next_decision(state)
    assert time.command == "time"
    policy.after_command(time)
    policy.prompt_ready = True
    locator = policy.next_decision(state)
    assert locator.command == "where drunk"
    policy.after_command(locator)


@pytest.mark.parametrize("location,clear", [("Grubby Inn", True), ("Main Street", False)])
def test_reset_probe_observes_city_route_without_travelling_or_casting(location, clear):
    policy, state = probe_policy()
    policy.known_skill_levels["invis"] = 99
    state = replace(state, affects=[[{"name": "invis", "duration": "20"}]])
    start_locator(policy, state)
    policy.observe_text(
        f"You detect the presence of:\nThe drunk                    {location}\n"
        "\n<113/113 hits 324/324 mana 220/220 move [Midgaard]>"
    )
    policy.prompt_ready = True
    decision = policy.next_decision(state)
    assert decision.command == "save"
    proof = policy.city_shop_route_probe_checkpoint(state)["campaign_city_shop_route_probe"]
    assert proof["complete"] and proof["clear"] is clear
    assert proof["locations"] == [location.casefold()]
    assert not policy.magic_shop_invisibility_attempted
    assert policy.city_shop_route_wait_attempts == 0


@pytest.mark.parametrize("response", ["", "You fail to find anyone by that name.\n", "Huh?\n"])
def test_missing_city_location_cannot_release_obstruction(monkeypatch, response):
    now = [10.0]
    monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: now[0])
    policy, state = probe_policy()
    start_locator(policy, state)
    if response:
        policy.observe_text(response)
    now[0] += 2
    policy.prompt_ready = True
    assert policy.next_decision(state).command == "save"
    assert not policy.city_shop_route_probe_checkpoint(state)["campaign_city_shop_route_probe"]["clear"]


def test_runtime_boundary_skips_optional_locator():
    policy, state = probe_policy()
    policy.world_time_queried = True
    policy.request_runtime_boundary()
    assert policy.next_decision(state).command == "save"
    assert not policy.city_shop_route_probe_checkpoint(state)["campaign_city_shop_route_probe"]["complete"]


def test_sleeping_probe_wakes_before_locator():
    policy, state = probe_policy()
    policy.world_time_queried = True
    assert policy.next_decision(replace(state, position=4)).command == "stand"


def revalidation_states():
    policy, state = probe_policy()
    start_locator(policy, state)
    policy.observe_text("You detect the presence of:\nThe drunk                    Grubby Inn\n")
    observed = {**state.to_dict(), "world_boot_id": "fixture-boot",
                **policy.city_shop_route_probe_checkpoint(state)}
    previous = {
        "world_boot_id": "fixture-boot", "magic_shop_route_blocked_by_drunk": True,
        "campaign_magic_shop_route_blocked_boot_id": "fixture-boot",
        "campaign_flight_purchase_cooldown": 3, "campaign_city_shop_route_cooldown": 2,
        "magic_shop_purchase_failed": False, "campaign_flight_funding_retry_pending": True,
        "campaign_flight_loan_attempted": True, "campaign_xp_loss_total": 118,
        "campaign_research_results": {"lost-hunt": {"xp_delta": -118}},
    }
    return previous, deepcopy(previous), observed


def test_fresh_location_releases_only_the_obsolete_route_cooldowns():
    previous, current, observed = revalidation_states()
    updated = campaign._reconcile_city_shop_route_probe(previous, current, observed, run_id=99)
    assert "magic_shop_route_blocked_by_drunk" not in updated
    assert "campaign_flight_purchase_cooldown" not in updated
    assert "campaign_city_shop_route_cooldown" not in updated
    for key in ("campaign_xp_loss_total", "campaign_research_results",
                "campaign_flight_funding_retry_pending", "campaign_flight_loan_attempted"):
        assert updated[key] == previous[key]
    assert updated["campaign_city_shop_route_probe"]["run_id"] == 99
    assert previous == current


@pytest.mark.parametrize("boundary", [
    "cached", "incomplete", "blocked", "on-route", "on-route-article", "no-locations", "no-routes",
    "unknown-boot", "changed-boot", "wrong-room", "purchase-failed", "purchase-unknown",
])
def test_revalidation_requires_fresh_complete_evidence(boundary):
    previous, current, observed = revalidation_states()
    probe = observed["campaign_city_shop_route_probe"]
    if boundary == "cached":
        current["campaign_city_shop_route_probe"] = observed.pop("campaign_city_shop_route_probe")
    elif boundary == "incomplete":
        probe["complete"] = False
    elif boundary == "blocked":
        probe["clear"] = False
    elif boundary == "on-route":
        probe["locations"] = ["Main Street"]
    elif boundary == "on-route-article":
        probe["locations"] = ["The Main Street", "The Leather Shop"]
    elif boundary == "no-locations":
        probe["locations"] = []
    elif boundary == "no-routes":
        probe["route_rooms"] = []
    elif boundary == "unknown-boot":
        observed["world_boot_id"] = probe["boot_id"] = None
    elif boundary == "changed-boot":
        observed["world_boot_id"] = probe["boot_id"] = "new-boot"
    elif boundary == "wrong-room":
        observed["room_vnum"] = "3001"
    elif boundary == "purchase-failed":
        previous["magic_shop_purchase_failed"] = True
    elif boundary == "purchase-unknown":
        previous.pop("magic_shop_purchase_failed")
    updated = campaign._reconcile_city_shop_route_probe(previous, current, observed, run_id=99)
    assert updated["magic_shop_route_blocked_by_drunk"]
    assert updated["campaign_flight_purchase_cooldown"] == 3
    assert updated["campaign_city_shop_route_cooldown"] == 2


@pytest.mark.parametrize("blocked", [False, True])
def test_public_policy_adapter_enables_only_the_recorded_obstruction(monkeypatch, blocked):
    captured = {}
    class Runner:
        def __init__(self, spec, path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return "finished"

    monkeypatch.setattr(campaign, "StarterBotRunner", Runner)
    policy, _state = probe_policy()
    result = asyncio.run(campaign._run_policy_segment(
        policy.spec, "unused.yaml", campaign._WORLD_TIME_PROBE_POLICY,
        current_state={"magic_shop_route_blocked_by_drunk": blocked},
    ))
    assert result == "finished"
    assert bool(captured.get("recheck_city_shop_route")) is blocked
    assert captured["world_time_probe"] and captured["return_home"]
