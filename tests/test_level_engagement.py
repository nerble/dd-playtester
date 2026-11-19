from dataclasses import replace
from types import SimpleNamespace

import pytest

from dd4tester import campaign
from dd4tester.character import CharacterSpec
from dd4tester.fastwalks import route_named
from dd4tester.hunt_candidates import HuntCandidate
from dd4tester.starter import FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


def candidate(hp: int = 1600, level: int = 39) -> HuntCandidate:
    return HuntCandidate(
        status="caution", score=1, area_file="test.are", mobile_vnum=916,
        target="the target", target_keyword="target", level=level,
        room_vnum=927, room_name="Test room", route=("north",),
        source_spawn_limit=1, room_spawn_count=1, boot_kills=0,
        loot=(), source_value=0, contained_coins=0, hazards=(),
        equipped_weapons=(), estimated_level_range=(level, level),
        estimated_base_hp_range=(hp, hp), estimated_peak_round_damage=100,
        estimated_critical_hit_damage=30, sentinel=True,
    )


def policy_and_state(target_hp: int | None = 1599):
    stop = FieldHuntStop(
        (), "the target", exact_target=True, source_mobile_vnum=916,
        source_policy_id="source-ranked-hunt-test-916-927-39",
        source_target_armed=False, maximum_level_offset=1,
        source_target_hp_ceiling=100_000, source_peak_round_damage=100,
        source_combat_action="flamestrike",
        source_combat_conservative_damage=122, source_combat_max_actions=12,
        allow_protected_hp_fuzz_probe=True, require_sanctuary=True,
        require_damage_window_probe=True,
    )
    spec = CharacterSpec.from_mapping({
        "name": "Testknight", "race": "dwarf", "gender": "male",
        "class": "warrior", "subclass": "knight",
    })
    policy = StarterPolicy(spec, "test-only", fastwalk_hunt_stops=(stop,))
    policy.current_room = "927"
    policy.enemy_snapshot_room = "927"
    policy.fastwalk_attack_target = stop.target
    policy.consider_target = stop.target
    policy.consider_target_selector = "#523"
    policy.consider_viable = True
    policy.consider_level_offset_ceiling = 1
    policy.consider_health_warning = True
    enemies = [] if target_hp is None else [{
        "name": "the target", "level": "39", "hp": str(target_hp),
        "maxhp": str(target_hp), "isnpc": "916",
    }]
    state = CharacterState(
        level=39, hp=936, max_hp=936, mana=502, max_mana=502,
        move=583, max_move=583, position=7, room_vnum="927",
        affects=[[{"name": "sanctuary", "duration": "2"}]],
        enemies=[enemies],
    )
    return policy, state


@pytest.mark.parametrize("hp", [0, 100, 1599, 10_000_000])
def test_source_selection_ignores_target_hp(hp):
    mob = candidate(hp)
    state = {"level": 39, "max_hp": 936}
    assert campaign._source_ranked_level_admission_available(
        mob, state, character_level=39, source_world=None,
    )
    assert campaign._source_ranked_candidate_in_current_band(
        mob, state, character_level=39,
    )
    assert not campaign._source_ranked_candidate_requires_sanctuary_for_state(
        mob, state, character_level=39,
    )


@pytest.mark.parametrize("level", [1, 34, 45, 90])
def test_level_rejections_survive_target_hp_change(level):
    assert not campaign._source_ranked_level_admission_available(
        candidate(1, level), {}, character_level=39, source_world=None,
    )


def test_source_plus_five_admission_uses_nominal_level_not_fuzzed_upper_bound():
    target = replace(candidate(level=45), estimated_level_range=(43, 47))

    assert campaign._source_ranked_level_admission_available(
        target, {}, character_level=40, source_world=None,
    )


@pytest.mark.parametrize("hp", [None, 1599, 10_000_000])
def test_viable_consider_opens_without_target_hp_permission(hp):
    policy, state = policy_and_state(hp)
    decision = policy._consider_fastwalk_target(state)
    assert decision is not None
    assert decision.command == "kill #523"
    assert policy.fastwalk_abort_reason is None


def test_oversized_hp_never_orders_escape_after_opening():
    policy, state = policy_and_state(10_000_000)
    policy.combat_active = True
    policy.active_target = "the target"
    policy.active_target_selector = "#523"
    policy.active_target_mobile_vnum = 916
    policy.field_combat_damage_probe_required = True
    policy.field_combat_probe_started_at = 0
    assert policy._live_source_damage_budget_decision(state) is None
    assert policy._damage_window_probe_decision(state) is None


def test_output_capability_does_not_forecast_target_hp(monkeypatch):
    output = SimpleNamespace(
        conservative_damage=10, maximum_actions=12,
        opening_conservative_damage=0, resource="actions", resource_cost=0,
    )
    monkeypatch.setattr(campaign, "_source_ranked_caster_output_for_state", lambda *a, **k: output)
    state = {"max_hp": 1000, "max_mana": 500}
    for hp in (1, 1599, 10_000_000):
        assert campaign._source_ranked_caster_output_can_cover(
            candidate(hp), state, character_level=39,
        )
    # Predicted incoming damage is report evidence, not a target-admission
    # veto; the live health floor remains the combat controller's authority.
    assert campaign._source_ranked_caster_output_can_cover(
        replace(candidate(), estimated_peak_round_damage=10000), state,
        character_level=39,
    )


@pytest.mark.parametrize(
    ("nominal_level", "fuzzed_maximum", "expected"),
    [(40, 42, True), (41, 43, True), (40, 43, True)],
)
def test_poison_special_source_fuzz_only_opens_bounded_scouting(
    nominal_level, fuzzed_maximum, expected,
):
    mob = replace(
        candidate(hp=2100, level=nominal_level),
        estimated_level_range=(nominal_level - 2, fuzzed_maximum),
        estimated_peak_round_damage=504,
        specials=("spec_poison",),
        autonomy_rejections=("target has special procedure spec_poison",),
    )
    admitted = campaign._source_ranked_special_candidate_in_live_level_ceiling(
        mob, character_level=39,
    )
    assert admitted is expected
    if admitted:
        state = {"level": 39, "max_hp": 936, "affects": []}
        assert campaign._audited_source_special_candidate_allowed(
            mob, state=state, character_max_hp=936,
        )
        assert campaign._source_ranked_candidate_in_current_band(
            mob, state, character_level=39,
        )


@pytest.mark.parametrize(
    ("live_level", "expected_command"),
    [(40, "kill #523"), (41, "look")],
)
def test_poison_source_fuzz_still_obeys_live_consider_level(
    live_level, expected_command,
):
    policy, state = policy_and_state()
    policy.fastwalk_hunt_stops = (
        replace(policy.fastwalk_hunt_stops[0], source_specials=("spec_poison",)),
    )
    state.enemies = [[{
        "name": "the target", "level": str(live_level), "hp": "100",
        "maxhp": "100", "isnpc": "916",
    }]]
    decision = policy._consider_fastwalk_target(state)
    assert decision is not None
    assert decision.command == expected_command
    if live_level == 41:
        assert "live level" in (policy.fastwalk_abort_reason or "")


@pytest.mark.parametrize(
    ("consider_ceiling", "expected_command"),
    [(1, "kill #523"), (None, "kill #523"), (5, "kill #523")],
)
def test_poison_source_fuzz_needs_consider_within_live_plus_one(
    consider_ceiling, expected_command,
):
    mob = replace(
        candidate(level=40),
        estimated_level_range=(38, 42),
        specials=("spec_poison",),
        autonomy_rejections=("target has special procedure spec_poison",),
    )
    policy, state = policy_and_state(target_hp=None)
    maximum_offset = campaign._source_ranked_maximum_level_offset(mob)
    policy.fastwalk_hunt_stops = (
        replace(
            policy.fastwalk_hunt_stops[0],
            maximum_level_offset=maximum_offset,
            source_specials=("spec_poison",),
        ),
    )
    policy.source_mobile_level_ranges_by_vnum = {916: (38, 42)}
    policy.consider_level_offset_ceiling = consider_ceiling

    decision = policy._consider_fastwalk_target(state)

    assert maximum_offset == 5
    assert decision is not None
    assert decision.command == expected_command
    if expected_command == "look":
        assert "source mobile range" in (policy.fastwalk_abort_reason or "")


def test_own_health_floor_still_orders_withdrawal():
    policy, state = policy_and_state(10_000_000)
    policy.fastwalk_route = route_named("ambush")
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.active_target = "the target"
    policy.active_target_selector = "#523"
    policy.active_target_mobile_vnum = 916
    policy.active_target_level = 39
    state.hp = 150
    state.in_combat = True
    state.position = 6
    decision = policy.next_decision(state)
    assert decision is not None
    assert decision.command == "flee"


@pytest.mark.parametrize("effect", ["fly", "levitation"])
@pytest.mark.parametrize("duration", [0, 1, 33])
def test_existing_flight_cannot_schedule_redundant_purchase(effect, duration):
    mob = replace(candidate(), requires_flight=True, estimated_flying_move_cost=30)
    state = {"affects": [[{"name": effect, "duration": str(duration)}]]}
    assert not campaign._source_ranked_candidate_needs_flight_refresh(mob, state)
    assert campaign._source_ranked_candidate_needs_flight_refresh(mob, {"affects": []})


def test_sanctuary_expiry_uses_own_health_with_large_target():
    policy, state = policy_and_state(10_000_000)
    policy.fastwalk_route = route_named("ambush")
    policy.active_target = "the target"
    policy.active_target_mobile_vnum = 916
    state.hp = 500
    assert policy._sanctuary_expiry_withdraw_reason(state) is None
    state.hp = 100
    assert "health at or below" in policy._sanctuary_expiry_withdraw_reason(state)
