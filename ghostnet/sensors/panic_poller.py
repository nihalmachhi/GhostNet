from __future__ import annotations

import asyncio
import os

import httpx


async def wait_for_panic() -> None:
    """Stop a decoy process when the internal control API raises the kill switch."""
    url = os.getenv("GHOSTNET_API_URL", "http://127.0.0.1:8000") + "/internal/panic"
    async with httpx.AsyncClient(timeout=1) as client:
        while True:
            try:
                response = await client.get(url)
                if response.is_success and response.json().get("active"):
                    os._exit(0)
            except httpx.HTTPError:
                pass
            await asyncio.sleep(0.5)


def start_poller() -> asyncio.Task[None]:
    return asyncio.create_task(wait_for_panic())


if __name__ == "__main__":
    asyncio.run(wait_for_panic())
