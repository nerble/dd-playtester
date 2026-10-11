import pytest

from dd4tester.character import CharacterSpec
from dd4tester.fastwalks import route_named
from dd4tester.hunt_candidates import MobileSource, WorldSource
from dd4tester.starter import FieldHuntStop, StarterPolicy, _incoming_attack_match


NAME = "Teacher's last student"


@pytest.mark.parametrize("line", [
    NAME + " misses you.",
    NAME + " decimates you!",
    NAME + "'s punch scratches you.",
    NAME + "'s poisoned kick wounds you!",
])
def test_source_known_possessive_name_is_not_truncated(line: str) -> None:
    match = _incoming_attack_match(line, known_direct_names=(NAME,))
    assert match is not None
    assert match.group("attacker") == NAME


def test_unbound_ambiguous_name_keeps_conservative_possessive_parsing() -> None:
    match = _incoming_attack_match(NAME + " misses you.")
    assert match is not None
    assert match.group("attacker") == "Teacher"


def test_real_possessive_attack_noun_is_not_added_to_the_attacker_name() -> None:
    match = _incoming_attack_match("An imp's fireball hits you.", known_direct_names=(NAME,))
    assert match.group("attacker") == "An imp"


def test_secondary_attacker_is_not_hidden_by_earlier_correct_primary() -> None:
    match = _incoming_attack_match(NAME + " misses you.\nAn imp's fireball hits you.\n",
                                   known_direct_names=(NAME,))
    assert match.group("attacker") == "An imp"


def _policy():
    mobile = MobileSource(10726, "student teacher", NAME, 30, 0, 0, "test.are")
    stop = FieldHuntStop((), NAME, source_mobile_vnum=10726,
                         source_reset_room_vnum="10786")
    policy = StarterPolicy(
        CharacterSpec("NameTest", "TEST_PASSWORD", "human", "neuter", "warrior"),
        "test-password", fastwalk_route=route_named("moria"),
        fastwalk_hunt_stops=(stop,), source_world=WorldSource(mobiles={10726: mobile}),
    )
    policy.current_room = "10786"
    policy.fastwalk_attack_started = True
    policy.fastwalk_attack_target = NAME
    policy.active_target = NAME
    policy.active_target_mobile_vnum = 10726
    policy.combat_active = True
    return policy


def test_live_policy_does_not_invent_teacher_from_the_students_direct_miss() -> None:
    policy = _policy()
    policy.observe_text(NAME + " misses you.\n" + NAME + " decimates you!\n")
    assert policy.unapproved_field_attacker is None
    assert policy.active_target == NAME
    assert policy.combat_active


def test_live_policy_still_rejects_an_actual_attacker_named_teacher() -> None:
    policy = _policy()
    policy.observe_text("Teacher hits you.\n")
    assert policy.unapproved_field_attacker == "Teacher"


def test_source_name_parsing_does_not_clear_an_existing_attacker_failure() -> None:
    policy = _policy()
    policy.unapproved_field_attacker = "An imp"
    policy.observe_text(NAME + " misses you.\n")
    assert policy.unapproved_field_attacker == "An imp"
