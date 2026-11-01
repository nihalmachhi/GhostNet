from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_event(event: dict[str, Any]) -> bytes:
    clean = {key: value for key, value in event.items() if key not in {"hash", "prev_hash"}}
    return json.dumps(clean, sort_keys=True, separators=(",", ":"), default=str).encode()


def hash_event(event: dict[str, Any], previous_hash: str) -> str:
    digest = hashlib.sha256()
    digest.update(previous_hash.encode())
    digest.update(canonical_event(event))
    return digest.hexdigest()


def verify_chain(events: list[dict[str, Any]]) -> bool:
    previous = ""
    for event in events:
        if event.get("prev_hash", "") != previous or event.get("hash") != hash_event(
            event, previous
        ):
            return False
        previous = event["hash"]
    return True
