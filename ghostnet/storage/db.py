from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from ghostnet.sensors.hashchain import hash_event
from ghostnet.sensors.schema import EventInput


class EventStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY, decoy_id TEXT NOT NULL, session_id TEXT NOT NULL,
                src_hash TEXT NOT NULL, src_port INTEGER NOT NULL, ts TEXT NOT NULL,
                kind TEXT NOT NULL, payload TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL
            )""")
            db.execute(
                "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS adaptations (action_id TEXT PRIMARY KEY, action_json TEXT NOT NULL, approved INTEGER NOT NULL, reason TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
            )
            db.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('panic','false')")

    def connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def append(self, event: EventInput) -> dict[str, Any]:
        value = event.model_dump(mode="json")
        with self.connect() as db:
            last = db.execute(
                "SELECT hash FROM events WHERE decoy_id=? ORDER BY rowid DESC LIMIT 1",
                (event.decoy_id,),
            ).fetchone()
            previous = str(last[0]) if last else ""
            value["prev_hash"] = previous
            value["hash"] = hash_event(value, previous)
            db.execute(
                "INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    event.event_id,
                    event.decoy_id,
                    event.session_id,
                    event.src_hash,
                    event.src_port,
                    event.ts.isoformat(),
                    event.kind,
                    json.dumps(value, sort_keys=True),
                    previous,
                    value["hash"],
                ),
            )
        return value

    def events(self, limit: int = 500) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT payload FROM events ORDER BY ts DESC LIMIT ?", (limit,)
            ).fetchall()
        return [json.loads(row[0]) for row in reversed(rows)]

    def set_panic(self, active: bool) -> None:
        with self.connect() as db:
            db.execute(
                "UPDATE settings SET value=? WHERE key='panic'", ("true" if active else "false",)
            )

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

    def adaptations(self) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute("SELECT * FROM adaptations ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]

    def count(self) -> int:
        with self.connect() as db:
            return int(db.execute("SELECT COUNT(*) FROM events").fetchone()[0])
