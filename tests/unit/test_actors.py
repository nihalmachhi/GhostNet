from __future__ import annotations

from ghostnet.pipeline.actors import link_actors


def _session(session_id: str, src: str, tokens: list[str] | None = None) -> dict:
    return {"id": session_id, "src_hash": src, "tokens": tokens or []}


def test_shared_token_links_sessions() -> None:
    sessions = [_session("a", "h:1", ["t1"]), _session("b", "h:2", ["t1"]), _session("c", "h:3")]
    actors, edges = link_actors(sessions)
    assert len(actors) == 2
    assert any("shared_canary:t1" in edge["evidence"] for edge in edges)
    assert sessions[0]["actor_id"] == sessions[1]["actor_id"]


def test_shared_source_links_sessions() -> None:
    sessions = [_session("a", "h:1"), _session("b", "h:1"), _session("c", "h:2")]
    actors, edges = link_actors(sessions)
    assert len(actors) == 2
    assert any("same_hashed_source" in edge["evidence"] for edge in edges)


def test_singleton_actor_has_low_confidence() -> None:
    actors, edges = link_actors([_session("a", "h:1")])
    assert actors[0]["confidence"] == 0.35
    assert edges == []
