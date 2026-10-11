from __future__ import annotations

import asyncio
import os

from ghostnet.sensors.privacy import hash_source


def emit(peer: tuple, kind: str, data: dict) -> None:
    import httpx

    source, port = str(peer[0]), int(peer[1])
    payload = {
        "decoy_id": "fake-db-01",
        "decoy_type": "fake-db",
        "session_id": f"{hash_source(source)}:{port}",
        "src_hash": hash_source(source),
        "src_port": port,
        "dst_port": 5433,
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
    emit(peer, "conn_open", {"service": "fake-db"})
    writer.write(b"GHOSTDB 0.1 ready\r\n")
    await writer.drain()
    try:
        while line := await asyncio.wait_for(reader.readline(), 5):
            command = line.decode("utf-8", "replace").strip()[:300]
            emit(peer, "command", {"command": command.split(" ", 1)[0].upper()})
            reply = (
                b"RESULT accounts=3\r\n"
                if command.upper().startswith("SELECT")
                else b"OK read-only demo\r\n"
            )
            writer.write(reply)
            await writer.drain()
    except (TimeoutError, OSError):
        pass
    finally:
        writer.close()
        await writer.wait_closed()


async def main() -> None:
    from ghostnet.sensors.panic_poller import wait_for_panic

    server = await asyncio.start_server(handle, "0.0.0.0", 5433)
    poller = asyncio.create_task(wait_for_panic())
    try:
        async with server:
            await server.serve_forever()
    finally:
        poller.cancel()


if __name__ == "__main__":
    asyncio.run(main())
