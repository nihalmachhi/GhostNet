from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from typing import Any

import yaml


@dataclass(frozen=True)
class Action:
    action_id: str
    kind: str
    decoy_type: str
    reason: str
    parameters: dict[str, str | int]


@lru_cache(maxsize=1)
def _allowed() -> dict[str, Any]:
    raw = files("ghostnet.rules").joinpath("allowed_actions.yaml").read_text(encoding="utf-8")
    return yaml.safe_load(raw) or {}


def allowed_actions() -> set[str]:
    return {str(item) for item in _allowed().get("actions", [])}


def validate_parameters(kind: str, parameters: dict[str, str | int]) -> tuple[bool, str]:
    """Validate action parameters without raising on hostile input."""
    if kind == "response_delay_ms":
        raw = parameters.get("delay_ms", 0)
        if isinstance(raw, bool) or not isinstance(raw, (int, str)):
            return False, "delay_ms must be an integer"
        try:
            delay = int(raw)
        except (TypeError, ValueError):
            return False, "delay_ms must be an integer"
        limit = int(_allowed().get("max_response_delay_ms", 250))
        if not 0 <= delay <= limit:
            return False, f"Response delay must be between 0 and {limit}ms"
    if kind == "add_lure":
        text = str(parameters.get("text", ""))
        if len(text) > int(_allowed().get("max_lure_chars", 280)):
            return False, "Lure text exceeds the inert-content length limit"
    return True, "Parameters accepted"


def approve(action: Action) -> tuple[bool, str]:
    """Apply the static allowlist and parameter policy."""
    if action.kind not in allowed_actions():
        return False, "Action is not in the safe allowlist"
    return validate_parameters(action.kind, action.parameters)
