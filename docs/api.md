# API

Two FastAPI apps are exposed. They share a SQLite database and a secret set, but
they are separate processes and separate trust boundaries.

## Admin API

Published at `http://127.0.0.1:8000` in Compose. Every route except `/health`
requires `X-Admin-Token`.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness only. |
| `GET` | `/fleet` | Configured decoys, event count, panic state, containment summary. |
| `GET` | `/events?limit=100&after=0` | Retained events in insertion order. |
| `GET` | `/events/{event_id}` | One event. |
| `GET` | `/sessions?class_label=&decoy=` | Derived sessions with labels and ATT&CK rows. |
| `GET` | `/sessions/{session_id}` | Session plus the exact events in its window. |
| `GET` | `/actors` | Linked actors and evidence edges. |
| `GET` | `/graph?actor=` | Actor/session/decoy/canary graph. |
| `GET` | `/attack/heatmap` | Tactic counts over derived sessions. |
| `GET` | `/adapt/propose` | Pick one allowlisted proposal and persist it with a TTL. |
| `POST` | `/adapt/approve` | Record an analyst decision. Never deploys. |
| `GET` | `/panic` | Current panic state. |
| `POST` | `/panic` | Requires `{"confirmation":"STOP GHOSTNET"}`. |
| `POST` | `/admin/panic/reset` | Requires `{"confirmation":"RESET GHOSTNET"}`. |
| `GET` | `/integrity` | Verify every chain and return a checkpoint. |
| `GET` | `/checkpoint` | Signed head hash and count per decoy. |
| `GET` | `/metrics` | Prometheus text gauges for events and panic. |
| `WS` | `/live?token=...&after=0` | Event stream with heartbeats and panic close. |

### Examples

```bash
curl -H "X-Admin-Token: $GHOSTNET_ADMIN_TOKEN" http://127.0.0.1:8000/fleet
curl -H "X-Admin-Token: $GHOSTNET_ADMIN_TOKEN" http://127.0.0.1:8000/sessions
curl -H "X-Admin-Token: $GHOSTNET_ADMIN_TOKEN" http://127.0.0.1:8000/checkpoint
curl -X POST -H "X-Admin-Token: $GHOSTNET_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action_id":"...","approve":true}' \
  http://127.0.0.1:8000/adapt/approve
```

`/adapt/propose` returns `policy_approved` and `requires_analyst_approval`, and
stores the proposal for `GHOSTNET_PROPOSAL_TTL_SECONDS` (default 300). Approving
an unknown, decided or expired proposal returns `404`, `409` or `410`.

## Ingest API

Reachable only on the internal `deception` network at `http://ingest-api:8002`.
No docs, OpenAPI or redoc routes are enabled.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness only. |
| `GET` | `/panic/{decoy_id}` | Authenticated kill-switch poll for one decoy. |
| `POST` | `/events` | Append one event. |

Authentication uses `X-Decoy-Token`, derived as:

```text
HMAC-SHA256(GHOSTNET_INGEST_SECRET, decoy_id)
```

The accepted decoy ids are `web-admin-01`, `fake-ssh-01` and `fake-db-01`.
Requests are limited to 600 per decoy per rolling minute and 8 KiB declared or
actual body size.

### Event shape

```json
{
  "decoy_id": "web-admin-01",
  "decoy_type": "web-admin",
  "session_id": "h:...:web-admin-01",
  "src_hash": "h:0123456789abcdef01234567",
  "src_port": 44444,
  "dst_port": 8081,
  "proto": "tcp",
  "kind": "auth_attempt",
  "data": {"user_len": 4, "password_len": 8, "category": "other"}
}
```

Unknown fields are rejected. The server assigns `event_id`, `ts`, `seq`,
`prev_hash` and `hash`. `data` is limited to 4 KiB.

## Error behaviour

- Missing or wrong admin token: `401`.
- Missing or wrong decoy token, or unknown decoy id: `401`.
- Oversized ingest body: `413`.
- Ingest rate limit: `429`.
- Unknown event, session or proposal: `404`.
- Proposal already decided: `409`.
- Proposal expired: `410`.
- Panic confirmation mismatch: `400`.
