# Threat model

## Assets

- The host and its Docker daemon.
- The event store: integrity, confidentiality and availability.
- The four secrets: hash key, chain key, ingest secret and admin token.
- The analyst's interpretation of labels and ATT&CK mappings.

## Adversaries

| Adversary | Capability assumed |
|---|---|
| Lab actor | Can connect to published decoy ports and send arbitrary bytes. |
| Compromised decoy | Knows its own ingest token and can emit events for itself. |
| Local unprivileged user | Can read repository files but not the Docker socket or `.env`. |
| Database writer | Can modify the SQLite file directly. |
| Curious operator | Can read the dashboard, exports and metrics. |

GhostNet does **not** model a host root compromise, a Docker daemon compromise,
a kernel container escape, or a targeted attacker with code execution in the
admin API. Those are out of scope for a local learning lab.

## Trust boundaries

1. **Actor → edge proxy.** Untrusted bytes. The proxy forwards only three fixed
   routes and applies connection and idle limits.
2. **Decoy → ingest API.** Authenticated per decoy with an HMAC token. One
   compromised decoy cannot impersonate another.
3. **Ingest API → event store.** The ingest app owns event shape and integrity
   fields. Rate and body limits bound resource use.
4. **Admin API → analyst.** Every route requires the admin token. The admin API
   is attached only to `control` and published on loopback.
5. **Store → exports.** Exports contain hashed sources and behavioral labels,
   never raw credentials or raw addresses.

## Mitigations

| Risk | Mitigation |
|---|---|
| Decoy becomes a foothold | Inert handlers; no shell, no SQL engine, no outbound client connections. |
| Lateral movement from a decoy | `deception` network is `internal: true`; only the edge proxy is dual-homed. |
| Host compromise via container | Non-root user, `cap_drop: ALL`, `no-new-privileges`, read-only root, tmpfs, pid/memory/CPU limits, no host mounts, no Docker socket. |
| Public exposure | All published ports bind `127.0.0.1`. The containment checker rejects anything else. |
| Credential collection | Passwords are reduced to length and a keyed hash before storage. |
| Event tampering | Per-decoy HMAC chain and signed checkpoint. |
| Unbounded input | 8 KiB body limit, 4 KiB event data limit, bounded line reads, connection semaphore. |
| Runaway response | Actions are allowlisted and parameter-bounded; approval never deploys. |
| Accidental operation | Panic switch requires `STOP GHOSTNET`; reset requires `RESET GHOSTNET`. |

## Residual risk

- A database writer can rewrite a whole chain. The HMAC key and exported
  checkpoints make casual edits detectable, not impossible.
- The admin token is a single shared secret. There is no user directory, MFA or
  per-analyst audit identity.
- Hashed source addresses are stable for a given hash key. They are
  pseudonymous, not anonymous, and can be linked across sessions.
- Shared NAT addresses can merge unrelated people into one actor.
- Low-interaction decoys observe only what the emulated protocol exposes.
- Labels are ordered heuristics with scores, not calibrated probabilities.
- Containment is checked at configuration and container level, not against a
  kernel exploit.
