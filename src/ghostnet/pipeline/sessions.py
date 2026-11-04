from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import mean, median, pstdev
from typing import Any

from ghostnet.pipeline.rules_engine import classify_features

IDLE_TIMEOUT_SECONDS = 300.0
EXPLOIT_MARKERS = ("..", "%2e", "/admin", "wp-admin", "/.env", "/etc/passwd", "union select")


def _timestamp(value: str) -> float:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def _session_features(rows: list[dict[str, Any]]) -> dict[str, Any]:
    parsed = [_timestamp(row["ts"]) for row in rows]
    intervals = [max(0.0, parsed[i] - parsed[i - 1]) for i in range(1, len(parsed))]
    auth = [row for row in rows if row["kind"] == "auth_attempt"]
    commands = [row for row in rows if row["kind"] == "command"]
    tokens = [
        str(row["data"]["canary_id"])
        for row in rows
        if row["kind"] == "token_seen" and row["data"].get("canary_id")
    ]
    users = {str(row["data"].get("user_hash", "")) for row in auth if row["data"].get("user_hash")}
    paths = [
        str(row["data"].get("path", ""))
        for row in rows
        if row["kind"] in {"http_request", "auth_attempt"}
    ]
    avg = mean(intervals) if intervals else 0.0
    return {
        "n_events": len(rows),
        "n_auth": len(auth),
        "n_unique_users": len(users),
        "n_commands": len(commands),
        "duration_s": max(0.0, parsed[-1] - parsed[0]),
        "iat_mean": avg,
        "iat_std": pstdev(intervals) if len(intervals) > 1 else 0.0,
        "iat_p50": median(intervals) if intervals else 0.0,
        "iat_cv": (pstdev(intervals) / avg) if len(intervals) > 1 and avg else 0.0,
        "has_token": bool(tokens),
        "token_count": len(tokens),
        "exploit_paths": sum(
            1 for path in paths if any(marker in path.lower() for marker in EXPLOIT_MARKERS)
        ),
        "tokens": tokens,
        "commands": [str(row["data"].get("command", "")) for row in commands],
        "event_kinds": [row["kind"] for row in rows],
    }


def _split_idle(rows: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    previous = 0.0
    for row in rows:
        timestamp = _timestamp(row["ts"])
        if current and timestamp - previous > IDLE_TIMEOUT_SECONDS:
            groups.append(current)
            current = []
        current.append(row)
        previous = timestamp
    if current:
        groups.append(current)
    return groups


def build_sessions(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group events by (hashed source, decoy) and split on an idle timeout.

    Source ports are ephemeral, so they are not part of the session key. Shared
    NAT addresses can therefore merge distinct people; the privacy docs state
    that limitation explicitly.
    """
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        grouped[(str(event["src_hash"]), str(event["decoy_id"]))].append(event)

    sessions: list[dict[str, Any]] = []
    for (src_hash, decoy_id), rows in grouped.items():
        rows.sort(key=lambda row: row["ts"])
        for index, group in enumerate(_split_idle(rows), 1):
            features = _session_features(group)
            classification = classify_features(features)
            started = group[0]["ts"]
            sessions.append(
                {
                    "id": f"s-{decoy_id}-{src_hash[-8:]}-{index:03d}",
                    "decoy_id": decoy_id,
                    "src_hash": src_hash,
                    "src_port": group[0]["src_port"],
                    "started_at": started,
                    "ended_at": group[-1]["ts"],
                    **{key: value for key, value in features.items() if key != "event_kinds"},
                    "class_label": classification["label"],
                    "rule_id": classification["rule_id"],
                    "rule_score": classification["rule_score"],
                    "rule_evidence": classification["rule_evidence"],
                    "events": group,
                }
            )
    return sorted(sessions, key=lambda item: item["started_at"])


def classify_session(session: dict[str, Any]) -> tuple[str, float]:
    """Backwards-compatible tuple form used by older callers and tests."""
    return str(session["class_label"]), float(session["rule_score"])
