from __future__ import annotations

import asyncio
from functools import partial

# Only decoy ports are exposed. The admin API is never reachable from the
# deception network through this process.
ROUTES = {
    8081: ("web-admin", 8080),
    2222: ("fake-ssh", 2222),
    5433: ("fake-db", 5433),
}
_CONNECTIONS = asyncio.Semaphore(128)


async def _copy(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        while chunk := await asyncio.wait_for(reader.read(65536), timeout=90):
            writer.write(chunk)
            await writer.drain()
    except (TimeoutError, OSError, ConnectionError):
        pass
    finally:
        writer.close()


async def _proxy(
    client_reader: asyncio.StreamReader,
    client_writer: asyncio.StreamWriter,
    target: str,
    port: int,
) -> None:
    async with _CONNECTIONS:
        try:
            upstream_reader, upstream_writer = await asyncio.wait_for(
                asyncio.open_connection(target, port), timeout=3
            )
        except (OSError, TimeoutError):
            client_writer.close()
            await client_writer.wait_closed()
            return
        try:
            await asyncio.gather(
                _copy(client_reader, upstream_writer),
                _copy(upstream_reader, client_writer),
            )
        finally:
            client_writer.close()


async def main() -> None:
    servers = []
    for listen_port, (host, upstream_port) in ROUTES.items():
        handler = partial(_proxy, target=host, port=upstream_port)
        servers.append(
            await asyncio.start_server(
                handler,
                host="0.0.0.0",  # noqa: S104 - container-local listener, loopback published
                port=listen_port,
                limit=8192,
            )
        )
    async with asyncio.TaskGroup() as group:
        for server in servers:
            group.create_task(server.serve_forever())


if __name__ == "__main__":
    asyncio.run(main())
