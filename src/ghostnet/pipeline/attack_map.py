from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml


def _raw_rules(rules_path: str | Path | None) -> str:
    if rules_path is not None:
        return Path(rules_path).read_text(encoding="utf-8")
    return files("ghostnet.rules").joinpath("attack_map.yaml").read_text(encoding="utf-8")


@lru_cache(maxsize=4)
def _mapping(raw: str) -> dict[str, list[dict[str, str]]]:
    return yaml.safe_load(raw) or {}


def map_behavior(label: str, rules_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Return observable ATT&CK mappings for a behavior label, cached by file content."""
    return list(_mapping(_raw_rules(rules_path)).get(label, []))
