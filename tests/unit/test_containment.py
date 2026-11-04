from __future__ import annotations

from pathlib import Path

import yaml

from ghostnet.orchestrator.containment_check import check_compose_config

ROOT = Path(__file__).resolve().parents[2]


def test_repository_compose_passes() -> None:
    assert check_compose_config(ROOT / "docker-compose.yml") == []


def test_privileged_decoy_is_rejected(tmp_path: Path) -> None:
    document = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    document["services"]["web-admin"]["privileged"] = True
    path = tmp_path / "compose.yml"
    path.write_text(yaml.safe_dump(document), encoding="utf-8")
    assert "web-admin:not_privileged" in check_compose_config(path)


def test_public_binding_and_network_are_rejected(tmp_path: Path) -> None:
    document = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    document["services"]["edge"]["ports"] = ["0.0.0.0:8081:8081"]
    document["networks"]["deception"]["internal"] = False
    path = tmp_path / "compose.yml"
    path.write_text(yaml.safe_dump(document), encoding="utf-8")
    failures = check_compose_config(path)
    assert "edge:loopback_port_binding" in failures
    assert any(item.endswith(":network_internal") for item in failures)


def test_admin_on_deception_network_is_rejected(tmp_path: Path) -> None:
    document = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    document["services"]["admin-api"]["networks"] = ["control", "deception"]
    path = tmp_path / "compose.yml"
    path.write_text(yaml.safe_dump(document), encoding="utf-8")
    assert "admin-api:reachable_from_deception" in check_compose_config(path)
