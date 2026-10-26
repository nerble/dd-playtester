from pathlib import Path
import subprocess

import pytest

from tools.launch_hidden_worker import _launch_with_windows


@pytest.mark.skipif(
    not hasattr(subprocess, "CREATE_NO_WINDOW"),
    reason="Windows worker flags are unavailable on non-Windows hosts",
)
def test_windows_launcher_reports_actual_worker_pid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, object] = {}

    class FakeProcess:
        pid = 4321

    def fake_popen(command: list[str], **kwargs: object) -> FakeProcess:
        captured["command"] = command
        captured.update(kwargs)
        return FakeProcess()

    stdout_path = tmp_path / "worker.out"
    stderr_path = tmp_path / "worker.err"
    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    assert (
        _launch_with_windows(
            ["python", "-m", "dd4tester", "hero"],
            cwd=tmp_path,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
        )
        == 4321
    )
    assert captured["command"] == ["python", "-m", "dd4tester", "hero"]
    assert captured["cwd"] == tmp_path
    assert captured["stdin"] is subprocess.DEVNULL
    assert captured["close_fds"] is False
    assert captured["creationflags"] == (
        subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    )
    assert not list(tmp_path.glob("*.launcher.cmd"))
