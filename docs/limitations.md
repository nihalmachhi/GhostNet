# Limitations

GhostNet is a portfolio-scale learning lab. The following limits are intentional
and should be stated whenever the project is described.

## Detection

- Labels come from ordered YAML heuristics. They are hypotheses with an explicit
  rule id, score and evidence, not calibrated probabilities.
- ATT&CK mappings are tactic and technique level. They do not establish intent,
  attribution or campaign membership.
- The synthetic evaluation is built from hand-written fixtures. It verifies that
  the pipeline behaves as designed; it is not a benchmark against real traffic.
- The rule set is small. A patient actor who stays below thresholds can look like
  `benign_noise`.
- Jittered command timing intentionally falls outside the low-variance scripted
  rule; the generated evaluation reports that miss instead of hiding it.

## Interaction

- Decoys are low interaction. They do not run a real shell, a real SSH daemon, a
  real SQL engine or a real web application framework surface.
- The SSH-like and DB-like services exchange a handful of lines and close.
- The web decoy records a small set of fields and always rejects login.
- There is no malware capture, file upload, PCAP capture or payload analysis.

## Identity

- Source addresses are keyed hashes. They are pseudonymous and stable for a given
  key, not anonymous.
- Shared NAT addresses can merge unrelated sessions into one actor.
- There is one shared admin token. There is no user directory, MFA or per-analyst
  audit identity.

## Integrity

- A database writer can rewrite an entire chain. HMACs and exported checkpoints
  make casual edits detectable, not impossible.
- Purging old events truncates the chain; export a new checkpoint afterwards.

## Deployment

- The project is not production ready and must not be exposed on a public
  interface.
- All published ports bind loopback. The containment checker rejects anything
  else.
- There is no TLS because the services are loopback-only. Do not add a remote
  listener without adding transport security and a real identity model.
- The site is a static showcase, not a live analyst console.

## Verification gaps

- On the development machine for this pass, Docker Desktop's Linux engine was not
  running. `docker compose config -q` and the static containment checks passed,
  but `docker compose build`, container startup and live runtime inspection were
  not executed locally. CI validates the Compose config and builds the images; it
  does not run a live container smoke test. Treat container runtime behavior as
  unverified until that check is added or the stack is run locally.
- The site is tested with Vitest and a production build, not with a browser
  automation suite.
- `npm audit` reports moderate findings in development-only lint tooling. The
  production dependency tree reports zero findings, and the affected packages
  have no non-breaking fix at the time of this pass.
