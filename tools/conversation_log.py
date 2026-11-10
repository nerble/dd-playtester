"""Append and validate the Discord-facing development conversation log."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import os
import re
import sys
import tempfile
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

if os.name == "nt":
    import msvcrt
else:
    import fcntl

SPEAKERS = ("USER", "CODEX COMMENTARY", "CODEX FINAL")
HEADER_RE = re.compile(
    rb"^\[\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}:\d{2} "
    rb"(?:AM|PM) NZST\] (?:USER|CODEX COMMENTARY|CODEX FINAL)$"
)
HEADERISH_RE = re.compile(rb"^\[")
CURRENT_HEADERISH_RE = re.compile(
    rb"^\[\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}:\d{2} "
    rb"(?:AM|PM) NZST\] "
    rb"[A-Z][A-Z0-9 _-]{1,60}\s*$"
)
TIMESTAMPED_BODY_LINE_RE = re.compile(
    rb"^\[\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}:\d{2} "
    rb"(?:AM|PM) NZST\]\s*",
    re.IGNORECASE,
)
RECENT_RECORD_CHECK_BYTES = 256_000
RECENT_BODY_DEDUPE_RECORDS = 128


@contextmanager
def _append_lock(path: Path):
    """Serialize duplicate checks and appends across concurrent Codex writers."""
    key = hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()
    lock_path = Path(tempfile.gettempdir()) / f"dd4-conversation-{key}.lock"
    with lock_path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _canonical_assistant_body(body: str) -> str:
    """Normalize harmless prose variations for duplicate detection only."""
    normalized = unicodedata.normalize("NFKC", body)
    normalized = normalized.translate(
        str.maketrans(
            {
                "\u2018": "'",
                "\u2019": "'",
                "\u201c": '"',
                "\u201d": '"',
                "\u2013": "-",
                "\u2014": "-",
                "\u2026": "...",
            }
        )
    ).casefold()
    for pattern, replacement in (
        (r"\bi'm\b", "i am"),
        (r"\byou're\b", "you are"),
        (r"\bwe're\b", "we are"),
        (r"\bthey're\b", "they are"),
        (r"\bit's\b", "it is"),
        (r"\bthat's\b", "that is"),
        (r"\bcan't\b", "cannot"),
        (r"\bdon't\b", "do not"),
        (r"\bdoesn't\b", "does not"),
        (r"\bdidn't\b", "did not"),
        (r"\bwon't\b", "will not"),
        (r"\bshouldn't\b", "should not"),
    ):
        normalized = re.sub(pattern, replacement, normalized)
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    return " ".join(normalized.split())


def timestamp() -> str:
    try:
        now = datetime.now(ZoneInfo("Pacific/Auckland"))
    except ZoneInfoNotFoundError:
        # Windows Python installations may not bundle IANA tzdata. This
        # machine is configured for Pacific/Auckland, so retain its local DST
        # offset while keeping the repository's required NZST label.
        now = datetime.now().astimezone()
    hour = now.hour % 12 or 12
    meridiem = now.strftime("%p").upper()
    return f"{now:%Y-%m-%d} {hour}:{now:%M:%S} {meridiem} NZST"


def _recent_records(
    path: Path, *, limit: int = RECENT_BODY_DEDUPE_RECORDS
) -> list[tuple[str, str]]:
    """Read a bounded tail of complete records without loading the history."""
    if not path.exists():
        return []
    size = path.stat().st_size
    with path.open("rb") as handle:
        handle.seek(max(0, size - RECENT_RECORD_CHECK_BYTES))
        data = handle.read()
    lines = data.splitlines(keepends=True)
    header_indexes = [
        index
        for index, line in enumerate(lines)
        if HEADER_RE.fullmatch(line.rstrip(b"\r\n"))
    ]
    records: list[tuple[str, str]] = []
    for position, index in enumerate(header_indexes):
        header_line = lines[index].rstrip(b"\r\n")
        header = header_line.decode("utf-8")
        speaker = header.rsplit("] ", 1)[-1]
        end = (
            header_indexes[position + 1]
            if position + 1 < len(header_indexes)
            else len(lines)
        )
        body = b"".join(lines[index + 1 : end]).rstrip().decode("utf-8")
        records.append((speaker, body))
    return records[-limit:]


def _last_record(path: Path) -> tuple[str, str] | None:
    """Read the last complete record without loading the whole history."""
    records = _recent_records(path, limit=1)
    return records[-1] if records else None


def append_entry(path: Path, speaker: str, body: str) -> str:
    if speaker not in SPEAKERS:
        raise ValueError(f"speaker must be one of: {', '.join(SPEAKERS)}")
    clean_body = body.rstrip("\r\n")
    for line in clean_body.encode("utf-8").splitlines():
        if HEADER_RE.fullmatch(line) or CURRENT_HEADERISH_RE.fullmatch(line):
            raise ValueError("body must not contain a timestamped speaker header")
        if speaker != "USER" and TIMESTAMPED_BODY_LINE_RE.match(line):
            raise ValueError(
                "outgoing assistant body must not contain a nested timestamped line"
            )
    with _append_lock(path):
        if speaker != "USER":
            recent_records = _recent_records(path)
            canonical_body = _canonical_assistant_body(clean_body)
            canonical_recent = {
                (recent_speaker, _canonical_assistant_body(recent_body))
                for recent_speaker, recent_body in recent_records
                if recent_speaker != "USER"
            }
            if recent_records and recent_records[-1] == (speaker, clean_body):
                raise ValueError("consecutive duplicate assistant body")
            if (speaker, canonical_body) in canonical_recent:
                raise ValueError("repeated assistant body in recent conversation")
        header = f"[{timestamp()}] {speaker}"
        entry = f"\r\n\r\n{header}\r\n{clean_body}\r\n"
        with path.open("ab") as handle:
            handle.write(entry.encode("utf-8"))
        return header


def validate(path: Path) -> int:
    data = path.read_bytes()
    lines = data.splitlines()
    valid = 0
    malformed: list[tuple[int, bytes]] = []
    legacy = 0
    for line_number, line in enumerate(lines, 1):
        if not HEADERISH_RE.match(line):
            continue
        if HEADER_RE.fullmatch(line):
            valid += 1
        elif line.endswith(b"] USER STEERING"):
            legacy += 1
        elif CURRENT_HEADERISH_RE.fullmatch(line):
            malformed.append((line_number, line[:160]))
        else:
            legacy += 1
    print(f"path={path}")
    print(f"bytes={len(data)}")
    print(f"valid_headers={valid}")
    print(f"legacy_headerish_lines={legacy}")
    print(f"malformed_headerish_lines={len(malformed)}")
    for line_number, line in malformed[:20]:
        print(f"malformed[{line_number}]={line.decode('latin1')}")
    return 1 if malformed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("DEVELOPMENT_CONVERSATION.txt"),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    append = subparsers.add_parser("append")
    append.add_argument("--speaker", choices=SPEAKERS, required=True)
    append.add_argument(
        "--quiet",
        action="store_true",
        help="append the record without printing its generated header",
    )
    body = append.add_mutually_exclusive_group(required=True)
    body.add_argument("--body")
    body.add_argument("--body-file", type=Path)
    body.add_argument(
        "--body-stdin",
        action="store_true",
        help="read the message body from standard input",
    )
    subparsers.add_parser("validate")
    args = parser.parse_args(argv)

    if args.command == "append":
        if args.body is not None:
            message_body = args.body
        elif args.body_file is not None:
            message_body = args.body_file.read_text(encoding="utf-8")
        else:
            stdin_buffer = getattr(sys.stdin, "buffer", None)
            if stdin_buffer is None:
                message_body = sys.stdin.read()
            else:
                message_body = stdin_buffer.read().decode("utf-8")
        header = append_entry(args.path, args.speaker, message_body)
        if not args.quiet:
            print(header)
        return 0
    return validate(args.path)


if __name__ == "__main__":
    sys.exit(main())
