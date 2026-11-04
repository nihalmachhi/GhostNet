# Changelog

All notable changes are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-11-04

### Added

- Separate `admin_api` and `ingest_api` apps with distinct trust boundaries.
- `orchestrator/edge_proxy.py` exposing only decoy ports on loopback.
- `core/` settings, secret validation, logging and constant-time token helpers.
- Per-decoy HMAC-SHA256 event chains with signed head checkpoints.
- SQLite migrations, `BEGIN IMMEDIATE` appends and server-owned integrity fields.
- Ordered YAML classification rules with rule id, score and evidence.
- Actor linking, behavior graph and ATT&CK heatmap.
- Allowlisted, TTL-bound adaptation proposals with analyst approval records.
- ATT&CK Navigator, STIX 2.1, CSV and JSONL exports plus a `ghostnet` CLI.
- Prometheus text metrics for event count and panic state.
- Cowrie-style JSONL adapter for authorized evaluation data.
- Deterministic synthetic evaluation generator and generated report.
- Documentation set: architecture, threat model, privacy, API, operations,
  testing, evaluation and limitations.
- 80 tests covering settings, privacy, chain integrity, storage, sessions,
  rules, actors, policy, exports, APIs, decoys, emitter, edge proxy,
  containment and evaluation. Branch coverage is above the 80% gate.
- React 19 showcase site with a tested in-browser rule/session simulator.

### Changed

- Published ports are loopback-only and the deception network is internal.
- Decoy containers run non-root with read-only roots, dropped capabilities,
  no-new-privileges, tmpfs and resource limits.
- README and site now describe the split control plane and generated evidence.

### Removed

- The single `ghostnet.api` app and the old `sensors.client` module.
- The previous `dashboard/` folder; the static site is the only front end.

### Fixed

- Hash-chain verification now checks per-decoy sequence continuity.
- Session detail queries the exact source/decoy/time window instead of a
  truncated global window.
- Ingest rejects oversized bodies before parsing.
- Panic polling and emitter key checks fail closed on placeholders.

## [0.1.0] - 2026-10-28

- Initial prototype: decoys, SQLite storage, basic sessions and a React site.
- Baseline audit: 5 tests passed; ruff, formatting and mypy passed.
- The prototype did not meet the supplied containment, privacy, event-integrity,
  coverage or API-separation requirements. Work continued in 0.2.0.

[0.2.0]: https://github.com/nihalmachhi/GhostNet/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/nihalmachhi/GhostNet/releases/tag/v0.1.0
