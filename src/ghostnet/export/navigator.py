from __future__ import annotations

from collections import Counter
from typing import Any


def navigator_layer(sessions: list[dict[str, Any]]) -> dict[str, Any]:
    """Build an ATT&CK Navigator layer from observed session mappings."""
    counts: Counter[str] = Counter()
    comments: dict[str, set[str]] = {}
    for session in sessions:
        for mapping in session.get("attack", []):
            technique = str(mapping["technique"])
            counts[technique] += 1
            comments.setdefault(technique, set()).add(str(mapping["tactic"]))
    return {
        "name": "GhostNet observed behavior",
        "versions": {"attack": "15", "navigator": "4.9.0", "layer": "4.5"},
        "domain": "enterprise-attack",
        "description": (
            "Rule-based labels from inert decoy sessions. Scores are observation counts, "
            "not confidence or attribution."
        ),
        "techniques": [
            {
                "techniqueID": technique,
                "score": count,
                "comment": "Tactics: " + ", ".join(sorted(comments[technique])),
                "enabled": True,
            }
            for technique, count in sorted(counts.items())
        ],
    }
