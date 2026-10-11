from __future__ import annotations

import os

import httpx
from fastapi import Request

from ghostnet.sensors.privacy import credential_summary, hash_source


async def send_event(
    request: Request,
    decoy_id: str,
    decoy_type: str,
    kind: str,
    data: dict,
    session_id: str | None = None,
) -> None:
    client = request.client
    source = client.host if client else "unknown"
    port = client.port if client else 0
    event = {
        "decoy_id": decoy_id,
        "decoy_type": decoy_type,
        "session_id": session_id or f"{hash_source(source)}:{port}",
        "src_hash": hash_source(source),
        "src_port": port,
        "dst_port": request.url.port or 0,
        "proto": "tcp",
        "kind": kind,
        "data": data,
    }
    url = os.getenv("GHOSTNET_API_URL", "http://127.0.0.1:8000") + "/events"
    async with httpx.AsyncClient(timeout=1) as client_http:
        try:
            await client_http.post(url, json=event)
        except httpx.HTTPError:
            return


__all__ = ["credential_summary", "send_event"]
