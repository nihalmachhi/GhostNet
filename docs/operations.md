# Operations

## Requirements

- Python 3.11 or newer (CI uses 3.12; the local lockfile was tested with 3.13).
- [uv](https://docs.astral.sh/uv/).
- Docker with Compose v2 for the contained stack.
- Node.js 22 for the site and tests.

## First run

```bash
uv sync --extra dev
cp .env.example .env
```

Generate four independent secrets and put them in `.env`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Run it four times. Every secret must be at least 16 characters and must not be a
placeholder from `.env.example`. Startup fails closed otherwise.

## Start the contained stack

```bash
uv run python -m ghostnet.orchestrator.lifecycle up
```

`lifecycle up` first runs the static Compose containment checks. If they fail, it
refuses to start. After `docker compose up --build -d`, it waits briefly and runs
runtime checks against the live containers. If a runtime check fails, it stops
the stack and exits non-zero.

Published loopback ports:

| Decoy | Address |
|---|---|
| Web admin | `127.0.0.1:8081` |
| SSH-like | `127.0.0.1:2222` |
| DB-like | `127.0.0.1:5433` |
| Admin API | `127.0.0.1:8000` |

The ingest API is not published. Decoys cannot reach the admin API.

## Generate synthetic activity

```bash
uv run python testactors/local_demo.py
```

This scripted actor is harmless and local. It is not an offensive tool.

## Stop

```bash
uv run python -m ghostnet.orchestrator.lifecycle down
```

## Panic switch

```bash
curl -X POST -H "X-Admin-Token: $GHOSTNET_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"confirmation":"STOP GHOSTNET"}' \
  http://127.0.0.1:8000/panic
```

Decoys poll the authenticated kill switch through the ingest API and exit. After
a panic stop, reset with `{"confirmation":"RESET GHOSTNET"}` and restart the
Compose stack.

## Exports

```bash
uv run ghostnet export-checkpoint --out checkpoint.json
uv run ghostnet export-navigator --out navigator.json
uv run ghostnet export-stix --out stix.json
uv run ghostnet export-csv --out sessions.csv
uv run ghostnet purge --database data/ghostnet.sqlite3
```

Exports use the same derived sessions as the API. STIX output contains attack
patterns and observed-data objects, not fabricated indicators from hashed
addresses.

## Metrics

`GET /metrics` (admin token required) returns:

```text
ghostnet_events_total <n>
ghostnet_panic <0|1>
```

Scrape it from a loopback-only Prometheus if you want history. GhostNet does not
ship a monitoring stack.

## Evaluation

```bash
uv run python -m ghostnet.evaluation
```

This rewrites `docs/evaluation.json` and `docs/evaluation.md` from deterministic
synthetic fixtures. It also re-runs the static containment check.

## Troubleshooting

| Symptom | Check |
|---|---|
| Startup says secrets are missing | `.env` exists, values are at least 16 chars and not placeholders. |
| `lifecycle up` refuses | Run `uv run python -m ghostnet.orchestrator.containment_check` and fix the listed control. |
| Containment reports `docker_runtime_unavailable` | The Docker daemon is not running. Static checks still work. |
| No events appear | Decoys emit to `ingest-api`; confirm the decoy token and that the ingest container is healthy. |
| `401` from the admin API | Send `X-Admin-Token` with the exact configured value. |
| `410` from `/adapt/approve` | The proposal TTL expired; request a new proposal. |
| Site cannot reach the API | The site is a static showcase. Point your own client at loopback `:8000`. |

## Local verification note

On the development machine used for this pass, Docker Desktop's Linux engine was
not running, so `docker compose build` and runtime container inspection could not
be executed. Static `docker compose config -q` and `check_compose_config` passed.
CI runs `docker compose config -q` and `docker compose build` on GitHub Actions.
