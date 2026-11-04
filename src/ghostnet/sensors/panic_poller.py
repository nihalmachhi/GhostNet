from __future__ import annotations

import asyncio
import os

import httpx

from ghostnet.core.security import decoy_token


async def wait_for_panic(decoy_id: str | None = None) -> None:
    """Stop a decoy when the authenticated internal kill switch is activated."""
    decoy = decoy_id or os.getenv("GHOSTNET_DECOY_ID", "")
    secret = os.getenv("GHOSTNET_INGEST_SECRET", "")
    if not decoy or not secret or secret.lower().startswith(("change-me", "replace-with")):
        raise RuntimeError("GHOSTNET_DECOY_ID and GHOSTNET_INGEST_SECRET are required")
    token = decoy_token(secret, decoy)
    url = os.getenv("GHOSTNET_API_URL", "http://127.0.0.1:8002") + f"/panic/{decoy}"
    async with httpx.AsyncClient(timeout=1) as client:
        while True:
            try:
                response = await client.get(url, headers={"X-Decoy-Token": token})
                if response.is_success and response.json().get("active"):
                    os._exit(0)
            except (httpx.HTTPError, ValueError):
                pass
            await asyncio.sleep(0.5)


def start_poller() -> asyncio.Task[None]:
    return asyncio.create_task(wait_for_panic())


if __name__ == "__main__":
    asyncio.run(wait_for_panic())
