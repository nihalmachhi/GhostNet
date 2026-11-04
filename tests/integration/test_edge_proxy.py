from __future__ import annotations

import asyncio
from functools import partial

from ghostnet.orchestrator import edge_proxy


async def _echo(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    while data := await reader.read(1024):
        writer.write(b"echo:" + data)
        await writer.drain()
    writer.close()


def test_proxy_forwards_to_upstream() -> None:
    async def run() -> None:
        upstream = await asyncio.start_server(_echo, "127.0.0.1", 0)
        upstream_port = upstream.sockets[0].getsockname()[1]
        proxy = await asyncio.start_server(
            partial(edge_proxy._proxy, target="127.0.0.1", port=upstream_port),
            "127.0.0.1",
            0,
        )
        proxy_port = proxy.sockets[0].getsockname()[1]
        reader, writer = await asyncio.open_connection("127.0.0.1", proxy_port)
        writer.write(b"hello")
        await writer.drain()
        assert await asyncio.wait_for(reader.read(64), timeout=2) == b"echo:hello"
        writer.close()
        await writer.wait_closed()
        proxy.close()
        upstream.close()
        await proxy.wait_closed()
        await upstream.wait_closed()

    asyncio.run(run())


def test_proxy_closes_when_upstream_is_unavailable() -> None:
    async def run() -> None:
        proxy = await asyncio.start_server(
            partial(edge_proxy._proxy, target="127.0.0.1", port=1),
            "127.0.0.1",
            0,
        )
        proxy_port = proxy.sockets[0].getsockname()[1]
        reader, writer = await asyncio.open_connection("127.0.0.1", proxy_port)
        assert await asyncio.wait_for(reader.read(1), timeout=5) == b""
        writer.close()
        proxy.close()
        await proxy.wait_closed()

    asyncio.run(run())
