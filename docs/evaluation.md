# Synthetic evaluation

> **Synthetic data.** This report is generated from hand-built fixtures. It verifies
> the classification pipeline and containment configuration. It is not evidence of
> real-world detection quality.

- Scenarios: **11**
- Accuracy: **90.91%**
- Macro F1: **91.67%**
- Containment: **pass**

## Per-label results

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `benign_noise` | 1.00 | 1.00 | 1.00 | 1 |
| `canary_followup` | 1.00 | 1.00 | 1.00 | 1 |
| `credential_guessing` | 1.00 | 1.00 | 1.00 | 1 |
| `credential_stuffing` | 1.00 | 1.00 | 1.00 | 2 |
| `exploit_attempt` | 1.00 | 1.00 | 1.00 | 1 |
| `interactive_exploration` | 0.50 | 1.00 | 0.67 | 1 |
| `scan_discovery` | 1.00 | 1.00 | 1.00 | 2 |
| `scripted_interaction` | 1.00 | 0.50 | 0.67 | 2 |

## Scenarios

| Scenario | Expected | Predicted | Rule | Score | ATT&CK |
|---|---|---|---|---:|---|
| `scan_discovery` | `scan_discovery` | `scan_discovery` | `scan_discovery` | 0.68 | Reconnaissance / T1595.002 |
| `credential_stuffing` | `credential_stuffing` | `credential_stuffing` | `credential_stuffing` | 0.92 | Credential Access / T1110.004 |
| `credential_guessing` | `credential_guessing` | `credential_guessing` | `credential_guessing` | 0.85 | Credential Access / T1110.001 |
| `exploit_attempt` | `exploit_attempt` | `exploit_attempt` | `exploit_attempt` | 0.90 | Initial Access / T1190 |
| `canary_followup` | `canary_followup` | `canary_followup` | `canary_followup` | 0.99 | Credential Access / T1552 |
| `scripted_interaction` | `scripted_interaction` | `scripted_interaction` | `scripted_interaction` | 0.60 | — |
| `scripted_interaction_jittered` | `scripted_interaction` | `interactive_exploration` | `interactive_exploration` | 0.50 | — |
| `interactive_exploration` | `interactive_exploration` | `interactive_exploration` | `interactive_exploration` | 0.50 | — |
| `benign_noise` | `benign_noise` | `benign_noise` | `benign_noise` | 0.20 | — |
| `scan_discovery_second` | `scan_discovery` | `scan_discovery` | `scan_discovery` | 0.68 | Reconnaissance / T1595.002 |
| `credential_stuffing_second` | `credential_stuffing` | `credential_stuffing` | `credential_stuffing` | 0.92 | Credential Access / T1110.004 |

## How to reproduce

```bash
uv run python -m ghostnet.evaluation
```

The command rewrites `docs/evaluation.json` and `docs/evaluation.md`.
