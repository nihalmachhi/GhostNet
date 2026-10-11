from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import mean, median, pstdev
from typing import Any


def build_sessions(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        grouped[event["session_id"]].append(event)
    sessions = []
    for session_id, rows in grouped.items():
        rows.sort(key=lambda row: row["ts"])
        times = [row["ts"] for row in rows]
        parsed = [
            datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() for value in times
        ]
        intervals = [max(0.0, parsed[i] - parsed[i - 1]) for i in range(1, len(parsed))]
        auth = [row for row in rows if row["kind"] == "auth_attempt"]
        commands = [row for row in rows if row["kind"] == "command"]
        users = sorted(
            {str(row["data"].get("user", "")) for row in auth if row["data"].get("user")}
        )
        avg = mean(intervals) if intervals else 0.0
        sessions.append(
            {
                "id": session_id,
                "decoy_id": rows[0]["decoy_id"],
                "src_hash": rows[0]["src_hash"],
                "src_port": rows[0]["src_port"],
                "started_at": times[0],
                "ended_at": times[-1],
                "duration_s": max(0.0, parsed[-1] - parsed[0]),
                "n_events": len(rows),
                "n_auth": len(auth),
                "n_unique_users": len(users),
                "n_commands": len(commands),
                "event_kinds": [r["kind"] for r in rows],
                "commands": [str(row["data"].get("command", "")) for row in commands],
                "tokens": [
                    str(row["data"].get("token", "")) for row in rows if row["kind"] == "token_seen"
                ],
                "iat_mean": avg,
                "iat_std": pstdev(intervals) if len(intervals) > 1 else 0.0,
                "iat_p50": median(intervals) if intervals else 0.0,
                "iat_cv": (pstdev(intervals) / avg) if len(intervals) > 1 and avg else 0.0,
                "events": rows,
            }
        )
    return sorted(sessions, key=lambda item: item["started_at"])


def classify_session(session: dict[str, Any]) -> tuple[str, float]:
    kinds = session["event_kinds"]
    if "token_seen" in kinds:
        return "canary_followup", 0.99
    if session["n_auth"] >= 4:
        return "credential_guessing", min(0.99, 0.75 + 0.04 * session["n_auth"])
    if session["n_commands"] >= 3 and session["iat_cv"] < 0.45:
        return "scripted_interaction", 0.86
    if session["n_commands"] >= 2 and session["duration_s"] >= 5:
        return "interactive_exploration", 0.73
    if session["n_events"] <= 2 and session["duration_s"] < 2:
        return "scan_discovery", 0.68
    return "benign_noise", 0.55
