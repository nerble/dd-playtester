import io
import sys
from pathlib import Path

import pytest
import re

from tools.conversation_log import append_entry, main, timestamp, validate


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


def test_append_entry_rejects_nested_streamer_header(tmp_path: Path) -> None:
    path = tmp_path / "DEVELOPMENT_CONVERSATION.txt"

    with pytest.raises(ValueError, match="must not contain"):
        append_entry(
            path,
            "CODEX COMMENTARY",
            "[2026-08-13 8:34:40 PM NZST] USER\nOld message",
        )

    assert not path.exists()


def test_append_command_reads_unicode_body_from_stdin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "DEVELOPMENT_CONVERSATION.txt"
    monkeypatch.setattr(sys, "stdin", io.StringIO("Don't lose the user's exact words: café.\n"))

    assert main(
        ["--path", str(path), "append", "--speaker", "CODEX COMMENTARY", "--body-stdin"]
    ) == 0

    output = capsys.readouterr().out
    assert " CODEX COMMENTARY\n" in path.read_text(encoding="utf-8")
    assert "Don't lose the user's exact words: café." in path.read_text(encoding="utf-8")
    assert " NZST\n" in output


def test_append_command_decodes_utf8_pipe_bytes_on_windows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "DEVELOPMENT_CONVERSATION.txt"
    message = "Exact punctuation: " + chr(0x2019) + " café."
    raw_stdin = io.BytesIO((message + "\n").encode("utf-8"))
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(raw_stdin, encoding="cp1252"))

    assert main(
        ["--path", str(path), "append", "--speaker", "CODEX COMMENTARY", "--body-stdin"]
    ) == 0

    assert message in path.read_text(encoding="utf-8")


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
