from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from ghostnet.core.logging import configure_logging
from ghostnet.core.security import verify_decoy_token
from ghostnet.core.settings import Settings
from ghostnet.sensors.schema import EventIn
from ghostnet.storage.db import EventStore

LOGGER = logging.getLogger("ghostnet.ingest")
ALLOWED_DECOYS = {"web-admin-01", "fake-ssh-01", "fake-db-01"}
MAX_BODY = 8192
RATE_LIMIT = 600


def create_ingest_app(settings: Settings | None = None) -> FastAPI:
    """Build the decoy-facing app with per-decoy auth and a small attack surface."""
    config = settings or Settings()
    config.require_secrets()
    configure_logging("ingest-api")
    store = EventStore(config.database, config.chain_key)
    app = FastAPI(title="GhostNet Ingest API", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings = config
    app.state.store = store
    requests: dict[str, deque[float]] = defaultdict(deque)

    @app.middleware("http")
    async def limit_body(request: Request, call_next: Any) -> Any:
        declared = request.headers.get("content-length")
        if declared and (not declared.isdigit() or int(declared) > MAX_BODY):
            return JSONResponse({"detail": "Request body exceeds 8 KiB"}, status_code=413)
        return await call_next(request)

    def authenticate(decoy_id: str, supplied: str | None) -> None:
        if decoy_id not in ALLOWED_DECOYS or not verify_decoy_token(
            config.ingest_secret, decoy_id, supplied
        ):
            raise HTTPException(401, "Decoy authentication required")
        now = time.monotonic()
        queue = requests[decoy_id]
        while queue and now - queue[0] > 60:
            queue.popleft()
        if len(queue) >= RATE_LIMIT:
            raise HTTPException(429, "Ingest rate limit exceeded")
        queue.append(now)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "ingest"}

    @app.get("/panic/{decoy_id}")
    def panic(decoy_id: str, x_decoy_token: str | None = Header(default=None)) -> dict[str, bool]:
        authenticate(decoy_id, x_decoy_token)
        return {"active": store.panic_active()}

    @app.post("/events", status_code=201)
    def ingest_event(
        event: EventIn, x_decoy_token: str | None = Header(default=None)
    ) -> dict[str, Any]:
        authenticate(event.decoy_id, x_decoy_token)
        stored = store.append(event)
        LOGGER.info(
            "event stored",
            extra={"decoy_id": event.decoy_id, "event_id": stored["event_id"]},
        )
        return stored

    return app
