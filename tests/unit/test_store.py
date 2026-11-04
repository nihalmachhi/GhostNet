from __future__ import annotations

import threading
from pathlib import Path

from conftest import make_event

from ghostnet.sensors.hashchain import verify_chain
from ghostnet.storage.db import EventStore

KEY = "unit-test-chain-key-123456"


def test_append_assigns_server_fields_and_chain(store: EventStore) -> None:
    first = store.append(make_event())
    second = store.append(make_event())
    assert first["seq"] == 1 and second["seq"] == 2
    assert second["prev_hash"] == first["hash"]
    assert len(first["event_id"]) == 32
    assert store.count() == 2
    assert verify_chain(store.all_events(), store.chain_key)


def test_pagination_and_session_queries(store: EventStore) -> None:
    store.append(make_event(session_id="one"))
    store.append(make_event(session_id="two"))
    store.append(make_event(session_id="one"))
    assert len(store.events(limit=1)) == 1
    assert len(store.events(limit=10, after=1)) == 2
    assert (
        len(store.events_in_window("h:" + "a" * 24, "web-admin-01", "2026-01-01", "2026-12-31"))
        == 3
    )
    assert store.latest_seq() == 3


def test_integrity_detects_database_tampering(store: EventStore) -> None:
    store.append(make_event())
    assert store.verify_integrity()["ok"] is True
    with store.connect() as db:
        db.execute("UPDATE events SET payload=replace(payload,'auth_attempt','edited')")
        db.commit()
    assert store.verify_integrity()["ok"] is False


def test_panic_and_adaptation_records(store: EventStore) -> None:
    assert store.panic_active() is False
    store.set_panic(True)
    assert store.panic_active() is True
    store.record_adaptation("a1", "{}", True, "ok")
    assert store.adaptations()[0]["approved"] == 1


def test_proposals_are_created_and_decided(store: EventStore) -> None:
    store.save_proposal("a1", "add_lure", "web-admin", "test", {"text": "x"}, 60)
    proposal = store.get_proposal("a1")
    assert proposal is not None and proposal["status"] == "pending"
    store.decide_proposal("a1", "approved")
    assert store.get_proposal("a1")["status"] == "approved"


def test_purge_old_events(store: EventStore) -> None:
    store.append(make_event())
    assert store.purge_old(1) == 0
    assert store.count() == 1


def test_concurrent_appends_keep_one_valid_chain(tmp_path: Path) -> None:
    store = EventStore(str(tmp_path / "concurrent.sqlite"), KEY)

    def worker() -> None:
        for _ in range(25):
            store.append(make_event())

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    events = store.all_events()
    assert len(events) == 200
    assert verify_chain(events, KEY)
