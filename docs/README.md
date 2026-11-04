# GhostNet documentation

GhostNet is a contained defensive deception lab. These documents describe what it
does, how it is put together, what it deliberately does not do, and how to verify
the claims in the README.

| Document | Purpose |
|---|---|
| [Architecture](architecture.md) | Services, trust boundaries and the event path |
| [Threat model](threat-model.md) | Assets, adversaries, mitigations and residual risk |
| [Privacy](privacy.md) | Exactly what is captured, hashed, excluded and retained |
| [API](api.md) | Admin and ingest endpoints, authentication and limits |
| [Operations](operations.md) | Local setup, lifecycle, panic, exports and metrics |
| [Testing](testing.md) | Test, lint, type-check, coverage and CI commands |
| [Evaluation](evaluation.md) | Generated synthetic evaluation report |
| [Limitations](limitations.md) | Honest scope and known weaknesses |

> **Synthetic data.** The evaluation report is generated from hand-built fixtures.
> It verifies the pipeline; it is not evidence of real-world detection quality.
