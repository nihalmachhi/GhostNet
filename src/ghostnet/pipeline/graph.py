from __future__ import annotations

from typing import Any


def behavior_graph(
    sessions: list[dict[str, Any]], actors: list[dict[str, Any]], actor_edges: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for actor in actors:
        nodes.append(
            {
                "id": actor["id"],
                "type": "actor",
                "label": actor["id"],
                "confidence": actor["confidence"],
            }
        )
    for session in sessions:
        nodes.append(
            {
                "id": session["id"],
                "type": "session",
                "label": session["class_label"],
                "decoy_id": session["decoy_id"],
            }
        )
        edges.append(
            {"source": session["actor_id"], "target": session["id"], "type": "observed_session"}
        )
        edges.append({"source": session["id"], "target": session["decoy_id"], "type": "touched"})
        nodes.append({"id": session["decoy_id"], "type": "decoy", "label": session["decoy_id"]})
        for token in session["tokens"]:
            token_id = "token:" + token
            nodes.append({"id": token_id, "type": "canary", "label": token[:12] + "..."})
            edges.append({"source": session["id"], "target": token_id, "type": "token_seen"})
    edges.extend(
        {
            "source": edge["source"],
            "target": edge["target"],
            "type": "linked",
            "evidence": edge["evidence"],
        }
        for edge in actor_edges
    )
    unique = {node["id"]: node for node in nodes}
    return {"nodes": list(unique.values()), "edges": edges}
