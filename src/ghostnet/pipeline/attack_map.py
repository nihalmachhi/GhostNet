from __future__ import annotations

from importlib.resources import files
from pathlib import Path

import yaml


def map_behavior(label: str, rules_path: str | Path | None = None) -> list[dict[str, str]]:
    if rules_path is not None:
        raw = Path(rules_path).read_text(encoding="utf-8")
    else:
        raw = files("ghostnet.rules").joinpath("attack_map.yaml").read_text(encoding="utf-8")
    mapping: dict[str, list[dict[str, str]]] = yaml.safe_load(raw) or {}
    return mapping.get(label, [])
