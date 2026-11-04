from __future__ import annotations

import pytest

from ghostnet.adapt.bandit import EpsilonGreedyPolicy
from ghostnet.adapt.policy import Action, allowed_actions, approve, validate_parameters


def _actions() -> list[Action]:
    return [
        Action("a1", "rotate_fake_credential", "web-admin", "test", {}),
        Action("a2", "add_lure", "web-admin", "test", {"text": "hello"}),
        Action("a3", "response_delay_ms", "web-admin", "test", {"delay_ms": 80}),
    ]


def test_bandit_is_reproducible_and_updates() -> None:
    first = EpsilonGreedyPolicy(epsilon=0.5, seed=3)
    second = EpsilonGreedyPolicy(epsilon=0.5, seed=3)
    assert [first.propose("scan", _actions()).action_id for _ in range(5)] == [
        second.propose("scan", _actions()).action_id for _ in range(5)
    ]
    chosen = first.propose("scan", _actions())
    first.update(chosen, 1.0, context="scan")
    assert first.counts


def test_bandit_state_persists(tmp_path) -> None:
    path = tmp_path / "bandit.json"
    policy = EpsilonGreedyPolicy(epsilon=0.0, seed=1, state_path=path)
    action = policy.propose("scan", _actions())
    policy.update(action, 0.5, context="scan")
    loaded = EpsilonGreedyPolicy(epsilon=0.0, seed=1, state_path=path)
    assert loaded.counts == policy.counts


def test_bandit_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError):
        EpsilonGreedyPolicy(epsilon=2)
    policy = EpsilonGreedyPolicy()
    with pytest.raises(ValueError):
        policy.propose("x", [])
    with pytest.raises(ValueError):
        policy.update(_actions()[0], 2.0)


def test_policy_allowlist_and_parameters() -> None:
    assert "add_lure" in allowed_actions()
    assert approve(_actions()[0])[0] is True
    assert approve(Action("x", "run_shell", "web-admin", "bad", {}))[0] is False
    assert (
        approve(Action("x", "response_delay_ms", "web-admin", "bad", {"delay_ms": 999}))[0] is False
    )
    assert (
        approve(Action("x", "response_delay_ms", "web-admin", "bad", {"delay_ms": "x"}))[0] is False
    )
    assert approve(Action("x", "add_lure", "web-admin", "bad", {"text": "x" * 300}))[0] is False
    assert validate_parameters("rotate_fake_credential", {})[0] is True
