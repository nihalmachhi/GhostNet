from __future__ import annotations

from typing import Any

from fastapi import Header, HTTPException, Request

from ghostnet.core.security import verify_admin_token
from ghostnet.pipeline.actors import link_actors
from ghostnet.pipeline.attack_map import map_behavior
from ghostnet.pipeline.sessions import build_sessions
from ghostnet.storage.db import EventStore


def require_admin(request: Request, x_admin_token: str | None = Header(default=None)) -> None:
    settings = request.app.state.settings
    if not verify_admin_token(settings.admin_token, x_admin_token):
        raise HTTPException(401, "Admin authentication required")


def store_of(request: Request) -> EventStore:
    return request.app.state.store  # type: ignore[no-any-return]


def enriched_sessions(request: Request) -> list[dict[str, Any]]:
    store = store_of(request)
    sessions = build_sessions(store.all_events())
    for session in sessions:
        session["attack"] = map_behavior(str(session["class_label"]))
    link_actors(sessions)
    for session in sessions:
        session.pop("events", None)
    return sessions
