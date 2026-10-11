from __future__ import annotations

from pathlib import Path

import yaml


def map_behavior(label: str, rules_path: str | Path | None = None) -> list[dict[str, str]]:
    path = (
        Path(rules_path)
        if rules_path
        else Path(__file__).resolve().parents[2] / "rules" / "attack_map.yaml"
    )
    mapping: dict[str, list[dict[str, str]]] = (
        yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    )
    return mapping.get(label, [])
