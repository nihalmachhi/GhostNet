from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 3


def migrate(db: sqlite3.Connection) -> None:
    """Create or upgrade the local schema in place.

    The store is deliberately small; migrations stay explicit so an operator can
    inspect every change before running an older database.
    """
    db.execute("CREATE TABLE IF NOT EXISTS schema_version(version INTEGER NOT NULL)")
    row = db.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
    if row is None:
        db.execute("INSERT INTO schema_version(version) VALUES(?)", (SCHEMA_VERSION,))
    elif int(row[0]) < SCHEMA_VERSION:
        db.execute("UPDATE schema_version SET version=?", (SCHEMA_VERSION,))

    db.execute(
        """CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY NOT NULL,
            seq INTEGER NOT NULL DEFAULT 1,
            decoy_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            src_hash TEXT NOT NULL,
            src_port INTEGER NOT NULL,
            dst_port INTEGER NOT NULL,
            proto TEXT NOT NULL DEFAULT 'tcp',
            ts TEXT NOT NULL,
            kind TEXT NOT NULL,
            payload TEXT NOT NULL,
            prev_hash TEXT NOT NULL,
            hash TEXT NOT NULL
        )"""
    )
    columns = {row[1] for row in db.execute("PRAGMA table_info(events)")}
    for name, definition in {
        "seq": "INTEGER NOT NULL DEFAULT 1",
        "dst_port": "INTEGER NOT NULL DEFAULT 0",
        "proto": "TEXT NOT NULL DEFAULT 'tcp'",
    }.items():
        if name not in columns:
            db.execute(f"ALTER TABLE events ADD COLUMN {name} {definition}")

    db.execute("CREATE INDEX IF NOT EXISTS events_session_idx ON events(session_id, decoy_id)")
    db.execute("CREATE INDEX IF NOT EXISTS events_decoy_seq_idx ON events(decoy_id, seq)")
    db.execute("CREATE INDEX IF NOT EXISTS events_ts_idx ON events(ts)")
    db.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    db.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('panic','false')")
    db.execute(
        """CREATE TABLE IF NOT EXISTS adaptations (
            action_id TEXT PRIMARY KEY,
            action_json TEXT NOT NULL,
            approved INTEGER NOT NULL,
            reason TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    db.execute(
        """CREATE TABLE IF NOT EXISTS proposals (
            action_id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            decoy_type TEXT NOT NULL,
            reason TEXT NOT NULL,
            parameters_json TEXT NOT NULL,
            created_at REAL NOT NULL,
            expires_at REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
        )"""
    )
    db.commit()
