from __future__ import annotations

import json

from ghostnet.adapters.cowrie import cowrie_to_event, parse_jsonl

SECRET = "unit-test-secret-value-1234"  # noqa: S105


def test_cowrie_login_is_minimized() -> None:
    record = {
        "eventid": "cowrie.login.failed",
        "src_ip": "192.0.2.5",
        "session": "abc",
        "username": "root",
        "password": "hunter2",
    }
    event = cowrie_to_event(record, SECRET)
    assert event is not None
    assert event.kind == "auth_attempt"
    assert "hunter2" not in json.dumps(event.model_dump())
    assert event.data["user_class"] == "admin"


def test_cowrie_command_and_unknown_event() -> None:
    command = cowrie_to_event(
        {"eventid": "cowrie.command.input", "src_ip": "192.0.2.5", "input": "ls -la"},
        SECRET,
    )
    assert command is not None and command.data["command"] == "LS"
    assert cowrie_to_event({"eventid": "other"}, SECRET) is None


def test_parse_jsonl_skips_invalid_lines() -> None:
    lines = ["not-json", json.dumps({"eventid": "cowrie.session.connect", "src_ip": "x"})]
    assert len(parse_jsonl(lines, SECRET)) == 1
