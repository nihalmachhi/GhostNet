from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ghostnet.admin_api.deps import require_admin, store_of

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/events")
def events(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    after: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    store = store_of(request)
    return {"events": store.events(limit, after), "next_after": store.latest_seq()}


@router.get("/events/{event_id}")
def event_detail(request: Request, event_id: str) -> dict[str, Any]:
    for event in store_of(request).all_events():
        if event.get("event_id") == event_id:
            return event
    raise HTTPException(404, "Event not found")
