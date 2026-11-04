from __future__ import annotations

import asyncio
from typing import Any

import httpx
import pytest

from ghostnet.sensors import emitter


class _Response:
    def __init__(self, success: bool = True) -> None:
        self.is_success = success


class _FakeClient:
    def __init__(self, *, fail: bool = False, success: bool = True) -> None:
        self.fail = fail
        self.success = success
        self.calls: list[tuple[str, dict[str, Any], dict[str, str]]] = []

    async def __aenter__(self) -> _FakeClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def post(self, url: str, json: dict[str, Any], headers: dict[str, str]) -> _Response:
        self.calls.append((url, json, headers))
        if self.fail:
            raise httpx.ConnectError("synthetic failure")
        return _Response(self.success)


def _reset() -> None:
    emitter._QUEUE = asyncio.Queue(maxsize=2048)
    emitter._DROPPED = 0
    emitter._SENT = 0
    emitter._WORKER = None


@pytest.mark.parametrize("value", ["", "change-me", "local-demo-key", "replace-with-secret"])
def test_key_rejects_placeholders(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("GHOSTNET_HASH_KEY", value)
    with pytest.raises(RuntimeError):
        emitter._key("GHOSTNET_HASH_KEY")


def test_clean_data_removes_raw_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GHOSTNET_HASH_KEY", "unit-test-hash-key-value-1234")
    monkeypatch.setenv("GHOSTNET_CANARY_TOKENS", "gk_live_demo_web_4f2a")
    cleaned = emitter._clean_data(
        "token_seen",
        {"token": "gk_live_demo_web_4f2a", "path": "/token", "user": "root"},
    )
    assert "token" not in cleaned
    assert "user" not in cleaned
    assert cleaned["canary_id"]
    assert cleaned["path"] == "/token"

    credential = emitter._clean_data(
        "auth_attempt", {"user": "root", "password": "hunter2", "user_len": 4}
    )
    assert credential == {"user_len": 4}


def test_emit_payload_queues_hashed_event(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset()
    monkeypatch.setenv("GHOSTNET_HASH_KEY", "unit-test-hash-key-value-1234")
    monkeypatch.setenv("GHOSTNET_INGEST_SECRET", "unit-test-ingest-secret-value-1234")
    monkeypatch.setenv("GHOSTNET_API_URL", "http://ingest.test")
    client = _FakeClient()
    monkeypatch.setattr(emitter.httpx, "AsyncClient", lambda **_: client)

    async def run() -> None:
        await emitter.emit_payload(
            "web-admin-01", "web-admin", "192.0.2.10", 4444, 8081, "auth_attempt", {"user": "x"}
        )
        for _ in range(100):
            if emitter._QUEUE.empty() and emitter.sent_events() == 1:
                break
            await asyncio.sleep(0.01)
        assert emitter._WORKER is not None
        emitter._WORKER.cancel()

    asyncio.run(run())
    url, payload, headers = client.calls[0]
    assert url == "http://ingest.test/events"
    assert payload["src_hash"].startswith("h:")
    assert payload["data"] == {}
    assert "X-Decoy-Token" in headers
    assert emitter.sent_events() == 1
    assert emitter.dropped_events() == 0


def test_emit_payload_drops_when_queue_full(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset()
    monkeypatch.setenv("GHOSTNET_HASH_KEY", "unit-test-hash-key-value-1234")
    monkeypatch.setenv("GHOSTNET_INGEST_SECRET", "unit-test-ingest-secret-value-1234")

    async def run() -> None:
        emitter._QUEUE = asyncio.Queue(maxsize=1)
        emitter._QUEUE.put_nowait(("url", {}, {}))
        await emitter.emit_payload("web-admin-01", "web-admin", "192.0.2.10", 1, 2, "conn_open", {})
        assert emitter._WORKER is not None
        emitter._WORKER.cancel()

    asyncio.run(run())
    assert emitter.dropped_events() == 1


def test_send_loop_survives_delivery_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset()
    client = _FakeClient(fail=True)
    monkeypatch.setattr(emitter.httpx, "AsyncClient", lambda **_: client)

    async def run() -> None:
        emitter._QUEUE.put_nowait(("http://ingest.test/events", {}, {}))
        task = asyncio.create_task(emitter._send_loop())
        for _ in range(100):
            if emitter._QUEUE.empty():
                break
            await asyncio.sleep(0.01)
        task.cancel()

    asyncio.run(run())
    assert emitter.sent_events() == 0
