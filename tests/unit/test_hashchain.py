from __future__ import annotations

from ghostnet.sensors.hashchain import chain_checkpoint, hash_event, verify_chain

KEY = "unit-test-chain-key-123456"


def _event(seq: int, prev: str, kind: str = "auth_attempt") -> dict:
    event = {
        "event_id": f"{seq:032d}",
        "seq": seq,
        "decoy_id": "web-admin-01",
        "ts": f"2026-01-01T00:00:{seq:02d}+00:00",
        "kind": kind,
        "prev_hash": prev,
    }
    event["hash"] = hash_event(event, prev, KEY)
    return event


def test_chain_verification_and_tamper_detection() -> None:
    first = _event(1, "")
    second = _event(2, first["hash"])
    assert verify_chain([first, second], KEY)
    second["kind"] = "edited"
    assert not verify_chain([first, second], KEY)


def test_sequence_gap_is_rejected() -> None:
    first = _event(1, "")
    third = _event(3, first["hash"])
    assert not verify_chain([first, third], KEY)


def test_chains_are_independent_per_decoy() -> None:
    first = _event(1, "")
    other = dict(_event(1, ""))
    other["decoy_id"] = "fake-ssh-01"
    other["hash"] = hash_event(other, "", KEY)
    assert verify_chain([first, other], KEY)


def test_checkpoint_reports_heads_and_counts() -> None:
    first = _event(1, "")
    second = _event(2, first["hash"])
    checkpoint = chain_checkpoint([first, second], KEY)
    assert checkpoint["verified"] is True
    assert checkpoint["counts"] == {"web-admin-01": 2}
    assert checkpoint["chains"]["web-admin-01"] == second["hash"]
