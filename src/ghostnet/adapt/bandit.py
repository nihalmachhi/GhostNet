from __future__ import annotations

import json
import random
from pathlib import Path

from ghostnet.adapt.policy import Action


class EpsilonGreedyPolicy:
    """Seeded, context-aware epsilon-greedy selector.

    It only proposes actions. Approval and deployment stay with the analyst and
    the static policy; ``update`` records observed engagement as a reward.
    """

    def __init__(
        self, epsilon: float = 0.1, seed: int = 7, state_path: str | Path | None = None
    ) -> None:
        if not 0 <= epsilon <= 1:
            raise ValueError("epsilon must be between 0 and 1")
        self.epsilon = epsilon
        self.random = random.Random(seed)  # noqa: S311 - reproducible policy sampling, not crypto
        self.values: dict[str, float] = {}
        self.counts: dict[str, int] = {}
        self.state_path = Path(state_path) if state_path else None
        self.load()

    @staticmethod
    def _key(context: str, action: Action) -> str:
        return f"{context}|{action.decoy_type}|{action.kind}"

    def propose(self, context: str, actions: list[Action]) -> Action:
        if not actions:
            raise ValueError("At least one pre-approved action is required")
        if self.random.random() < self.epsilon:
            return self.random.choice(actions)
        return max(
            actions,
            key=lambda action: (
                self.values.get(self._key(context, action), 0.0),
                -self.counts.get(self._key(context, action), 0),
                action.action_id,
            ),
        )

    def update(self, action: Action, reward: float, context: str = "quiet") -> None:
        if not 0 <= reward <= 1:
            raise ValueError("reward must be between 0 and 1")
        key = self._key(context, action)
        count = self.counts.get(key, 0)
        self.values[key] = (self.values.get(key, 0.0) * count + reward) / (count + 1)
        self.counts[key] = count + 1
        self.save()

    def save(self) -> None:
        if self.state_path is None:
            return
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(
            json.dumps(
                {"epsilon": self.epsilon, "values": self.values, "counts": self.counts},
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    def load(self) -> None:
        if self.state_path is None or not self.state_path.exists():
            return
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
            self.values = {str(k): float(v) for k, v in payload.get("values", {}).items()}
            self.counts = {str(k): int(v) for k, v in payload.get("counts", {}).items()}
        except (OSError, ValueError, TypeError):
            self.values, self.counts = {}, {}
