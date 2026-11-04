from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

NAMESPACE = uuid.UUID("8f4d7c1e-6d2a-4f1a-9f1c-2b7c6a1d0e33")


def _stix_id(kind: str, value: str) -> str:
    return f"{kind}--{uuid.uuid5(NAMESPACE, kind + ':' + value)}"


def _attack_patterns(sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for session in sessions:
        for mapping in session.get("attack", []):
            technique = str(mapping["technique"])
            seen[technique] = {
                "type": "attack-pattern",
                "spec_version": "2.1",
                "id": _stix_id("attack-pattern", technique),
                "created": "2026-01-01T00:00:00.000Z",
                "modified": "2026-01-01T00:00:00.000Z",
                "name": str(mapping["name"]),
                "external_references": [
                    {
                        "source_name": "mitre-attack",
                        "external_id": technique,
                        "url": f"https://attack.mitre.org/techniques/{technique.replace('.', '/')}/",
                    }
                ],
            }
    return list(seen.values())


def stix_bundle(sessions: list[dict[str, Any]]) -> dict[str, Any]:
    """Export attack patterns and observed sessions.

    Hashed source identifiers are not actionable IOCs, so no indicator objects
    are fabricated from them.
    """
    objects: list[dict[str, Any]] = [
        {
            "type": "identity",
            "spec_version": "2.1",
            "id": _stix_id("identity", "ghostnet"),
            "created": "2026-01-01T00:00:00.000Z",
            "modified": "2026-01-01T00:00:00.000Z",
            "name": "GhostNet defensive deception lab",
            "identity_class": "system",
        }
    ]
    objects.extend(_attack_patterns(sessions))
    for session in sessions:
        objects.append(
            {
                "type": "observed-data",
                "spec_version": "2.1",
                "id": _stix_id("observed-data", str(session["id"])),
                "created": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "modified": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "first_observed": session["started_at"],
                "last_observed": session["ended_at"],
                "number_observed": int(session["n_events"]),
                "x_ghostnet_session_id": session["id"],
                "x_ghostnet_decoy": session["decoy_id"],
                "x_ghostnet_src_hash": session["src_hash"],
                "x_ghostnet_label": session["class_label"],
                "x_ghostnet_rule_score": session["rule_score"],
            }
        )
    return {
        "type": "bundle",
        "id": _stix_id("bundle", "ghostnet-export"),
        "objects": objects,
    }
