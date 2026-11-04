from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import os
from collections.abc import Mapping
from typing import Any

import httpx

from ghostnet.core.security import decoy_token
from ghostnet.sensors.privacy import summarize_token

LOGGER = logging.getLogger("ghostnet.sensors.emitter")
_QUEUE: asyncio.Queue[tuple[str, dict[str, Any], dict[str, str]]] = asyncio.Queue(maxsize=2048)
_DROPPED = 0
_SENT = 0
_WORKER: asyncio.Task[None] | None = None


def _key(name: str) -> str:
    value = os.getenv(name, "")
    if not value or value.lower().startswith(("change-me", "local-demo", "replace-with")):
        raise RuntimeError(f"{name} is required; event emission is disabled")
    return value


def dropped_events() -> int:
    return _DROPPED


def sent_events() -> int:
    return _SENT


def queue_depth() -> int:
    return _QUEUE.qsize()


def _canaries() -> set[str]:
    return {
        item.strip() for item in os.getenv("GHOSTNET_CANARY_TOKENS", "").split(",") if item.strip()
    }


def _clean_data(kind: str, data: Mapping[str, object]) -> dict[str, object]:
    clean = {key: value for key, value in data.items() if key not in {"user", "password", "token"}}
    if kind == "token_seen" and "token" in data:
        clean.update(summarize_token(str(data["token"]), _canaries(), _key("GHOSTNET_HASH_KEY")))
    return clean


async def _send_loop() -> None:
    global _SENT
    async with httpx.AsyncClient(timeout=httpx.Timeout(1.0, connect=1.0)) as client:
        while True:
            url, payload, headers = await _QUEUE.get()
            try:
                response = await client.post(url, json=payload, headers=headers)
                if response.is_success:
                    _SENT += 1
            except httpx.HTTPError:
                LOGGER.debug("event delivery failed", exc_info=True)
            finally:
                _QUEUE.task_done()


async def emit_payload(
    decoy_id: str,
    decoy_type: str,
    source: str,
    source_port: int,
    destination_port: int,
    kind: str,
    data: Mapping[str, object],
    session_id: str | None = None,
) -> None:
    """Queue a privacy-minimized event without blocking the decoy handler."""
    global _WORKER, _DROPPED
    ingest_secret = _key("GHOSTNET_INGEST_SECRET")
    hash_key = _key("GHOSTNET_HASH_KEY")
    source_hash = (
        "h:" + hmac.new(hash_key.encode(), source.encode(), hashlib.sha256).hexdigest()[:24]
    )
    payload = {
        "decoy_id": decoy_id,
        "decoy_type": decoy_type,
        "session_id": session_id or f"{source_hash}:{decoy_id}",
        "src_hash": source_hash,
        "src_port": max(0, min(source_port, 65535)),
        "dst_port": max(0, min(destination_port, 65535)),
        "proto": "tcp",
        "kind": kind,
        "data": _clean_data(kind, data),
    }
    token = decoy_token(ingest_secret, decoy_id)
    url = os.getenv("GHOSTNET_API_URL", "http://127.0.0.1:8002") + "/events"
    if _WORKER is None or _WORKER.done():
        _WORKER = asyncio.create_task(_send_loop())
    if _QUEUE.full():
        try:
            _QUEUE.get_nowait()
            _QUEUE.task_done()
            _DROPPED += 1
        except asyncio.QueueEmpty:
            pass
    _QUEUE.put_nowait((url, payload, {"X-Decoy-Token": token}))
