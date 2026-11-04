from __future__ import annotations

from ghostnet.export.csvout import sessions_csv, sessions_jsonl
from ghostnet.export.navigator import navigator_layer
from ghostnet.export.stix import stix_bundle
from ghostnet.pipeline.attack_map import map_behavior


def _session() -> dict:
    return {
        "id": "s-1",
        "decoy_id": "web-admin-01",
        "src_hash": "h:" + "a" * 24,
        "started_at": "2026-01-01T00:00:00+00:00",
        "ended_at": "2026-01-01T00:00:05+00:00",
        "n_events": 3,
        "n_auth": 1,
        "n_commands": 1,
        "class_label": "canary_followup",
        "rule_id": "canary_followup",
        "rule_score": 0.99,
        "attack": map_behavior("canary_followup"),
    }


def test_navigator_layer_uses_observation_counts() -> None:
    layer = navigator_layer([_session()])
    assert layer["techniques"][0]["techniqueID"] == "T1552"
    assert layer["techniques"][0]["score"] == 1


def test_stix_bundle_has_no_fake_indicators() -> None:
    bundle = stix_bundle([_session()])
    types = [item["type"] for item in bundle["objects"]]
    assert "indicator" not in types
    assert "observed-data" in types
    assert "attack-pattern" in types


def test_csv_and_jsonl_exports() -> None:
    text = sessions_csv([_session()])
    assert "class_label" in text and "canary_followup" in text
    assert sessions_jsonl([_session()]).startswith("{")
