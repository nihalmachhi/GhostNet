from __future__ import annotations

import csv
import io
import json
from typing import Any

SESSION_FIELDS = (
    "id",
    "decoy_id",
    "src_hash",
    "started_at",
    "ended_at",
    "n_events",
    "n_auth",
    "n_commands",
    "class_label",
    "rule_id",
    "rule_score",
)


def sessions_csv(sessions: list[dict[str, Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=SESSION_FIELDS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(sessions)
    return buffer.getvalue()


def sessions_jsonl(sessions: list[dict[str, Any]]) -> str:
    return "\n".join(json.dumps(session, sort_keys=True) for session in sessions) + "\n"
