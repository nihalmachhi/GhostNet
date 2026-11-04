from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any

PLACEHOLDER_KEYS = {
    "",
    "change-me",
    "local-demo-key-change-me",
    "replace-with-a-different-random-secret",
}


def _chain_key(key: str | None = None) -> bytes:
    value = key or os.getenv("GHOSTNET_CHAIN_KEY")
    if not value or value.strip().lower() in PLACEHOLDER_KEYS or len(value) < 16:
        raise RuntimeError("GHOSTNET_CHAIN_KEY is required; refusing unsigned event storage")
    return value.encode()


def canonical_event(event: dict[str, Any]) -> bytes:
    """Serialize the event without its integrity fields for HMAC verification."""
    clean = {key: value for key, value in event.items() if key not in {"hash", "prev_hash"}}
    return json.dumps(clean, sort_keys=True, separators=(",", ":"), default=str).encode()


def hash_event(event: dict[str, Any], previous_hash: str, key: str | None = None) -> str:
    """HMAC the previous head and canonical event under the chain key."""
    message = previous_hash.encode() + canonical_event(event)
    return hmac.new(_chain_key(key), message, hashlib.sha256).hexdigest()


def verify_chain(events: list[dict[str, Any]], key: str | None = None) -> bool:
    """Verify every per-decoy chain, including contiguous sequence numbers."""
    previous: dict[str, str] = {}
    expected_seq: dict[str, int] = {}
    for event in events:
        decoy = str(event.get("decoy_id", ""))
        expected_previous = previous.get(decoy, "")
        expected_number = expected_seq.get(decoy, 1)
        if (
            event.get("prev_hash", "") != expected_previous
            or event.get("seq") != expected_number
            or event.get("hash") != hash_event(event, expected_previous, key)
        ):
            return False
        previous[decoy] = str(event["hash"])
        expected_seq[decoy] = expected_number + 1
    return True


def chain_checkpoint(events: list[dict[str, Any]], key: str | None = None) -> dict[str, Any]:
    """Return the signed head hash for each decoy chain.

    A checkpoint only proves the state at export time; it does not make a
    database writer unable to rewrite the whole chain.
    """
    heads: dict[str, str] = {}
    counts: dict[str, int] = {}
    for event in events:
        decoy = str(event["decoy_id"])
        heads[decoy] = str(event["hash"])
        counts[decoy] = counts.get(decoy, 0) + 1
    return {"chains": heads, "counts": counts, "verified": verify_chain(events, key)}
