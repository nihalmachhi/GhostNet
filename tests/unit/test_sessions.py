from __future__ import annotations

from conftest import event_dict

from ghostnet.pipeline.rules_engine import classify_features, rule_set_hash
from ghostnet.pipeline.sessions import build_sessions


def _ts(second: int) -> str:
    return f"2026-01-01T00:00:{second:02d}+00:00"


def test_sessions_group_by_source_and_decoy_and_split_on_idle() -> None:
    events = [
        event_dict(_ts(0), kind="conn_open"),
        event_dict(_ts(1), kind="conn_open", src_hash="h:" + "b" * 24),
        event_dict("2026-01-01T00:16:40+00:00", kind="conn_open"),
    ]
    sessions = build_sessions(events)
    assert len(sessions) == 3
    assert all(session["decoy_id"] == "web-admin-01" for session in sessions)


def test_canary_and_credential_rules() -> None:
    canary = build_sessions([event_dict(_ts(0), kind="token_seen", data={"canary_id": "abc"})])[0]
    assert canary["class_label"] == "canary_followup"
    assert canary["rule_score"] > 0.9

    stuffing = build_sessions([event_dict(_ts(i), data={"user_hash": f"u{i}"}) for i in range(4)])[
        0
    ]
    assert stuffing["class_label"] == "credential_stuffing"
    assert stuffing["n_unique_users"] == 4


def test_exploit_scan_and_command_rules() -> None:
    exploit = build_sessions(
        [event_dict(_ts(0), kind="http_request", data={"path": "/../../etc/passwd"})]
    )[0]
    assert exploit["class_label"] == "exploit_attempt"

    scan = build_sessions([event_dict(_ts(0), kind="conn_open")])[0]
    assert scan["class_label"] == "scan_discovery"

    scripted = build_sessions(
        [event_dict(_ts(i), kind="command", data={"command": "SELECT"}) for i in range(1, 5)]
    )[0]
    assert scripted["class_label"] == "scripted_interaction"


def test_benign_fallback_and_rule_hash() -> None:
    assert classify_features({"n_events": 10, "duration_s": 1})["label"] == "benign_noise"
    assert len(rule_set_hash()) == 64
