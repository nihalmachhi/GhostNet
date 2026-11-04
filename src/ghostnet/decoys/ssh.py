from __future__ import annotations

import asyncio
import os

from ghostnet.decoys.base import Peer, close_writer, peer_of, read_line
from ghostnet.sensors.emitter import emit_payload
from ghostnet.sensors.privacy import credential_summary

DECOY = "fake-ssh-01"
BANNER = os.getenv("GHOSTNET_SSH_BANNER", "SSH-2.0-OpenSSH_9.6")


async def _emit(peer: Peer, kind: str, data: dict[str, object]) -> None:
    await emit_payload(DECOY, "fake-ssh", peer[0], peer[1], 2222, kind, data)


async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    peer = peer_of(writer)
    await _emit(peer, "conn_open", {"service": "ssh-like"})
    try:
        writer.write(f"{BANNER}\r\nlogin: ".encode())
        await writer.drain()
        user = await read_line(reader, 5)
        writer.write(b"password: ")
        await writer.drain()
        password = await read_line(reader, 5)
        await _emit(peer, "auth_attempt", dict(credential_summary(user, password)))
        writer.write(b"Access denied\r\n")
        await writer.drain()
    except (TimeoutError, OSError, ConnectionError):
        return
    finally:
        await close_writer(writer)


async def main() -> None:
    from ghostnet.sensors.panic_poller import wait_for_panic

    server = await asyncio.start_server(handle, "0.0.0.0", 2222, limit=8192)
    poller = asyncio.create_task(wait_for_panic(DECOY))
    try:
        async with server:
            await server.serve_forever()
    finally:
        poller.cancel()


if __name__ == "__main__":
    asyncio.run(main())
