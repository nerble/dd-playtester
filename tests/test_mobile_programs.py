from dataclasses import replace

import pytest

from dd4tester.hunt_candidates import MobileProgram
from dd4tester.mobile_programs import (
    greeting_display_programs_only,
    greeting_echo_programs_only,
    idle_echo_programs_only,
    noncombat_echo_programs_only,
)


IDLE_ECHO = MobileProgram(
    "rand_prog", "10",
    ("if isfight($i)", "break", "else", "mpecho $I asks for aspirin.", "endif"),
)


DISPLAY_GREETING = MobileProgram(
    "all_greet_prog", "100",
    ("say Squeak. Time to die you fool. Squeak.", "emote draws its sword."),
)


def test_display_greeting_requires_explicit_bounded_output_commands() -> None:
    assert greeting_display_programs_only((DISPLAY_GREETING,))
    assert greeting_display_programs_only((replace(DISPLAY_GREETING, trigger="greet_prog"),))
    assert not greeting_display_programs_only(())
    assert not greeting_display_programs_only((DISPLAY_GREETING,) * 5)
    assert not greeting_echo_programs_only((DISPLAY_GREETING,))


@pytest.mark.parametrize("program", [
    replace(DISPLAY_GREETING, trigger="fight_prog"),
    replace(DISPLAY_GREETING, trigger="speech_prog"),
    replace(DISPLAY_GREETING, condition="101"),
    replace(DISPLAY_GREETING, condition="unknown"),
    replace(DISPLAY_GREETING, commands=("say",)),
    replace(DISPLAY_GREETING, commands=("mpkill $n",)),
    replace(DISPLAY_GREETING, commands=("mptransfer $n 3001",)),
    replace(DISPLAY_GREETING, commands=("cast poison $n",)),
    replace(DISPLAY_GREETING, commands=("if ispc($n)", "say Hello.", "endif")),
    replace(DISPLAY_GREETING, commands=("say hello\nmpkill $n",)),
    replace(DISPLAY_GREETING, commands=("say hello\rmpkill $n",)),
    replace(DISPLAY_GREETING, commands=("emote waves.",) * 9),
])
def test_display_greeting_rejects_other_actions_or_control_flow(program) -> None:
    assert not greeting_display_programs_only((program,))
    assert not greeting_display_programs_only((DISPLAY_GREETING, program))


def test_idle_echo_proof_accepts_empty_and_exact_noncombat_scripts() -> None:
    assert idle_echo_programs_only(())
    assert idle_echo_programs_only((IDLE_ECHO,))
    assert idle_echo_programs_only((IDLE_ECHO, IDLE_ECHO))


@pytest.mark.parametrize("program", [
    replace(IDLE_ECHO, trigger="fight_prog"),
    replace(IDLE_ECHO, trigger="greet_prog"),
    replace(IDLE_ECHO, condition="101"),
    replace(IDLE_ECHO, condition="unknown"),
    replace(IDLE_ECHO, commands=("mpecho hello",)),
    replace(IDLE_ECHO, commands=("if !isfight($i)", *IDLE_ECHO.commands[1:])),
    replace(IDLE_ECHO, commands=("if isfight($n)", *IDLE_ECHO.commands[1:])),
    replace(IDLE_ECHO, commands=(*IDLE_ECHO.commands[:3], "mpkill $n", "endif")),
    replace(IDLE_ECHO, commands=(*IDLE_ECHO.commands[:3], "mpforce $n sleep", "endif")),
    replace(IDLE_ECHO, commands=(*IDLE_ECHO.commands[:3], "mpecho", "endif")),
    replace(IDLE_ECHO, commands=(*IDLE_ECHO.commands[:3], "mpecho CHAT hello", "endif")),
    replace(IDLE_ECHO, commands=(*IDLE_ECHO.commands, "cast poison $n")),
])
def test_idle_echo_proof_rejects_other_actions_or_control_flow(program: MobileProgram) -> None:
    assert not idle_echo_programs_only((program,))
    assert not idle_echo_programs_only((IDLE_ECHO, program))


GREETING_ECHO = MobileProgram(
    "all_greet_prog", "50",
    ("if rand(33)", "mpecho $I asks for help.", "else", "if rand(50)",
     "mpecho $I recalls home.", "else", "mpecho $I warns you.", "endif", "endif"),
)


def test_greeting_proof_accepts_only_balanced_bounded_echo_branches() -> None:
    assert greeting_echo_programs_only((GREETING_ECHO,))
    assert greeting_echo_programs_only((replace(GREETING_ECHO, trigger="greet_prog"),))
    assert noncombat_echo_programs_only((GREETING_ECHO, IDLE_ECHO))
    assert noncombat_echo_programs_only(())
    assert not greeting_echo_programs_only(())
    assert not idle_echo_programs_only((GREETING_ECHO,))


@pytest.mark.parametrize("program", [
    replace(GREETING_ECHO, trigger="fight_prog"),
    replace(GREETING_ECHO, trigger="rand_prog"),
    replace(GREETING_ECHO, condition="101"),
    replace(GREETING_ECHO, condition="someone"),
    replace(GREETING_ECHO, commands=("mpkill $n",)),
    replace(GREETING_ECHO, commands=("mptransfer $n 3001",)),
    replace(GREETING_ECHO, commands=("cast poison $n",)),
    replace(GREETING_ECHO, commands=("mpecho CHAT hello",)),
    replace(GREETING_ECHO, commands=("mpecho",)),
    replace(GREETING_ECHO, commands=("if rand(101)", "mpecho hello", "endif")),
    replace(GREETING_ECHO, commands=("else", "mpecho hello")),
    replace(GREETING_ECHO, commands=("if rand(50)", "mpecho hello")),
    replace(GREETING_ECHO, commands=("mpecho hello", "endif")),
    replace(GREETING_ECHO, commands=("if rand(50)", "else", "else", "mpecho hello", "endif")),
    replace(GREETING_ECHO, commands=("if ispc($n)", "mpecho hello", "endif")),
    replace(GREETING_ECHO, commands=("mpecho hello",) * 33),
    replace(GREETING_ECHO, commands=("if rand(50)",) * 5 + ("mpecho hello",) + ("endif",) * 5),
])
def test_greeting_proof_rejects_actions_unknown_conditions_and_malformed_blocks(
    program: MobileProgram,
) -> None:
    assert not greeting_echo_programs_only((program,))
    assert not noncombat_echo_programs_only((IDLE_ECHO, program))


def test_greeting_proof_rejects_unbounded_program_counts() -> None:
    assert not greeting_echo_programs_only((GREETING_ECHO,) * 5)
    assert not noncombat_echo_programs_only((GREETING_ECHO,) * 5)
