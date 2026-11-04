from __future__ import annotations

from collections import defaultdict
from typing import Any


class _UnionFind:
    def __init__(self, values: list[str]) -> None:
        self.parent = {value: value for value in values}

    def find(self, value: str) -> str:
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left: str, right: str) -> None:
        self.parent[self.find(right)] = self.find(left)


def link_actors(
    sessions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Link sessions by shared canary evidence, then by hashed source.

    Indexes keep this near-linear; the previous pairwise loop was O(n²). NAT
    caveat: a shared source hash can merge unrelated people behind one address.
    """
    union = _UnionFind([str(session["id"]) for session in sessions])
    evidence: dict[tuple[str, str], set[str]] = defaultdict(set)

    by_token: dict[str, list[str]] = defaultdict(list)
    by_source: dict[str, list[str]] = defaultdict(list)
    for session in sessions:
        session_id = str(session["id"])
        for token in session.get("tokens", []):
            by_token[str(token)].append(session_id)
        if session.get("src_hash"):
            by_source[str(session["src_hash"])].append(session_id)

    for token, members in by_token.items():
        for member in members[1:]:
            pair = (min(members[0], member), max(members[0], member))
            evidence[pair].add("shared_canary:" + token)
            union.union(members[0], member)
    for _source, members in by_source.items():
        for member in members[1:]:
            pair = (min(members[0], member), max(members[0], member))
            evidence[pair].add("same_hashed_source")
            union.union(members[0], member)

    groups: dict[str, list[str]] = defaultdict(list)
    for session in sessions:
        groups[union.find(str(session["id"]))].append(str(session["id"]))

    actor_ids: dict[str, str] = {}
    actors: list[dict[str, Any]] = []
    for index, members in enumerate(sorted(groups.values(), key=lambda item: sorted(item)[0]), 1):
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
                "session_ids": sorted(members),
                "confidence": 0.95
                if any(item.startswith("shared_canary") for item in actor_evidence)
                else 0.72
                if len(members) > 1
                else 0.35,
                "evidence": actor_evidence,
            }
        )
    edges = [
        {"source": pair[0], "target": pair[1], "evidence": sorted(values)}
        for pair, values in evidence.items()
    ]
    for session in sessions:
        session["actor_id"] = actor_ids[str(session["id"])]
    return actors, edges
