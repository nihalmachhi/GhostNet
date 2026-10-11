from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from ghostnet.api.main import Settings, create_app
from ghostnet.pipeline.sessions import build_sessions, classify_session
from ghostnet.sensors.hashchain import verify_chain
from ghostnet.sensors.privacy import credential_summary, hash_source
from ghostnet.sensors.schema import EventInput
from ghostnet.storage.db import EventStore


def event(session: str = "s1", src: str = "h:source") -> EventInput:
    return EventInput(
        decoy_id="web-admin-01",
        decoy_type="web-admin",
        session_id=session,
        src_hash=src,
        src_port=1234,
        dst_port=8081,
        kind="auth_attempt",
        data=credential_summary("analyst", "synthetic-only"),
    )


def test_hash_chain_detects_edits(tmp_path: Path) -> None:
    store = EventStore(str(tmp_path / "events.sqlite"))
    store.append(event())
    store.append(event(session="s2"))
    rows = store.events()
    assert verify_chain(rows)
    rows[0]["kind"] = "edited"
    assert not verify_chain(rows)


def test_password_raw_text_not_retained() -> None:
    result = credential_summary("demo", "super-secret-demo")
    assert "password" not in json.dumps(result).lower().replace("password_len", "").replace(
        "password_hash", ""
    )
    assert result["password_len"] == 17
    assert hash_source("127.0.0.1") == hash_source("127.0.0.1")


def test_sessions_and_rule_classification(tmp_path: Path) -> None:
    store = EventStore(str(tmp_path / "events.sqlite"))
    store.append(event())
    store.append(event())
    sessions = build_sessions(store.events())
    assert sessions[0]["n_auth"] == 2
    assert classify_session(sessions[0])[0] == "scan_discovery"


def test_api_requires_explicit_panic_confirmation(tmp_path: Path) -> None:
    client = TestClient(create_app(Settings(database=str(tmp_path / "api.sqlite"))))
    assert client.post("/panic", json={"confirmation": "no"}).status_code == 400
    assert client.post("/panic", json={"confirmation": "STOP GHOSTNET"}).json()["panic"] is True
    assert client.get("/internal/panic").json()["active"] is True


def test_adaptation_is_allowlisted_and_never_deployed(tmp_path: Path) -> None:
    client = TestClient(create_app(Settings(database=str(tmp_path / "api.sqlite"))))
    result = client.post(
        "/adapt/approve", json={"action_id": "x", "kind": "run_shell", "approve": True}
    )
    assert result.status_code == 200
    assert result.json()["approved"] is False
    assert result.json()["deployed"] is False
