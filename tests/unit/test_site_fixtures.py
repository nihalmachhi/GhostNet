from __future__ import annotations

import json
from pathlib import Path

import yaml

from ghostnet.pipeline.rules_engine import classify_features

ROOT = Path(__file__).resolve().parents[2]
SIM = ROOT / "site" / "src" / "features" / "simulator" / "__fixtures__"


def _load(name: str) -> object:
    return json.loads((SIM / name).read_text(encoding="utf-8"))


def _load_data(name: str) -> object:
    return json.loads((ROOT / "site" / "src" / "data" / name).read_text(encoding="utf-8"))


def test_site_rule_fixture_matches_yaml() -> None:
    expected = yaml.safe_load(
        (ROOT / "src" / "ghostnet" / "rules" / "classify.yaml").read_text(encoding="utf-8")
    )["rules"]
    assert _load("rules.generated.json") == expected


def test_site_classification_fixture_matches_python() -> None:
    cases = _load("classification.json")
    assert isinstance(cases, list)
    for case in cases:
        assert classify_features(case["features"]) == case["expected"], case["name"]


def test_site_results_fixture_is_labelled_synthetic() -> None:
    results = _load_data("results.generated.json")
    assert isinstance(results, dict)
    assert results["data_kind"] == "synthetic"
    assert results["containment"]["passed"] is True
    assert results["boundary_case"]["predicted"] == "interactive_exploration"
