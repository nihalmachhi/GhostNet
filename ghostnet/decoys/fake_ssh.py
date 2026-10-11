from __future__ import annotations

import asyncio
import os

from ghostnet.sensors.client import credential_summary
from ghostnet.sensors.privacy import hash_source


def log_event(source: str, source_port: int, kind: str, data: dict) -> None:
    import httpx

    payload = {
        "decoy_id": "fake-ssh-01",
        "decoy_type": "fake-ssh",
        "session_id": f"{hash_source(source)}:{source_port}",
        "src_hash": hash_source(source),
        "src_port": source_port,
        "dst_port": 2222,
        "proto": "tcp",
        "kind": kind,
        "data": data,
    }
    try:
        httpx.post(
            os.getenv("GHOSTNET_API_URL", "http://127.0.0.1:8000") + "/events",
            json=payload,
            timeout=1,
        )
    except httpx.HTTPError:
        pass


async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    peer = writer.get_extra_info("peername") or ("unknown", 0)
    source, port = str(peer[0]), int(peer[1])
    log_event(source, port, "conn_open", {"service": "ssh-like"})
    try:
        writer.write(b"SSH-2.0-GhostNet-Lab\r\nlogin: ")
        await writer.drain()
        user = (
            (await asyncio.wait_for(reader.readline(), 4)).decode("utf-8", "replace").strip()[:80]
        )
        writer.write(b"password: ")
        await writer.drain()
        password = (
            (await asyncio.wait_for(reader.readline(), 4)).decode("utf-8", "replace").strip()[:256]
        )
        log_event(source, port, "auth_attempt", credential_summary(user, password))
        writer.write(b"Access denied\r\n")
        await writer.drain()
    except (TimeoutError, OSError):
        return
    finally:
        writer.close()
        await writer.wait_closed()


async def main() -> None:
    from ghostnet.sensors.panic_poller import wait_for_panic

    server = await asyncio.start_server(handle, "0.0.0.0", 2222)
    poller = asyncio.create_task(wait_for_panic())
    try:
        async with server:
            await server.serve_forever()
    finally:
        poller.cancel()


if __name__ == "__main__":
    asyncio.run(main())
