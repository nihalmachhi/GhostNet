from __future__ import annotations

import json
from typing import Any

from ghostnet.sensors.privacy import credential_summary, hash_source
from ghostnet.sensors.schema import EventIn

COWRIE_EVENTS = {
    "cowrie.login.success": "auth_attempt",
    "cowrie.login.failed": "auth_attempt",
    "cowrie.command.input": "command",
    "cowrie.session.connect": "conn_open",
}


def cowrie_to_event(record: dict[str, Any], secret: str) -> EventIn | None:
    """Normalize one Cowrie JSON record without retaining raw credentials.

    The adapter is for evaluation against public, licensed Cowrie-style logs.
    It never writes the original record.
    """
    kind = COWRIE_EVENTS.get(str(record.get("eventid", "")))
    if kind is None:
        return None
    source = str(record.get("src_ip", "unknown"))
    session = str(record.get("session", "cowrie-session"))[:120]
    data: dict[str, Any]
    if kind == "auth_attempt":
        data = dict(
            credential_summary(str(record.get("username", "")), str(record.get("password", "")))
        )
    elif kind == "command":
        data = {"command": str(record.get("input", "")).split(" ", 1)[0][:80].upper()}
    else:
        data = {"service": "cowrie"}
    return EventIn(
        decoy_id="cowrie-adapter",
        decoy_type="cowrie",
        session_id=session,
        src_hash=hash_source(source, secret),
        src_port=0,
        dst_port=22,
        kind=kind,
        data=data,
    )


def parse_jsonl(lines: list[str], secret: str) -> list[EventIn]:
    events: list[EventIn] = []
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        event = cowrie_to_event(record, secret)
        if event is not None:
            events.append(event)
    return events
