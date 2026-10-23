"""Narrow source proofs for mobile scripts with no combat effects."""

from __future__ import annotations

import re
from collections.abc import Collection

from .hunt_candidates import MobileProgram


_RANDOM_BRANCH = re.compile(r"if rand\(([0-9]{1,3})\)", re.IGNORECASE)


def greeting_echo_programs_only(programs: Collection[MobileProgram]) -> bool:
    """Prove bounded greeting scripts contain only random branches and echoes."""
    if not programs or len(programs) > 4:
        return False
    for program in programs:
        if (
            program.trigger.casefold() not in {"greet_prog", "all_greet_prog"}
            or not program.condition.isdecimal()
            or not 0 <= int(program.condition) <= 100
            or not 1 <= len(program.commands) <= 32
        ):
            return False
        branches: list[bool] = []
        echoed = False
        for line in program.commands:
            command = " ".join(line.split())
            branch = _RANDOM_BRANCH.fullmatch(command)
            if branch is not None:
                if int(branch[1]) > 100 or len(branches) >= 4:
                    return False
                branches.append(False)
            elif command.casefold() == "else":
                if not branches or branches[-1]:
                    return False
                branches[-1] = True
            elif command.casefold() == "endif":
                if not branches:
                    return False
                branches.pop()
            else:
                verb, separator, body = command.partition(" ")
                if (
                    verb.casefold() != "mpecho" or not separator or not body
                    or body.split(" ", 1)[0].casefold() == "chat"
                ):
                    return False
                echoed = True
        if branches or not echoed:
            return False
    return True


def noncombat_echo_programs_only(programs: Collection[MobileProgram]) -> bool:
    """Accept the existing idle proof or the separate greeting-only grammar."""
    if idle_echo_programs_only(programs):
        return True
    return len(programs) <= 4 and all(
        idle_echo_programs_only((program,))
        or greeting_echo_programs_only((program,))
        for program in programs
    )


def source_reviewed_noncombat_programs_only(
    programs: Collection[MobileProgram],
) -> bool:
    """Prove the narrow, source-reviewed speech-and-give script shape.

    This is intentionally separate from the general idle/greeting proof. It
    admits only bounded speech triggers plus the exact ``give_prog ruby eye``
    handoff used by the reviewed passive prototype; no movement, combat,
    spell, force, or arbitrary object commands are accepted.
    """
    if not 1 <= len(programs) <= 3:
        return False

    def echo_command(command: str) -> bool:
        verb, separator, body = " ".join(command.split()).partition(" ")
        return bool(
            separator
            and body
            and verb.casefold() in {"say", "mpasound", "mpecho"}
        )

    for program in programs:
        trigger = program.trigger.casefold()
        condition = " ".join(program.condition.split()).casefold()
        commands = tuple(" ".join(command.split()) for command in program.commands)
        if trigger == "rand_prog":
            if (
                not program.condition.isdecimal()
                or not 0 <= int(program.condition) <= 100
                or len(commands) != 1
                or not echo_command(commands[0])
            ):
                return False
            continue
        if trigger in {"greet_prog", "all_greet_prog"}:
            if (
                not program.condition.isdecimal()
                or not 0 <= int(program.condition) <= 100
                or not 1 <= len(commands) <= 8
                or not all(echo_command(command) for command in commands)
            ):
                return False
            continue
        if trigger == "give_prog":
            if (
                condition != "ruby eye"
                or not 1 <= len(commands) <= 8
                or commands[-1].casefold() != "mpjunk ruby"
                or not all(
                    echo_command(command)
                    for command in commands[:-1]
                )
            ):
                return False
            continue
        return False
    return True


def idle_echo_programs_only(programs: Collection[MobileProgram]) -> bool:
    """Accept only random scripts that stop in combat and otherwise echo once."""
    for program in programs:
        commands = tuple(" ".join(line.split()) for line in program.commands)
        if (
            program.trigger.casefold() != "rand_prog"
            or not program.condition.isdecimal()
            or not 0 <= int(program.condition) <= 100
            or len(commands) != 5
            or commands[0].casefold() != "if isfight($i)"
            or commands[1].casefold() != "break"
            or commands[2].casefold() != "else"
            or commands[4].casefold() != "endif"
        ):
            return False
        command, separator, body = commands[3].partition(" ")
        if (
            command.casefold() != "mpecho" or not separator or not body
            or body.split(" ", 1)[0].casefold() == "chat"
        ):
            return False
    return True
