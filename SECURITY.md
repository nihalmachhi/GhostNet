# Security policy

GhostNet is a defensive deception lab and a learning project. It is not intended
for production or public-network deployment.

## Supported versions

`main` is the only supported branch.

## Reporting

Report a suspected vulnerability through a private GitHub security advisory if
available, or open a minimal issue that describes the affected component without
including secrets or exploit payloads. Do not include real credentials, personal
data or live target details.

## Scope

In scope:

- Container or network containment escapes in the supplied Compose layout.
- Authentication or authorization bypass in the admin or ingest API.
- Event integrity bypass in the hash chain or checkpoint logic.
- Privacy leaks of raw credentials or raw source addresses.
- Unsafe defaults that weaken the documented safety boundaries.

Out of scope:

- Running the decoys on a public interface.
- Kernel or Docker daemon exploits.
- Social engineering, denial of service against the host, or physical access.
- Detection-quality claims derived from the synthetic evaluation.
