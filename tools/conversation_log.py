"""Append and validate the Discord-facing development conversation log."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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


def append_entry(path: Path, speaker: str, body: str) -> str:
    if speaker not in SPEAKERS:
        raise ValueError(f"speaker must be one of: {', '.join(SPEAKERS)}")
    clean_body = body.rstrip("\r\n")
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
    body = append.add_mutually_exclusive_group(required=True)
    body.add_argument("--body")
    body.add_argument("--body-file", type=Path)
    subparsers.add_parser("validate")
    args = parser.parse_args(argv)

    if args.command == "append":
        header = append_entry(
            args.path,
            args.speaker,
            args.body
            if args.body is not None
            else args.body_file.read_text(encoding="utf-8"),
        )
        print(header)
        return 0
    return validate(args.path)


if __name__ == "__main__":
    sys.exit(main())
