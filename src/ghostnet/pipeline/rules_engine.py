from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

OPS = {
    "gte": lambda left, right: left >= right,
    "gt": lambda left, right: left > right,
    "lte": lambda left, right: left <= right,
    "lt": lambda left, right: left < right,
    "eq": lambda left, right: left == right,
    "ne": lambda left, right: left != right,
}


def _rules_path(rules_path: str | Path | None) -> str:
    if rules_path is not None:
        return Path(rules_path).read_text(encoding="utf-8")
    return files("ghostnet.rules").joinpath("classify.yaml").read_text(encoding="utf-8")


@lru_cache(maxsize=4)
def _load_rules(raw: str) -> tuple[dict[str, Any], ...]:
    document = yaml.safe_load(raw) or {}
    return tuple(document.get("rules", []))


def load_rules(rules_path: str | Path | None = None) -> tuple[dict[str, Any], ...]:
    """Load and cache the ordered rule set; the YAML hash can be reported by callers."""
    return _load_rules(_rules_path(rules_path))


def _matches(features: dict[str, Any], condition: dict[str, Any]) -> bool:
    for key, expected in condition.items():
        actual = features.get(key)
        if isinstance(expected, dict):
            if actual is None:
                return False
            for op, value in expected.items():
                if op not in OPS or not OPS[op](actual, value):
                    return False
        elif actual != expected:
            return False
    return True


def classify_features(
    features: dict[str, Any], rules_path: str | Path | None = None
) -> dict[str, Any]:
    """Return the first matching label, its rule score and the evidence that fired."""
    for rule in load_rules(rules_path):
        if _matches(features, rule.get("when", {})):
            return {
                "label": rule["label"],
                "rule_id": rule["id"],
                "rule_score": float(rule["score"]),
                "rule_evidence": list(rule.get("evidence", [])),
            }
    return {
        "label": "benign_noise",
        "rule_id": "fallback",
        "rule_score": 0.1,
        "rule_evidence": ["no rule matched"],
    }


def rule_set_hash(rules_path: str | Path | None = None) -> str:
    import hashlib

    return hashlib.sha256(_rules_path(rules_path).encode()).hexdigest()
