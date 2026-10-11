from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Action:
    action_id: str
    kind: str
    decoy_type: str
    reason: str
    parameters: dict[str, str | int]


ALLOWED_ACTIONS = {"rotate_fake_credential", "add_lure", "change_banner", "response_delay_ms"}


def approve(action: Action) -> tuple[bool, str]:
    if action.kind not in ALLOWED_ACTIONS:
        return False, "Action is not in the safe allowlist"
    if action.kind == "response_delay_ms":
        delay = int(action.parameters.get("delay_ms", 0))
        if not 0 <= delay <= 250:
            return False, "Response delay must be between 0 and 250ms"
    if action.kind == "add_lure" and len(str(action.parameters.get("text", ""))) > 280:
        return False, "Lure text exceeds the inert-content length limit"
    return True, "Approved by static policy"
