from __future__ import annotations

import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from ghostnet.adapt.bandit import EpsilonGreedyPolicy
from ghostnet.admin_api.routers import (
    actors,
    adapt,
    attack,
    events,
    fleet,
    integrity,
    metrics,
    panic,
    sessions,
)
from ghostnet.core.logging import configure_logging
from ghostnet.core.security import verify_admin_token
from ghostnet.core.settings import Settings
from ghostnet.storage.db import EventStore


def create_admin_app(settings: Settings | None = None) -> FastAPI:
    """Build the analyst-facing app; importing this module has no side effects."""
    config = settings or Settings()
    config.require_secrets()
    configure_logging("admin-api")
    app = FastAPI(title="GhostNet Admin API", version="0.2.0")
    app.state.settings = config
    app.state.store = EventStore(config.database, config.chain_key)
    app.state.bandit = EpsilonGreedyPolicy(state_path=config.bandit_state_path)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[config.cors_origin],
        allow_methods=["GET", "POST"],
        allow_headers=["X-Admin-Token", "Content-Type"],
    )
    for router in (
        fleet.router,
        events.router,
        sessions.router,
        actors.router,
        attack.router,
        adapt.router,
        panic.router,
        integrity.router,
        metrics.router,
    ):
        app.include_router(router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "admin"}

    @app.websocket("/live")
    async def live(socket: WebSocket) -> None:
        token = socket.query_params.get("token", "")
        if not verify_admin_token(config.admin_token, token):
            await socket.close(code=4401)
            return
        await socket.accept()
        last = int(socket.query_params.get("after", "0") or 0)
        try:
            while True:
                if app.state.store.panic_active():
                    await socket.send_json({"type": "panic", "message": "panic switch active"})
                    await socket.close(code=1001)
                    return
                batch = app.state.store.events(limit=1000, after=last)
                for event in batch:
                    await socket.send_json(event)
                if batch:
                    last = app.state.store.latest_seq()
                else:
                    await socket.send_json({"type": "heartbeat"})
                await asyncio.sleep(0.5)
        except WebSocketDisconnect:
            return

    return app


# Compatibility alias for callers that imported the old single-app factory.
create_app = create_admin_app
