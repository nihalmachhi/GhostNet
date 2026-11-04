# Privacy

GhostNet is designed to observe behavior, not to collect secrets. All data in the
repository and in the generated evaluation is synthetic.

## Captured

| Field | Treatment |
|---|---|
| Source address | HMAC-SHA256 with `GHOSTNET_HASH_KEY`, truncated to 24 hex characters, prefixed `h:`. |
| Source and destination port | Integer, clamped to `0..65535`. |
| Decoy id and type | Fixed identifiers from the deployment. |
| Timestamp | Server-generated UTC ISO-8601. |
| Event kind | Coarse category such as `auth_attempt`, `command`, `http_request`. |
| Username | Keyed hash (20 chars), length and coarse class (`admin`, `default`, `other`). |
| Password | Keyed hash (20 chars), length and coarse category (`common_wordlist`, `other`). |
| HTTP path | Stored for rule matching. Query strings are not parsed into separate fields. |
| Command | First token, uppercased, capped at 80 characters by the Cowrie adapter. |
| User agent | First 120 characters on the web decoy. |
| Canary token | Only an exact configured canary gets a `canary_id` (keyed hash, 12 chars). Everything else is hashed. |

## Never captured

- Raw passwords or raw usernames.
- Raw source addresses in stored events.
- Request bodies beyond the fields above.
- Packet payloads, TLS material or files.
- Outbound connection data: decoys never connect back to a client.

## Keys

Four independent secrets are required at startup:

- `GHOSTNET_HASH_KEY` hashes sources, usernames, passwords and tokens.
- `GHOSTNET_CHAIN_KEY` HMACs the event chain.
- `GHOSTNET_INGEST_SECRET` derives per-decoy ingest tokens.
- `GHOSTNET_ADMIN_TOKEN` authenticates analyst requests.

Each must be at least 16 characters and must not be a documented placeholder.
Rotating the hash key creates a new, unlinkable pseudonym set. Rotating the chain
key invalidates existing chain verification, so export a checkpoint first.

## Retention

`GHOSTNET_RETENTION_DAYS` defaults to 30. `ghostnet purge` deletes events older
than the window. Purging truncates history: old checkpoints no longer describe
the retained chain, so export a new checkpoint after a purge.

## Limits

- Hashed identifiers are pseudonymous. With the hash key, an operator can test a
  guessed address; without it, they cannot reverse the digest.
- The same key produces stable identifiers, so events can be linked over time.
- Shared NAT addresses can merge distinct people. The session builder documents
  this rather than pretending the link is identity.
- Canary tokens are intentionally recognizable to the decoy; only their keyed
  identifier is stored.
