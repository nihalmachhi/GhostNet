from __future__ import annotations

import asyncio
import os

from ghostnet.decoys.base import Peer, close_writer, peer_of, read_line
from ghostnet.sensors.emitter import emit_payload

DECOY = "fake-db-01"
BANNER = os.getenv("GHOSTNET_DB_BANNER", "GHOSTDB 0.1 ready")


async def _emit(peer: Peer, kind: str, data: dict[str, object]) -> None:
    await emit_payload(DECOY, "fake-db", peer[0], peer[1], 5433, kind, data)


async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    peer = peer_of(writer)
    await _emit(peer, "conn_open", {"service": "fake-db"})
    writer.write(f"{BANNER}\r\n".encode())
    await writer.drain()
    try:
        while True:
            line = await read_line(reader, 5)
            if not line:
                break
            command = line[:300]
            await _emit(peer, "command", {"command": command.split(" ", 1)[0].upper()})
            reply = (
                b"RESULT accounts=3\r\n"
                if command.upper().startswith("SELECT")
                else b"OK read-only demo\r\n"
            )
            writer.write(reply)
            await writer.drain()
    except (TimeoutError, OSError, ConnectionError):
        pass
    finally:
        await close_writer(writer)


async def main() -> None:
    from ghostnet.sensors.panic_poller import wait_for_panic

    server = await asyncio.start_server(handle, "0.0.0.0", 5433, limit=8192)
    poller = asyncio.create_task(wait_for_panic(DECOY))
    try:
        async with server:
            await server.serve_forever()
    finally:
        poller.cancel()


if __name__ == "__main__":
    asyncio.run(main())
