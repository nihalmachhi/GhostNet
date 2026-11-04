from __future__ import annotations

import pytest
from conftest import make_event
from fastapi.testclient import TestClient

from ghostnet.ingest_api import main as ingest_main


def test_ingest_rejects_bad_tokens_and_unknown_decoys(
    ingest_client: TestClient,
) -> None:
    event = make_event().model_dump()
    assert ingest_client.post("/events", json=event).status_code == 401
    assert (
        ingest_client.post("/events", json=event, headers={"X-Decoy-Token": "wrong"}).status_code
        == 401
    )
    unknown = {**event, "decoy_id": "not-a-decoy"}
    assert (
        ingest_client.post("/events", json=unknown, headers={"X-Decoy-Token": "x"}).status_code
        == 401
    )


def test_ingest_rejects_oversized_body(
    ingest_client: TestClient, decoy_headers: dict[str, str]
) -> None:
    response = ingest_client.post(
        "/events",
        content=b"{}",
        headers={**decoy_headers, "content-length": "9000"},
    )
    assert response.status_code == 413


def test_ingest_rejects_client_integrity_fields(
    ingest_client: TestClient, decoy_headers: dict[str, str]
) -> None:
    event = make_event().model_dump()
    event["event_id"] = "0" * 32
    assert ingest_client.post("/events", json=event, headers=decoy_headers).status_code == 422


def test_ingest_rate_limit(
    ingest_client: TestClient, decoy_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ingest_main, "RATE_LIMIT", 1)
    event = make_event().model_dump()
    assert ingest_client.post("/events", json=event, headers=decoy_headers).status_code == 201
    assert ingest_client.post("/events", json=event, headers=decoy_headers).status_code == 429


def test_panic_endpoint_uses_decoy_auth(
    ingest_client: TestClient, decoy_headers: dict[str, str]
) -> None:
    assert ingest_client.get("/panic/web-admin-01").status_code == 401
    response = ingest_client.get("/panic/web-admin-01", headers=decoy_headers)
    assert response.status_code == 200 and response.json() == {"active": False}
