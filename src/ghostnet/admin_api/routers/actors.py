from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from ghostnet.admin_api.deps import enriched_sessions, require_admin
from ghostnet.pipeline.actors import link_actors
from ghostnet.pipeline.graph import behavior_graph

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/actors")
def actors(request: Request) -> dict[str, Any]:
    rows = enriched_sessions(request)
    linked, edges = link_actors(rows)
    return {"actors": linked, "evidence_edges": edges}


@router.get("/graph")
def graph(request: Request, actor: str | None = None) -> dict[str, Any]:
    rows = enriched_sessions(request)
    linked, edges = link_actors(rows)
    if actor:
        ids: list[str] = next((row["session_ids"] for row in linked if row["id"] == actor), [])
        rows = [row for row in rows if row["id"] in ids]
        linked = [row for row in linked if row["id"] == actor]
        edges = [row for row in edges if row["source"] in ids and row["target"] in ids]
    return behavior_graph(rows, linked, edges)
