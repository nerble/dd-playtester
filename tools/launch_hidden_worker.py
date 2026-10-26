"""Launch a detached worker with durable stdout and stderr logs."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess


def _launch_with_windows(
    command: list[str],
    *,
    cwd: Path,
    stdout_path: Path,
    stderr_path: Path,
) -> int:
    # Keep the reported PID attached to the actual worker so watchdog cleanup
    # cannot strand a hidden command-wrapper process.
    creationflags = (
        subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    )
    with stdout_path.open("ab", buffering=0) as stdout_file, stderr_path.open(
        "ab", buffering=0
    ) as stderr_file:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=stdout_file,
            stderr=stderr_file,
            close_fds=False,
            creationflags=creationflags,
        )
    return process.pid


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", type=Path, required=True)
    parser.add_argument("--stdout", type=Path, required=True)
    parser.add_argument("--stderr", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    command = list(args.command)
    if command[:1] == ["--"]:
        command.pop(0)
    if not command:
        parser.error("a worker command is required after --")

    stdout_path = args.stdout.resolve()
    stderr_path = args.stderr.resolve()
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        process_id = _launch_with_windows(
            command,
            cwd=args.cwd.resolve(),
            stdout_path=stdout_path,
            stderr_path=stderr_path,
        )
    else:
        with stdout_path.open("ab", buffering=0) as stdout_file, stderr_path.open(
            "ab",
            buffering=0,
        ) as stderr_file:
            process = subprocess.Popen(
                command,
                cwd=args.cwd.resolve(),
                stdin=subprocess.DEVNULL,
                stdout=stdout_file,
                stderr=stderr_file,
                close_fds=True,
                start_new_session=True,
            )
        process_id = process.pid

    print(
        json.dumps(
            {
                "pid": process_id,
                "stdout": str(stdout_path),
                "stderr": str(stderr_path),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
