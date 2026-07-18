from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO


@dataclass(frozen=True)
class TranscriptEvent:
    timestamp: str
    kind: str
    payload: dict[str, Any]


class TranscriptRecorder:
    def __init__(self, path: Path, *, run_id: int) -> None:
        self.path = path
        self.run_id = run_id
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file: TextIO = self.path.open("a", encoding="utf-8")

    @classmethod
    def create(cls, base_dir: Path, *, scenario_name: str, run_id: int) -> "TranscriptRecorder":
        safe_name = "".join(char if char.isalnum() or char in ("-", "_") else "-" for char in scenario_name)
        path = base_dir / f"{safe_name}-{run_id}.jsonl"
        return cls(path, run_id=run_id)

    def record(self, kind: str, payload: dict[str, Any]) -> TranscriptEvent:
        event = TranscriptEvent(
            timestamp=datetime.now(UTC).isoformat(),
            kind=kind,
            payload=payload,
        )
        self._file.write(
            json.dumps(
                {
                    "timestamp": event.timestamp,
                    "run_id": self.run_id,
                    "kind": event.kind,
                    "payload": event.payload,
                },
                sort_keys=True,
            )
            + "\n"
        )
        self._file.flush()
        return event

    def close(self) -> None:
        self._file.close()

    def __enter__(self) -> "TranscriptRecorder":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
