from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from ghostnet.admin_api.deps import enriched_sessions, require_admin, store_of

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/sessions")
def sessions(
    request: Request, class_label: str | None = None, decoy: str | None = None
) -> dict[str, Any]:
    rows = enriched_sessions(request)
    if class_label:
        rows = [row for row in rows if row["class_label"] == class_label]
    if decoy:
        rows = [row for row in rows if row["decoy_id"] == decoy]
    return {"sessions": rows}


@router.get("/sessions/{session_id}")
def session_detail(request: Request, session_id: str) -> dict[str, Any]:
    for session in enriched_sessions(request):
        if session["id"] == session_id:
            return {
                **session,
                "events": store_of(request).events_in_window(
                    session["src_hash"],
                    session["decoy_id"],
                    session["started_at"],
                    session["ended_at"],
                ),
            }
    raise HTTPException(404, "Session not found")
