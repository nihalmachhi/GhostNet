from __future__ import annotations

import json
import os
import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from ghostnet.sensors.hashchain import chain_checkpoint, hash_event, verify_chain
from ghostnet.sensors.schema import EventIn, EventStored
from ghostnet.storage.migrations import migrate


class EventStore:
    """SQLite event store with a per-decoy HMAC hash chain.

    A database writer can still rewrite the whole chain. The HMAC key and
    exported checkpoints make casual edits detectable, not impossible.
    """

    def __init__(self, path: str, chain_key: str | None = None) -> None:
        self.path = Path(path)
        self.chain_key = chain_key or os.getenv("GHOSTNET_CHAIN_KEY")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            migrate(db)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """Open a connection that is always closed, even after an exception."""
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA busy_timeout=15000")
            db.execute("PRAGMA foreign_keys=ON")
            yield db
        finally:
            db.close()

    def append(self, event: EventIn) -> dict[str, Any]:
        """Append one server-owned event under ``BEGIN IMMEDIATE``."""
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            last = db.execute(
                "SELECT seq, hash FROM events WHERE decoy_id=? ORDER BY seq DESC LIMIT 1",
                (event.decoy_id,),
            ).fetchone()
            previous = str(last["hash"]) if last else ""
            seq = int(last["seq"]) + 1 if last else 1
            value = event.model_dump(mode="json")
            value.update(
                {
                    "event_id": uuid4().hex,
                    "ts": datetime.now(UTC).isoformat(),
                    "seq": seq,
                    "prev_hash": previous,
                }
            )
            value["hash"] = hash_event(value, previous, self.chain_key)
            stored = EventStored(**value).model_dump(mode="json")
            db.execute(
                """INSERT INTO events(
                    event_id,seq,decoy_id,session_id,src_hash,src_port,dst_port,proto,ts,kind,
                    payload,prev_hash,hash
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    stored["event_id"],
                    stored["seq"],
                    stored["decoy_id"],
                    stored["session_id"],
                    stored["src_hash"],
                    stored["src_port"],
                    stored["dst_port"],
                    stored["proto"],
                    stored["ts"],
                    stored["kind"],
                    json.dumps(stored, sort_keys=True),
                    stored["prev_hash"],
                    stored["hash"],
                ),
            )
            db.commit()
        return stored

    def events(self, limit: int = 500, after: int = 0) -> list[dict[str, Any]]:
        """Return events in insertion order using a rowid cursor."""
        with self.connect() as db:
            rows = db.execute(
                "SELECT payload FROM events WHERE rowid>? ORDER BY rowid ASC LIMIT ?",
                (max(0, after), max(1, min(limit, 1000))),
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def all_events(self) -> list[dict[str, Any]]:
        """Return the full retained event table for session and actor analysis."""
        with self.connect() as db:
            rows = db.execute("SELECT payload FROM events ORDER BY rowid ASC").fetchall()
        return [json.loads(row[0]) for row in rows]

    def events_in_window(
        self, src_hash: str, decoy_id: str, started_at: str, ended_at: str
    ) -> list[dict[str, Any]]:
        """Return events for a generated session, not a truncated global window."""
        with self.connect() as db:
            rows = db.execute(
                """SELECT payload FROM events
                   WHERE src_hash=? AND decoy_id=? AND ts>=? AND ts<=?
                   ORDER BY rowid ASC""",
                (src_hash, decoy_id, started_at, ended_at),
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def latest_seq(self) -> int:
        with self.connect() as db:
            row = db.execute("SELECT COALESCE(MAX(rowid),0) FROM events").fetchone()
        return int(row[0])

    def count(self) -> int:
        with self.connect() as db:
            return int(db.execute("SELECT COUNT(*) FROM events").fetchone()[0])

    def verify_integrity(self) -> dict[str, Any]:
        """Verify every retained chain and return a signed head checkpoint."""
        rows = self.all_events()
        ok = verify_chain(rows, self.chain_key)
        return {"ok": ok, "count": len(rows), "checkpoint": chain_checkpoint(rows)}

    def set_panic(self, active: bool) -> None:
        with self.connect() as db:
            db.execute(
                "UPDATE settings SET value=? WHERE key='panic'", ("true" if active else "false",)
            )
            db.commit()

    def panic_active(self) -> bool:
        with self.connect() as db:
            row = db.execute("SELECT value FROM settings WHERE key='panic'").fetchone()
        return bool(row and row[0] == "true")

    def record_adaptation(
        self, action_id: str, action_json: str, approved: bool, reason: str
    ) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT INTO adaptations(action_id,action_json,approved,reason) VALUES(?,?,?,?)",
                (action_id, action_json, int(approved), reason),
            )
            db.commit()

    def adaptations(self) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute("SELECT * FROM adaptations ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]

    def save_proposal(
        self,
        action_id: str,
        kind: str,
        decoy_type: str,
        reason: str,
        parameters: dict[str, str | int],
        ttl_seconds: int,
    ) -> None:
        now = time.time()
        with self.connect() as db:
            db.execute(
                """INSERT OR REPLACE INTO proposals(
                    action_id,kind,decoy_type,reason,parameters_json,created_at,expires_at,status
                ) VALUES(?,?,?,?,?,?,?,'pending')""",
                (
                    action_id,
                    kind,
                    decoy_type,
                    reason,
                    json.dumps(parameters),
                    now,
                    now + ttl_seconds,
                ),
            )
            db.commit()

    def get_proposal(self, action_id: str) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM proposals WHERE action_id=?", (action_id,)).fetchone()
        return dict(row) if row else None

    def decide_proposal(self, action_id: str, status: str) -> None:
        with self.connect() as db:
            db.execute("UPDATE proposals SET status=? WHERE action_id=?", (status, action_id))
            db.commit()

    def purge_old(self, retention_days: int) -> int:
        """Delete events older than the retention window.

        Purging truncates history; old checkpoints no longer describe the
        retained chain. The caller should export a new checkpoint afterwards.
        """
        cutoff = (datetime.now(UTC) - timedelta(days=max(1, retention_days))).isoformat()
        with self.connect() as db:
            cursor = db.execute("DELETE FROM events WHERE ts < ?", (cutoff,))
            db.commit()
            return int(cursor.rowcount)
