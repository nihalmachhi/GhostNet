from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from ghostnet.orchestrator.containment_check import check_compose_config
from ghostnet.pipeline.attack_map import map_behavior
from ghostnet.pipeline.sessions import build_sessions

BASE = datetime(2026, 1, 1, tzinfo=UTC)
LABELS = (
    "benign_noise",
    "canary_followup",
    "credential_guessing",
    "credential_stuffing",
    "exploit_attempt",
    "interactive_exploration",
    "scan_discovery",
    "scripted_interaction",
)


def _ts(seconds: float) -> str:
    return (BASE + timedelta(seconds=seconds)).isoformat()


def _event(
    scenario: str,
    seconds: float,
    kind: str,
    data: dict[str, Any] | None = None,
    *,
    decoy_id: str = "web-admin-01",
    decoy_type: str = "web-admin",
    dst_port: int = 8081,
) -> dict[str, Any]:
    source = "h:" + hashlib.sha256(scenario.encode()).hexdigest()[:24]
    return {
        "event_id": "0" * 32,
        "seq": 1,
        "decoy_id": decoy_id,
        "decoy_type": decoy_type,
        "session_id": f"{scenario}:{decoy_id}",
        "src_hash": source,
        "src_port": 40000,
        "dst_port": dst_port,
        "proto": "tcp",
        "ts": _ts(seconds),
        "kind": kind,
        "data": data or {},
        "prev_hash": "",
        "hash": "",
    }


def _auth(user: str) -> dict[str, Any]:
    return {"user_hash": f"u-{user}", "user_len": 4, "user_class": "other", "password_len": 8}


def synthetic_scenarios() -> list[tuple[str, list[dict[str, Any]]]]:
    """Return deterministic, labelled synthetic sessions.

    These are hand-built fixtures for pipeline validation, not observations of
    real traffic. Every scenario uses its own hashed source so sessions never
    merge.
    """
    return [
        (
            "scan_discovery",
            [_event("scan_discovery", 0, "conn_open", {"service": "web-admin"})],
        ),
        (
            "credential_stuffing",
            [
                _event("credential_stuffing", index, "auth_attempt", _auth(f"user{index}"))
                for index in range(5)
            ],
        ),
        (
            "credential_guessing",
            [
                _event("credential_guessing", index, "auth_attempt", _auth("root"))
                for index in range(4)
            ],
        ),
        (
            "exploit_attempt",
            [
                _event(
                    "exploit_attempt",
                    index * 2,
                    "http_request",
                    {"method": "GET", "path": "/wp-admin/setup.php"},
                )
                for index in range(3)
            ],
        ),
        (
            "canary_followup",
            [
                _event("canary_followup", 0, "http_request", {"method": "GET", "path": "/"}),
                _event("canary_followup", 1, "token_seen", {"canary_id": "abc123def456"}),
            ],
        ),
        (
            "scripted_interaction",
            [
                _event("scripted_interaction", index * 2, "command", {"command": "WHOAMI"})
                for index in range(4)
            ],
        ),
        (
            "scripted_interaction_jittered",
            [
                _event("scripted_interaction_jittered", seconds, "command", {"command": "WHOAMI"})
                for seconds in (0, 1, 8, 9.5)
            ],
        ),
        (
            "interactive_exploration",
            [
                _event("interactive_exploration", 0, "conn_open", {"service": "fake-ssh"}),
                _event("interactive_exploration", 0, "command", {"command": "LS"}),
                _event("interactive_exploration", 8, "command", {"command": "CAT"}),
            ],
        ),
        (
            "benign_noise",
            [
                _event("benign_noise", 0, "conn_open", {"service": "fake-db"}),
                _event("benign_noise", 4, "conn_open", {"service": "fake-db"}),
            ],
        ),
        (
            "scan_discovery_second",
            [
                _event(
                    "scan_discovery_second",
                    0,
                    "conn_open",
                    {"service": "fake-ssh"},
                    decoy_id="fake-ssh-01",
                    decoy_type="fake-ssh",
                    dst_port=2222,
                )
            ],
        ),
        (
            "credential_stuffing_second",
            [
                _event(
                    "credential_stuffing_second",
                    index,
                    "auth_attempt",
                    _auth(f"name{index}"),
                    decoy_id="fake-ssh-01",
                    decoy_type="fake-ssh",
                    dst_port=2222,
                )
                for index in range(4)
            ],
        ),
    ]


def _scores(expected: list[str], predicted: list[str]) -> dict[str, Any]:
    matrix: dict[str, dict[str, int]] = {label: dict.fromkeys(LABELS, 0) for label in LABELS}
    for truth, guess in zip(expected, predicted, strict=True):
        matrix[truth][guess] += 1

    per_label: dict[str, dict[str, float]] = {}
    for label in LABELS:
        true_positive = matrix[label][label]
        false_positive = sum(matrix[other][label] for other in LABELS if other != label)
        false_negative = sum(matrix[label][other] for other in LABELS if other != label)
        precision = (
            true_positive / (true_positive + false_positive)
            if true_positive + false_positive
            else 0.0
        )
        recall = (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative
            else 0.0
        )
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_label[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": true_positive + false_negative,
        }

    correct = sum(1 for truth, guess in zip(expected, predicted, strict=True) if truth == guess)
    return {
        "accuracy": round(correct / len(expected), 4) if expected else 0.0,
        "macro_f1": round(sum(item["f1"] for item in per_label.values()) / len(LABELS), 4),
        "per_label": per_label,
        "confusion_matrix": matrix,
    }


def evaluate(repo_root: Path | None = None) -> dict[str, Any]:
    """Run the deterministic synthetic evaluation and return a report."""
    root = repo_root or Path(__file__).resolve().parents[2]
    scenarios = synthetic_scenarios()
    events = [event for _, rows in scenarios for event in rows]
    sessions = build_sessions(events)
    by_session = {str(session["id"]): session for session in sessions}

    expected: list[str] = []
    predicted: list[str] = []
    details: list[dict[str, Any]] = []
    for name, rows in scenarios:
        truth = name.removesuffix("_second").removesuffix("_jittered")
        session_id = f"s-{rows[0]['decoy_id']}-{rows[0]['src_hash'][-8:]}-001"
        session = by_session[session_id]
        expected.append(truth)
        predicted.append(str(session["class_label"]))
        details.append(
            {
                "scenario": name,
                "expected": truth,
                "predicted": session["class_label"],
                "rule_id": session["rule_id"],
                "rule_score": session["rule_score"],
                "attack": map_behavior(str(session["class_label"])),
                "event_count": session["n_events"],
            }
        )

    compose = root / "docker-compose.yml"
    containment = check_compose_config(compose) if compose.exists() else ["compose_missing"]
    return {
        "kind": "synthetic",
        "description": (
            "Deterministic synthetic sessions generated from hand-built fixtures. "
            "They validate the rule pipeline; they are not real-world detection evidence. "
            "One scripted scenario is deliberately jittered to expose a rule boundary."
        ),
        "sessions": len(sessions),
        "labels": list(LABELS),
        "metrics": _scores(expected, predicted),
        "containment": {
            "path": str(compose.relative_to(root)) if compose.exists() else "docker-compose.yml",
            "failures": containment,
            "passed": not containment,
        },
        "details": details,
    }


def render_markdown(report: dict[str, Any]) -> str:
    metrics = report["metrics"]
    lines = [
        "# Synthetic evaluation",
        "",
        "> **Synthetic data.** This report is generated from hand-built fixtures. It verifies",
        "> the classification pipeline and containment configuration. It is not evidence of",
        "> real-world detection quality.",
        "",
        f"- Scenarios: **{report['sessions']}**",
        f"- Accuracy: **{metrics['accuracy']:.2%}**",
        f"- Macro F1: **{metrics['macro_f1']:.2%}**",
        f"- Containment: **{'pass' if report['containment']['passed'] else 'FAIL'}**",
        "",
        "## Per-label results",
        "",
        "| Label | Precision | Recall | F1 | Support |",
        "|---|---:|---:|---:|---:|",
    ]
    for label, values in metrics["per_label"].items():
        lines.append(
            f"| `{label}` | {values['precision']:.2f} | {values['recall']:.2f} | "
            f"{values['f1']:.2f} | {values['support']} |"
        )
    lines.extend(
        [
            "",
            "## Scenarios",
            "",
            "| Scenario | Expected | Predicted | Rule | Score | ATT&CK |",
            "|---|---|---|---|---:|---|",
        ]
    )
    for detail in report["details"]:
        attack = (
            ", ".join(f"{item['tactic']} / {item['technique']}" for item in detail["attack"]) or "—"
        )
        lines.append(
            f"| `{detail['scenario']}` | `{detail['expected']}` | "
            f"`{detail['predicted']}` | `{detail['rule_id']}` | "
            f"{detail['rule_score']:.2f} | {attack} |"
        )
    lines.extend(
        [
            "",
            "## How to reproduce",
            "",
            "```bash",
            "uv run python -m ghostnet.evaluation",
            "```",
            "",
            "The command rewrites `docs/evaluation.json` and `docs/evaluation.md`.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the synthetic GhostNet evaluation")
    parser.add_argument("--out", default="docs", help="Directory for evaluation.json and .md")
    args = parser.parse_args()
    report = evaluate()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "evaluation.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "evaluation.md").write_text(render_markdown(report), encoding="utf-8")
    counts = Counter(item["predicted"] for item in report["details"])
    print(f"wrote {out / 'evaluation.json'} and {out / 'evaluation.md'}")
    print(f"accuracy={report['metrics']['accuracy']:.4f} labels={dict(sorted(counts.items()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
