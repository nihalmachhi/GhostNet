from __future__ import annotations

from ghostnet.pipeline.attack_map import map_behavior


def test_observable_mappings_have_evidence() -> None:
    mapping = map_behavior("credential_guessing")
    assert mapping[0]["technique"] == "T1110.001"
    assert mapping[0]["evidence"]
    assert map_behavior("scripted_interaction") == []
    assert map_behavior("interactive_exploration") == []


def test_unknown_label_is_empty() -> None:
    assert map_behavior("not-a-label") == []
