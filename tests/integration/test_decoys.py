from __future__ import annotations

import asyncio
from typing import Any

import pytest
from fastapi.testclient import TestClient

from ghostnet.decoys import fake_db, ssh, web_admin
from ghostnet.sensors.emitter import _clean_data


def test_web_admin_records_minimized_events(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, Any]] = []

    async def fake_emit(request: Any, kind: str, data: Any) -> None:
        calls.append((kind, data))

    monkeypatch.setattr(web_admin, "_emit", fake_emit)
    client = TestClient(web_admin.app)
    assert client.get("/").status_code == 200
    assert client.get("/recover").status_code == 200
    assert client.get("/token/abc").status_code == 200
    login = client.post("/login", json={"user": "root", "password": "hunter2"})
    assert login.status_code == 401
    assert (
        client.post(
            "/login", content=b"not-json", headers={"content-type": "application/json"}
        ).status_code
        == 400
    )
    assert (
        client.post("/login", content=b"{}", headers={"content-length": "9000"}).status_code == 400
    )
    assert client.get("/health").json()["decoy"] == "web-admin-01"
    assert {kind for kind, _ in calls} >= {"http_request", "token_seen", "auth_attempt"}


def test_ssh_decoy_emits_auth_attempt(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[tuple[str, dict[str, Any]]] = []

    async def fake_emit(*args: Any, **kwargs: Any) -> None:
        events.append((args[5], args[6]))

    monkeypatch.setattr(ssh, "emit_payload", fake_emit)

    async def run() -> None:
        server = await asyncio.start_server(ssh.handle, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        await reader.readuntil(b"login: ")
        writer.write(b"root\n")
        await writer.drain()
        await reader.readuntil(b"password: ")
        writer.write(b"hunter2\n")
        await writer.drain()
        await reader.read(100)
        writer.close()
        await writer.wait_closed()
        server.close()
        await server.wait_closed()

    asyncio.run(run())
    assert [kind for kind, _ in events] == ["conn_open", "auth_attempt"]
    assert "hunter2" not in str(events)


def test_fake_db_decoy_emits_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    async def fake_emit(*args: Any, **kwargs: Any) -> None:
        events.append(str(args[5]))

    monkeypatch.setattr(fake_db, "emit_payload", fake_emit)

    async def run() -> None:
        server = await asyncio.start_server(fake_db.handle, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        await reader.readuntil(b"\r\n")
        writer.write(b"SELECT demo\n")
        await writer.drain()
        await reader.readuntil(b"\r\n")
        writer.close()
        await writer.wait_closed()
        server.close()
        await server.wait_closed()

    asyncio.run(run())
    assert events == ["conn_open", "command"]


def test_emitter_token_cleaning() -> None:
    cleaned = _clean_data("token_seen", {"token": "unknown-token", "path": "/token"})
    assert "token" not in cleaned
    assert "token_hash" in cleaned
    assert cleaned["path"] == "/token"


def test_panic_poller_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    from ghostnet.sensors import panic_poller

    monkeypatch.delenv("GHOSTNET_INGEST_SECRET", raising=False)
    monkeypatch.delenv("GHOSTNET_DECOY_ID", raising=False)
    with pytest.raises(RuntimeError):
        asyncio.run(panic_poller.wait_for_panic())
