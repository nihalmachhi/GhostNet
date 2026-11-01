from __future__ import annotations

from collections import defaultdict

from ghostnet.adapt.policy import Action


class EpsilonGreedyPolicy:
    """Small auditable epsilon-greedy selector; it proposes, never deploys actions."""

    def __init__(self) -> None:
        self.values: dict[str, float] = defaultdict(float)
        self.counts: dict[str, int] = defaultdict(int)

    def propose(self, context: str, actions: list[Action]) -> Action:
        if not actions:
            raise ValueError("At least one pre-approved action is required")
        return max(
            actions,
            key=lambda action: (
                self.values[action.kind],
                -self.counts[action.kind],
                action.action_id,
            ),
        )

    def update(self, action: Action, reward: float) -> None:
        count = self.counts[action.kind]
        self.values[action.kind] = (self.values[action.kind] * count + reward) / (count + 1)
        self.counts[action.kind] = count + 1
