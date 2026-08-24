from __future__ import annotations

import errno
import hashlib
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import IO


class CampaignLeaseBusyError(RuntimeError):
    """Raised when another process owns the same campaign lease."""


class CampaignLease:
    """Hold an OS-backed, process-scoped lease for one campaign config."""

    def __init__(self, path: Path, *, timeout: float = 0.0) -> None:
        if timeout < 0:
            raise ValueError("lease timeout cannot be negative")
        self.path = path
        self.timeout = timeout
        self._handle: IO[bytes] | None = None
        self._locked = False

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+b")
        try:
            if handle.seek(0, os.SEEK_END) < 1:
                handle.write(b"\0")
                handle.flush()
            deadline = time.monotonic() + self.timeout
            while True:
                try:
                    self._lock_handle(handle)
                except OSError as exc:
                    if not _is_lock_contention(exc):
                        raise
                    if time.monotonic() >= deadline:
                        raise CampaignLeaseBusyError(
                            f"campaign lease is already held: {self.path}"
                        ) from None
                    time.sleep(min(0.05, max(0.0, deadline - time.monotonic())))
                else:
                    self._handle = handle
                    self._locked = True
                    self._write_owner(handle)
                    return
        except BaseException:
            handle.close()
            raise

    def release(self) -> None:
        handle = self._handle
        if handle is None:
            return
        try:
            if self._locked:
                self._unlock_handle(handle)
        finally:
            self._locked = False
            self._handle = None
            handle.close()

    def __enter__(self) -> "CampaignLease":
        self.acquire()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.release()

    @staticmethod
    def _lock_handle(handle: IO[bytes]) -> None:
        handle.seek(0)
        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            return
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    @staticmethod
    def _unlock_handle(handle: IO[bytes]) -> None:
        handle.seek(0)
        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            return
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _write_owner(handle: IO[bytes]) -> None:
        owner = (
            f"pid={os.getpid()} "
            f"started={datetime.now(UTC).isoformat()}\n"
        ).encode("ascii")
        handle.seek(0)
        handle.truncate()
        handle.write(owner)
        handle.flush()


def campaign_lease_path(database: Path, config_path: Path) -> Path:
    """Return a stable lock path without serializing unrelated campaigns."""
    identity = str(config_path.resolve()).encode("utf-8")
    digest = hashlib.sha256(identity).hexdigest()[:16]
    database = database.resolve()
    return database.parent / ".campaign-leases" / f"{database.stem}-{digest}.lock"


def _is_lock_contention(exc: OSError) -> bool:
    if isinstance(exc, (BlockingIOError, PermissionError)):
        return True
    if exc.errno in {errno.EACCES, errno.EAGAIN, errno.EWOULDBLOCK}:
        return True
    return getattr(exc, "winerror", None) in {32, 33}
