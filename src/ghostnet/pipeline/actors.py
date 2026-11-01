from __future__ import annotations

from collections import defaultdict
from typing import Any


def link_actors(
    sessions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    parent = {session["id"]: session["id"] for session in sessions}
    evidence: dict[tuple[str, str], set[str]] = defaultdict(set)

    def root(value: str) -> str:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    for index, left in enumerate(sessions):
        for right in sessions[index + 1 :]:
            shared = set(left["tokens"]) & set(right["tokens"])
            if shared:
                key = (left["id"], right["id"])
                evidence[key].update("shared_canary:" + token for token in shared)
                parent[root(right["id"])] = root(left["id"])
            elif left["src_hash"] == right["src_hash"] and left["src_hash"]:
                key = (left["id"], right["id"])
                evidence[key].add("same_hashed_source")
                parent[root(right["id"])] = root(left["id"])
    groups: dict[str, list[str]] = defaultdict(list)
    for session in sessions:
        groups[root(session["id"])].append(session["id"])
    actor_ids: dict[str, str] = {}
    actors = []
    for index, (_leader, members) in enumerate(sorted(groups.items()), 1):
        actor_id = f"actor-{index:03d}"
        for member in members:
            actor_ids[member] = actor_id
        actor_evidence = sorted(
            {
                item
                for pair, values in evidence.items()
                if pair[0] in members or pair[1] in members
                for item in values
            }
        )
        actors.append(
            {
                "id": actor_id,
                "session_ids": members,
                "confidence": 0.95
                if any(e.startswith("shared_canary") for e in actor_evidence)
                else 0.72
                if len(members) > 1
                else 0.35,
                "evidence": actor_evidence,
            }
        )
    edges = [
        {"source": a, "target": b, "evidence": sorted(values)}
        for (a, b), values in evidence.items()
    ]
    for session in sessions:
        session["actor_id"] = actor_ids[session["id"]]
    return actors, edges
