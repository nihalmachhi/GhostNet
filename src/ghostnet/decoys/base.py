from __future__ import annotations

import asyncio
from typing import TypeAlias

Peer: TypeAlias = tuple[str, int]
MAX_LINE = 4096


def peer_of(writer: asyncio.StreamWriter) -> Peer:
    """Return a safe peer tuple without trusting optional socket extras."""
    peer = writer.get_extra_info("peername") or ("unknown", 0)
    return str(peer[0]), int(peer[1])


async def read_line(reader: asyncio.StreamReader, timeout: float = 5.0) -> str:
    """Read one bounded line; long input is truncated instead of buffered forever."""
    raw = await asyncio.wait_for(reader.readline(), timeout)
    return raw[:MAX_LINE].decode("utf-8", "replace").strip()


async def close_writer(writer: asyncio.StreamWriter) -> None:
    writer.close()
    try:
        await writer.wait_closed()
    except (ConnectionError, OSError):
        pass
