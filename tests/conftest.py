from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

SECRETS = {
    "GHOSTNET_HASH_KEY": "test-only-hash-key-never-use-in-production",
    "GHOSTNET_CHAIN_KEY": "test-only-chain-key-never-use-in-production",
    "GHOSTNET_INGEST_SECRET": "test-only-ingest-secret-never-use-in-production",
    "GHOSTNET_ADMIN_TOKEN": "test-only-admin-token-never-use-in-production",
}

for key, value in SECRETS.items():
    os.environ.setdefault(key, value)

from ghostnet.admin_api.main import create_admin_app  # noqa: E402
from ghostnet.core.security import decoy_token  # noqa: E402
from ghostnet.core.settings import Settings  # noqa: E402
from ghostnet.ingest_api.main import create_ingest_app  # noqa: E402
from ghostnet.sensors.privacy import credential_summary  # noqa: E402
from ghostnet.sensors.schema import EventIn  # noqa: E402
from ghostnet.storage.db import EventStore  # noqa: E402


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        database=str(tmp_path / "ghostnet.sqlite3"),
        hash_key=SECRETS["GHOSTNET_HASH_KEY"],
        chain_key=SECRETS["GHOSTNET_CHAIN_KEY"],
        ingest_secret=SECRETS["GHOSTNET_INGEST_SECRET"],
        admin_token=SECRETS["GHOSTNET_ADMIN_TOKEN"],
        bandit_state_path=str(tmp_path / "bandit.json"),
    )


@pytest.fixture
def store(settings: Settings) -> EventStore:
    return EventStore(settings.database, settings.chain_key)


@pytest.fixture
def admin_client(settings: Settings) -> TestClient:
    return TestClient(create_admin_app(settings))


@pytest.fixture
def ingest_client(settings: Settings) -> TestClient:
    return TestClient(create_ingest_app(settings))


@pytest.fixture
def admin_headers(settings: Settings) -> dict[str, str]:
    return {"X-Admin-Token": settings.admin_token}


@pytest.fixture
def decoy_headers(settings: Settings) -> dict[str, str]:
    return {"X-Decoy-Token": decoy_token(settings.ingest_secret, "web-admin-01")}


def make_event(
    *,
    session_id: str = "session-1",
    src_hash: str = "h:" + "a" * 24,
    decoy_id: str = "web-admin-01",
    kind: str = "auth_attempt",
    data: dict[str, Any] | None = None,
    src_port: int = 44444,
    dst_port: int = 8081,
) -> EventIn:
    return EventIn(
        decoy_id=decoy_id,
        decoy_type="web-admin",
        session_id=session_id,
        src_hash=src_hash,
        src_port=src_port,
        dst_port=dst_port,
        kind=kind,
        data=data if data is not None else dict(credential_summary("analyst", "synthetic-only")),
    )


def event_dict(
    ts: str,
    *,
    kind: str = "auth_attempt",
    data: dict[str, Any] | None = None,
    src_hash: str = "h:" + "a" * 24,
    decoy_id: str = "web-admin-01",
    session_id: str = "session-1",
) -> dict[str, Any]:
    return {
        "event_id": "0" * 32,
        "seq": 1,
        "decoy_id": decoy_id,
        "decoy_type": "web-admin",
        "session_id": session_id,
        "src_hash": src_hash,
        "src_port": 44444,
        "dst_port": 8081,
        "proto": "tcp",
        "ts": ts,
        "kind": kind,
        "data": data or {},
        "prev_hash": "",
        "hash": "",
    }
