from __future__ import annotations

import sys
from pathlib import Path

import pytest

from ghostnet import cli


def _run(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], *args: str) -> str:
    monkeypatch.setattr(sys, "argv", ["ghostnet", *args])
    assert cli.main() == 0
    return capsys.readouterr().out


def test_checkpoint_export(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    output = _run(
        monkeypatch,
        capsys,
        "export-checkpoint",
        "--database",
        str(tmp_path / "db.sqlite"),
    )
    assert "verified" in output


def test_navigator_stix_csv_and_purge(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    database = str(tmp_path / "db.sqlite")
    assert "techniques" in _run(monkeypatch, capsys, "export-navigator", "--database", database)
    assert "bundle" in _run(monkeypatch, capsys, "export-stix", "--database", database)
    assert "class_label" in _run(monkeypatch, capsys, "export-csv", "--database", database)
    assert "purged" in _run(monkeypatch, capsys, "purge", "--database", database)


def test_export_to_file(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    out = tmp_path / "checkpoint.json"
    _run(
        monkeypatch,
        capsys,
        "export-checkpoint",
        "--database",
        str(tmp_path / "db.sqlite"),
        "--out",
        str(out),
    )
    assert out.exists()
