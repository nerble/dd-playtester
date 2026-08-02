from pathlib import Path

import re

from tools.conversation_log import append_entry, timestamp, validate


def test_append_entry_uses_the_streamer_header_contract(tmp_path: Path) -> None:
    path = tmp_path / "DEVELOPMENT_CONVERSATION.txt"
    header = append_entry(
        path,
        "CODEX COMMENTARY",
        "A progress update with UTF-8: café.",
    )

    data = path.read_bytes()
    assert f"{header}\r\n".encode("ascii") in data
    assert b"cafe" not in data
    assert validate(path) == 0


def test_timestamp_forces_uppercase_meridiem() -> None:
    assert re.fullmatch(
        r"\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}:\d{2} (?:AM|PM) NZST",
        timestamp(),
    )


def test_validate_rejects_malformed_headerish_lines(tmp_path: Path) -> None:
    path = tmp_path / "DEVELOPMENT_CONVERSATION.txt"
    path.write_bytes(
        b"[2026-08-01 7:00:00 PM NZST] CODEX COMMENTARY\r\n"
        b"good\r\n"
        b"[2026-08-01 7:01:00 PM NZST] CODEX COMMENTARY EXTRA\r\n"
        b"bad\r\n"
    )

    assert validate(path) == 1


def test_validate_allows_legacy_header_text_inside_append_only_history(
    tmp_path: Path,
) -> None:
    path = tmp_path / "DEVELOPMENT_CONVERSATION.txt"
    path.write_bytes(
        b"[Codex | 11:39:57 AM +12:00]\r\n"
        b"legacy body\r\n"
        b"[2026-08-01 7:00:00 PM NZST] CODEX COMMENTARY\r\n"
        b"current body\r\n"
    )

    assert validate(path) == 0
