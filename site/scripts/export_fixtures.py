"""Generate the site's parity fixtures from the Python implementation.

Run from the repository root:

    uv run python site/scripts/export_fixtures.py

The generated JSON files are committed so the site can build without Python.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from ghostnet.evaluation import evaluate
from ghostnet.pipeline.attack_map import map_behavior
from ghostnet.pipeline.rules_engine import classify_features

ROOT = Path(__file__).resolve().parents[2]
SITE = Path(__file__).resolve().parents[1]
DATA = SITE / "src" / "data"
SIM = SITE / "src" / "features" / "simulator" / "__fixtures__"
RULES = ROOT / "src" / "ghostnet" / "rules"

CASES: list[dict[str, Any]] = [
    {
        "name": "canary_followup",
        "features": {
            "n_events": 2,
            "n_auth": 0,
            "n_unique_users": 0,
            "n_commands": 0,
            "duration_s": 1.0,
            "iat_cv": 0.0,
            "has_token": True,
            "exploit_paths": 0,
        },
    },
    {
        "name": "exploit_attempt",
        "features": {
            "n_events": 3,
            "n_auth": 0,
            "n_unique_users": 0,
            "n_commands": 0,
            "duration_s": 4.0,
            "iat_cv": 1.0,
            "has_token": False,
            "exploit_paths": 1,
        },
    },
    {
        "name": "credential_stuffing",
        "features": {
            "n_events": 5,
            "n_auth": 5,
            "n_unique_users": 5,
            "n_commands": 0,
            "duration_s": 4.0,
            "iat_cv": 0.0,
            "has_token": False,
            "exploit_paths": 0,
        },
    },
    {
        "name": "credential_guessing",
        "features": {
            "n_events": 4,
            "n_auth": 4,
            "n_unique_users": 1,
            "n_commands": 0,
            "duration_s": 3.0,
            "iat_cv": 0.0,
            "has_token": False,
            "exploit_paths": 0,
        },
    },
    {
        "name": "scan_discovery",
        "features": {
            "n_events": 1,
            "n_auth": 0,
            "n_unique_users": 0,
            "n_commands": 0,
            "duration_s": 0.0,
            "iat_cv": 0.0,
            "has_token": False,
            "exploit_paths": 0,
        },
    },
    {
        "name": "scripted_interaction",
        "features": {
            "n_events": 4,
            "n_auth": 0,
            "n_unique_users": 0,
            "n_commands": 4,
            "duration_s": 6.0,
            "iat_cv": 0.0,
            "has_token": False,
            "exploit_paths": 0,
        },
    },
    {
        "name": "interactive_exploration",
        "features": {
            "n_events": 3,
            "n_auth": 0,
            "n_unique_users": 0,
            "n_commands": 2,
            "duration_s": 8.0,
            "iat_cv": 1.0,
            "has_token": False,
            "exploit_paths": 0,
        },
    },
    {
        "name": "benign_noise",
        "features": {
            "n_events": 2,
            "n_auth": 0,
            "n_unique_users": 0,
            "n_commands": 0,
            "duration_s": 4.0,
            "iat_cv": 1.0,
            "has_token": False,
            "exploit_paths": 0,
        },
    },
    {
        "name": "jittered_scripted_boundary",
        "features": {
            "n_events": 4,
            "n_auth": 0,
            "n_unique_users": 0,
            "n_commands": 4,
            "duration_s": 9.5,
            "iat_cv": 0.9,
            "has_token": False,
            "exploit_paths": 0,
        },
    },
]


def _dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    rules = yaml.safe_load((RULES / "classify.yaml").read_text(encoding="utf-8"))
    attack = yaml.safe_load((RULES / "attack_map.yaml").read_text(encoding="utf-8"))
    _dump(SIM / "rules.generated.json", rules["rules"])
    _dump(SIM / "attack_map.generated.json", attack)

    cases = [
        {
            "name": case["name"],
            "features": case["features"],
            "expected": classify_features(case["features"]),
        }
        for case in CASES
    ]
    _dump(SIM / "classification.json", cases)

    report = evaluate(ROOT)
    labels = report["metrics"]["per_label"]
    results = {
        "data_kind": report["kind"],
        "scenarios": report["sessions"],
        "accuracy": report["metrics"]["accuracy"],
        "macro_f1": report["metrics"]["macro_f1"],
        "containment": report["containment"],
        "labels": [
            {
                "label": label,
                "precision": values["precision"],
                "recall": values["recall"],
                "f1": values["f1"],
                "support": values["support"],
                "attack": map_behavior(label),
            }
            for label, values in labels.items()
        ],
        "boundary_case": next(
            item
            for item in report["details"]
            if item["scenario"] == "scripted_interaction_jittered"
        ),
    }
    _dump(DATA / "results.generated.json", results)
    print(f"wrote fixtures under {SIM} and {DATA}")


if __name__ == "__main__":
    main()
