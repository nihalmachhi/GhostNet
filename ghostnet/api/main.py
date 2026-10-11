from __future__ import annotations

import asyncio
import json
import uuid
from collections import Counter
from typing import Any

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from ghostnet.adapt.bandit import EpsilonGreedyPolicy
from ghostnet.adapt.policy import Action, approve
from ghostnet.pipeline.actors import link_actors
from ghostnet.pipeline.attack_map import map_behavior
from ghostnet.pipeline.graph import behavior_graph
from ghostnet.pipeline.sessions import build_sessions, classify_session
from ghostnet.sensors.schema import EventInput
from ghostnet.storage.db import EventStore


class PanicRequest(BaseModel):
    confirmation: str


class AdaptDecision(BaseModel):
    action_id: str
    kind: str
    decoy_type: str = "web-admin"
    reason: str = "Analyst-reviewed proposal"
    parameters: dict[str, str | int] = Field(default_factory=dict)
    approve: bool = False


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GHOSTNET_", env_file=".env", extra="ignore")
    database: str = "data/ghostnet.sqlite3"
    cors_origin: str = "http://localhost:5173"


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()
    store = EventStore(config.database)
    bandit = EpsilonGreedyPolicy()
    app = FastAPI(title="GhostNet Defensive Deception Lab", version="0.1.0")
    app.state.store = store
    app.add_middleware(
        CORSMiddleware, allow_origins=[config.cors_origin], allow_methods=["*"], allow_headers=["*"]
    )

    def enriched_sessions() -> list[dict[str, Any]]:
        sessions = build_sessions(store.events())
        for session in sessions:
            label, score = classify_session(session)
            session["class_label"], session["confidence"] = label, score
            session["attack"] = map_behavior(label)
        actors, _ = link_actors(sessions)
        for session in sessions:
            session.pop("events", None)
        return sessions

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "project": "GhostNet"}

    @app.post("/events", status_code=201)
    def ingest_event(event: EventInput) -> dict[str, Any]:
        return store.append(event)

    @app.get("/internal/panic")
    def internal_panic() -> dict[str, bool]:
        return {"active": store.panic_active()}

    @app.get("/fleet")
    def fleet() -> dict[str, Any]:
        return {
            "decoys": [
                {
                    "id": "web-admin-01",
                    "type": "web-admin",
                    "interaction": "low",
                    "status": "configured",
                    "published": "127.0.0.1:8081",
                },
                {
                    "id": "fake-ssh-01",
                    "type": "ssh-like prompt",
                    "interaction": "low",
                    "status": "configured",
                    "published": "127.0.0.1:2222",
                },
                {
                    "id": "fake-db-01",
                    "type": "fake database",
                    "interaction": "low",
                    "status": "configured",
                    "published": "127.0.0.1:5433",
                },
            ],
            "event_count": store.count(),
            "panic": store.panic_active(),
            "containment": {
                "config_checked_before_start": True,
                "network": "internal",
                "host_bindings": "loopback-only",
            },
        }

    @app.get("/events")
    def events(limit: int = Query(default=100, ge=1, le=500)) -> dict[str, Any]:
        return {"events": store.events(limit)}

    @app.get("/sessions")
    def sessions(class_label: str | None = None, decoy: str | None = None) -> dict[str, Any]:
        rows = enriched_sessions()
        if class_label:
            rows = [row for row in rows if row["class_label"] == class_label]
        if decoy:
            rows = [row for row in rows if row["decoy_id"] == decoy]
        return {"sessions": rows}

    @app.get("/sessions/{session_id}")
    def session_detail(session_id: str) -> dict[str, Any]:
        for session in enriched_sessions():
            if session["id"] == session_id:
                return {
                    **session,
                    "events": [
                        event for event in store.events() if event["session_id"] == session_id
                    ],
                }
        raise HTTPException(404, "Session not found")

    @app.get("/actors")
    def actors() -> dict[str, Any]:
        rows = enriched_sessions()
        linked, edges = link_actors(rows)
        return {"actors": linked, "evidence_edges": edges}

    @app.get("/graph")
    def graph(actor: str | None = None) -> dict[str, Any]:
        rows = enriched_sessions()
        linked, edges = link_actors(rows)
        if actor:
            session_ids = next((row["session_ids"] for row in linked if row["id"] == actor), [])
            rows = [row for row in rows if row["id"] in session_ids]
            linked = [row for row in linked if row["id"] == actor]
            edges = [
                row
                for row in edges
                if row["source"] in session_ids and row["target"] in session_ids
            ]
        return behavior_graph(rows, linked, edges)

    @app.get("/attack/heatmap")
    def attack_heatmap() -> dict[str, Any]:
        counts: Counter[str] = Counter()
        for session in enriched_sessions():
            for mapping in session["attack"]:
                counts[mapping["tactic"]] += 1
        return {
            "tactics": [{"tactic": name, "count": count} for name, count in sorted(counts.items())]
        }

    @app.get("/adapt/propose")
    def adapt_propose() -> dict[str, Any]:
        rows = enriched_sessions()
        context = rows[-1]["class_label"] if rows else "quiet"
        actions = [
            Action(
                uuid.uuid4().hex,
                kind,
                "web-admin",
                f"Safe response to {context}",
                {"delay_ms": 80} if kind == "response_delay_ms" else {},
            )
            for kind in ("rotate_fake_credential", "add_lure", "change_banner", "response_delay_ms")
        ]
        selected = bandit.propose(context, actions)
        allowed, reason = approve(selected)
        return {
            "action": selected.__dict__,
            "policy_approved": allowed,
            "policy_reason": reason,
            "requires_analyst_approval": True,
        }

    @app.post("/adapt/approve")
    def adapt_approve(decision: AdaptDecision) -> dict[str, Any]:
        action = Action(
            decision.action_id,
            decision.kind,
            decision.decoy_type,
            decision.reason,
            decision.parameters,
        )
        allowed, reason = approve(action)
        accepted = decision.approve and allowed
        store.record_adaptation(
            action.action_id,
            json.dumps(action.__dict__, sort_keys=True),
            accepted,
            reason if allowed else reason,
        )
        return {
            "action_id": action.action_id,
            "approved": accepted,
            "policy_approved": allowed,
            "reason": reason,
            "deployed": False,
        }

    @app.post("/panic")
    def panic(request: PanicRequest) -> dict[str, Any]:
        if request.confirmation != "STOP GHOSTNET":
            raise HTTPException(400, "Explicit confirmation 'STOP GHOSTNET' is required")
        store.set_panic(True)
        return {
            "panic": True,
            "decoys_should_exit": True,
            "message": "Decoy agents poll the internal kill switch and exit; verify with the fleet panel.",
        }

    @app.post("/admin/panic/reset")
    def reset_panic(request: PanicRequest) -> dict[str, bool]:
        if request.confirmation != "RESET GHOSTNET":
            raise HTTPException(400, "Explicit confirmation 'RESET GHOSTNET' is required")
        store.set_panic(False)
        return {"panic": False}

    @app.websocket("/live")
    async def live(socket: WebSocket) -> None:
        await socket.accept()
        last_id = ""
        try:
            while True:
                latest = store.events(1)
                if latest and latest[-1]["event_id"] != last_id:
                    last_id = latest[-1]["event_id"]
                    await socket.send_json(latest[-1])
                await asyncio.sleep(0.5)
        except WebSocketDisconnect:
            return

    return app


app = create_app()
