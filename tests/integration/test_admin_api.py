from __future__ import annotations

from conftest import make_event
from fastapi.testclient import TestClient


def test_admin_requires_a_token(admin_client: TestClient) -> None:
    assert admin_client.get("/health").status_code == 200
    assert admin_client.get("/fleet").status_code == 401
    assert admin_client.get("/fleet", headers={"X-Admin-Token": "wrong"}).status_code == 401


def test_ingest_and_admin_read_paths(
    ingest_client: TestClient,
    admin_client: TestClient,
    decoy_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    event = make_event()
    response = ingest_client.post("/events", json=event.model_dump(), headers=decoy_headers)
    assert response.status_code == 201
    stored = response.json()
    assert stored["seq"] == 1

    fleet = admin_client.get("/fleet", headers=admin_headers)
    assert fleet.status_code == 200 and fleet.json()["event_count"] == 1
    events = admin_client.get("/events", headers=admin_headers).json()["events"]
    assert events[0]["event_id"] == stored["event_id"]
    assert (
        admin_client.get(f"/events/{stored['event_id']}", headers=admin_headers).status_code == 200
    )
    assert admin_client.get("/events/unknown", headers=admin_headers).status_code == 404

    sessions = admin_client.get("/sessions", headers=admin_headers).json()["sessions"]
    assert sessions and sessions[0]["class_label"] == "scan_discovery"
    session_id = sessions[0]["id"]
    detail = admin_client.get(f"/sessions/{session_id}", headers=admin_headers)
    assert detail.status_code == 200 and len(detail.json()["events"]) == 1
    assert admin_client.get("/sessions/missing", headers=admin_headers).status_code == 404

    assert admin_client.get("/actors", headers=admin_headers).status_code == 200
    assert admin_client.get("/graph", headers=admin_headers).status_code == 200
    assert admin_client.get("/attack/heatmap", headers=admin_headers).status_code == 200
    integrity = admin_client.get("/integrity", headers=admin_headers).json()
    assert integrity["ok"] is True and integrity["count"] == 1
    assert admin_client.get("/checkpoint", headers=admin_headers).status_code == 200


def test_panic_and_live_websocket(admin_client: TestClient, admin_headers: dict[str, str]) -> None:
    assert (
        admin_client.post("/panic", json={"confirmation": "no"}, headers=admin_headers).status_code
        == 400
    )
    with admin_client.websocket_connect(f"/live?token={admin_headers['X-Admin-Token']}") as socket:
        assert socket.receive_json()["type"] == "heartbeat"
        admin_client.post("/panic", json={"confirmation": "STOP GHOSTNET"}, headers=admin_headers)
        assert socket.receive_json()["type"] == "panic"
    assert admin_client.post(
        "/admin/panic/reset", json={"confirmation": "RESET GHOSTNET"}, headers=admin_headers
    ).json() == {"panic": False}


def test_adaptation_requires_a_known_proposal(
    admin_client: TestClient, admin_headers: dict[str, str]
) -> None:
    assert (
        admin_client.post(
            "/adapt/approve", json={"action_id": "unknown", "approve": True}, headers=admin_headers
        ).status_code
        == 404
    )
    proposal = admin_client.get("/adapt/propose", headers=admin_headers).json()
    action_id = proposal["action"]["action_id"]
    assert proposal["requires_analyst_approval"] is True
    approved = admin_client.post(
        "/adapt/approve", json={"action_id": action_id, "approve": True}, headers=admin_headers
    )
    assert approved.status_code == 200 and approved.json()["deployed"] is False
    assert (
        admin_client.post(
            "/adapt/approve", json={"action_id": action_id, "approve": True}, headers=admin_headers
        ).status_code
        == 409
    )


def test_metrics_are_prometheus_text(
    admin_client: TestClient, admin_headers: dict[str, str]
) -> None:
    response = admin_client.get("/metrics", headers=admin_headers)
    assert response.status_code == 200
    assert "ghostnet_events_total" in response.text
