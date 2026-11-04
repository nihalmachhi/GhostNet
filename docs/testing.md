# Testing

Every claim in the README should be reproducible with one of the commands below.
The suite is deliberately small enough to read and broad enough to cover the
safety boundaries.

## Commands

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -q --cov=ghostnet --cov-report=term-missing
uv run python -m ghostnet.orchestrator.containment_check
uv run python -m ghostnet.evaluation
uv run python site/scripts/export_fixtures.py
```

The Python suite enforces 80% branch coverage. The current run is above that
threshold; the exact number is printed by the coverage command and recorded in
the CI log.

## Generated artifacts

`ghostnet.evaluation` writes `docs/evaluation.json` and `docs/evaluation.md`.
`site/scripts/export_fixtures.py` writes the site result card and the simulator
fixtures from the same Python rules. Both are deterministic; CI regenerates them
and fails if the working tree changes, so the site cannot drift from the backend.

## What is covered

| Area | Examples |
|---|---|
| Settings and secrets | Placeholder rejection, minimum length, fail-closed startup. |
| Privacy | Keyed hashes, user classes, credential summaries, canary handling. |
| Hash chain | Per-decoy chains, sequence continuity, tamper detection, checkpoints. |
| Store | Append under a transaction, window queries, proposals, panic state, purge. |
| Sessions and rules | Idle splitting, credential stuffing, canary follow-up, exploit paths, jitter boundary. |
| Actors and graph | Shared-source and shared-canary linking, graph nodes and edges. |
| Adaptation | Allowlist, parameter bounds, TTL, approve/reject, no deployment. |
| Exports | Navigator, STIX, CSV/JSONL, no fabricated indicators. |
| Ingest API | Auth, unknown decoys, rate limit, oversized body, server-owned fields. |
| Admin API | Auth, event/session detail, graph, heatmap, panic, WebSocket, metrics. |
| Decoys | Web login and body limits, SSH prompt, DB commands, panic poller. |
| Emitter | Queueing, keyed source, canary summarization, drop-on-full, delivery errors. |
| Edge proxy | Forwarding, upstream failure, no admin route. |
| Containment | Repository Compose passes; privileged, public and dual-homed variants fail. |
| Evaluation | Deterministic report, honest boundary miss, synthetic labelling. |

## Test layout

```
tests/
  conftest.py              secrets, app clients, event builders
  unit/                    pure logic, storage, policy, exports, evaluation
  integration/             FastAPI apps, decoy sockets, edge proxy
```

Integration tests use FastAPI `TestClient` and real loopback sockets. They do not
need Docker.

## Site checks

```bash
cd site
npm ci
npm run lint
npm run typecheck
npm test -- --run
npm run build
```

The site simulator has a Vitest suite and a parity fixture generated from the
Python implementation, so the browser explanation cannot silently drift from the
backend rules.

## CI

`.github/workflows/ci.yml` runs three jobs on every push to `main` and every pull
request:

1. **python** — lint, format check, mypy, coverage-gated tests, containment check,
   generated-report regeneration and a drift check.
2. **site** — npm ci, lint, typecheck, Vitest, production build.
3. **docker** — `docker compose config -q` and `docker compose build` with
   CI-only secrets.

`.github/workflows/site.yml` publishes the built site to GitHub Pages.
