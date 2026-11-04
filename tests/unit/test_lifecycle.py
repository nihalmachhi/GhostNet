from __future__ import annotations

import subprocess

import pytest

from ghostnet.orchestrator import containment_check, lifecycle


def test_runtime_unavailable_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args: str) -> subprocess.CompletedProcess[str]:
        raise OSError("no docker")

    monkeypatch.setattr(containment_check, "_docker", fail)
    assert containment_check.check_runtime("docker-compose.yml") == [
        "docker_runtime_unavailable:OSError"
    ]


def test_lifecycle_usage(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.argv", ["lifecycle"])
    assert lifecycle.main() == 2
    assert "Usage" in capsys.readouterr().out


def test_lifecycle_refuses_bad_compose(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(lifecycle, "check_compose_config", lambda path: ["bad"])
    monkeypatch.setattr("sys.argv", ["lifecycle", "up"])
    assert lifecycle.main() == 2
