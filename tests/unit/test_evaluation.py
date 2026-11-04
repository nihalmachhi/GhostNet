from __future__ import annotations

from pathlib import Path

from ghostnet.evaluation import evaluate, render_markdown, synthetic_scenarios

ROOT = Path(__file__).resolve().parents[2]


def test_synthetic_evaluation_is_deterministic_and_honest() -> None:
    report = evaluate(ROOT)
    assert report["kind"] == "synthetic"
    assert report["sessions"] == len(synthetic_scenarios()) == 11
    assert report["containment"]["passed"] is True
    assert report["metrics"]["accuracy"] == 0.9091

    details = {item["scenario"]: item for item in report["details"]}
    assert details["credential_stuffing"]["predicted"] == "credential_stuffing"
    assert details["canary_followup"]["predicted"] == "canary_followup"
    # Deliberate boundary case: jittered commands fall outside the low-variance rule.
    assert details["scripted_interaction_jittered"]["predicted"] == "interactive_exploration"


def test_markdown_labels_synthetic_data() -> None:
    markdown = render_markdown(evaluate(ROOT))
    assert "Synthetic data" in markdown
    assert "not evidence of" in markdown
    assert "credential_stuffing" in markdown
