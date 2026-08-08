"""Launch a detached worker with durable stdout and stderr logs."""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess


def _launch_with_windows_shell(
    command: list[str],
    *,
    cwd: Path,
    stdout_path: Path,
    stderr_path: Path,
) -> int:
    launcher_path = stdout_path.with_suffix(stdout_path.suffix + ".launcher.cmd")
    command_line = subprocess.list2cmdline(command)
    launcher_path.write_text(
        "@echo off\r\n"
        f'cd /d "{cwd}"\r\n'
        f'{command_line} 1>>"{stdout_path}" 2>>"{stderr_path}"\r\n'
        'del "%~f0"\r\n',
        encoding="ascii",
    )

    class ShellExecuteInfo(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("fMask", wintypes.ULONG),
            ("hwnd", wintypes.HWND),
            ("lpVerb", wintypes.LPCWSTR),
            ("lpFile", wintypes.LPCWSTR),
            ("lpParameters", wintypes.LPCWSTR),
            ("lpDirectory", wintypes.LPCWSTR),
            ("nShow", ctypes.c_int),
            ("hInstApp", wintypes.HINSTANCE),
            ("lpIDList", ctypes.c_void_p),
            ("lpClass", wintypes.LPCWSTR),
            ("hkeyClass", wintypes.HANDLE),
            ("dwHotKey", wintypes.DWORD),
            ("hIcon", wintypes.HANDLE),
            ("hProcess", wintypes.HANDLE),
        ]

    execute = ShellExecuteInfo()
    execute.cbSize = ctypes.sizeof(execute)
    execute.fMask = 0x00000040  # SEE_MASK_NOCLOSEPROCESS
    execute.lpVerb = "open"
    execute.lpFile = str(launcher_path)
    execute.lpDirectory = str(cwd)
    execute.nShow = 0  # SW_HIDE
    if not ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(execute)):
        raise ctypes.WinError()
    try:
        process_id = ctypes.windll.kernel32.GetProcessId(execute.hProcess)
        if not process_id:
            raise ctypes.WinError()
        return int(process_id)
    finally:
        ctypes.windll.kernel32.CloseHandle(execute.hProcess)


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
        process_id = _launch_with_windows_shell(
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
