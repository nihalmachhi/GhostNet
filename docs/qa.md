# Final QA

This is a point-in-time record, not a permanent guarantee. Re-run the commands
below on the commit you intend to show.

## Scope

- Date: 2026-11-05
- Branch: `main`
- Commit tested: `bc899ca` (`fix: quote compose tmpfs options so containers start`)
- Local environment: Windows, Python 3.13.7, Node.js 22.19.0, npm 10.9.3
- Fresh-clone environment: `uv` resolved CPython 3.12.12

## Local checks

| Check | Command | Result |
|---|---|---|
| Python lint | `uv run ruff check .` | pass |
| Python format | `uv run ruff format --check .` | pass, 93 files |
| Python types | `uv run mypy src` | pass, 56 files |
| Python tests | `uv run pytest -q --cov=ghostnet --cov-report=term-missing` | 84 passed |
| Coverage gate | same as above | 84.81% branch coverage (gate 80%) |
| Evaluation | `uv run python -m ghostnet.evaluation` | pass, 90.91% accuracy, 91.67% macro F1 |
| Fixture export | `uv run python site/scripts/export_fixtures.py` | pass, no content diff |
| Site lint | `npm run lint` | pass |
| Site types | `npm run typecheck` | pass |
| Site tests | `npm test -- --run` | 18 passed |
| Site build | `npm run build` | pass |
| Production audit | `npm audit --omit=dev` | 0 findings |
| Dev audit | `npm audit` | 7 moderate findings in lint tooling, no fix available |
| Container build | `docker compose build` | pass, six services |
| Container health | `docker compose up -d` | all healthchecks healthy |
| Decoy traffic | HTTP login, SSH-style login, DB query through edge | 7 events, 3 sessions |
| Admin API | `/fleet`, `/events`, `/integrity`, `/adapt/*`, `/panic` | pass |
| Runtime controls | `docker inspect` | uid 65534, read-only root, all caps dropped |

Re-running the evaluation and fixture exporter produced no content diff in
`docs/evaluation.json`, `docs/evaluation.md`, `site/src/data/results.generated.json`
or `site/src/features/simulator/__fixtures__/`. The generated numbers on the site
therefore match the committed report.

## Fresh-clone check

A clean clone of `origin/main` at `bc899ca` was created outside the working tree
and verified without reusing local build artifacts:

```bash
git clone --depth 1 https://github.com/nihalmachhi/GhostNet.git ghostnet-fresh
cd ghostnet-fresh
uv sync --frozen --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -q --cov=ghostnet --cov-fail-under=80
uv run python -m ghostnet.evaluation
git diff --exit-code -- docs/evaluation.json docs/evaluation.md
cd site
npm ci
npm run lint
npm run typecheck
npm test -- --run
npm run build
```

All steps passed. The clone was clean after the generated-report check, so the
committed artifacts reproduce from the committed source.

## Docker runtime verification

Docker Desktop's Linux engine was available on 2026-11-05, so the full stack was
built and started with CI-style secrets:

```bash
docker compose config -q
docker compose build
docker compose up -d
curl -H "X-Admin-Token: $GHOSTNET_ADMIN_TOKEN" http://127.0.0.1:8000/fleet
```

Results:

- All six services built. The admin and ingest APIs reached `healthy`; the decoys
  and edge stayed running.
- Unauthenticated `/fleet` returned `401`; the authenticated call reported three
  decoys and panic off.
- Scripted traffic through the edge produced events on all three decoys: an HTTP
  login, an SSH-style login and a DB query. The admin API reported 7 events and 3
  sessions, with only `src_hash` and hashed session IDs retained.
- `/integrity` verified all three per-decoy HMAC chains. `/adapt/propose` returned
  a TTL-bound action, approval recorded `deployed=false`, and a duplicate decision
  returned `409`. Panic and reset worked.
- A decoy container could not resolve `admin-api`, and `ghostnet_deception` is
  internal, so the admin API is not reachable from the deception network.
- `docker inspect` confirmed uid/gid `65534:65534`, a read-only root filesystem and
  `CapDrop=["ALL"]`.

The first live run exposed a real bug: the unquoted YAML flow sequence
`tmpfs: [/tmp:rw,noexec,nosuid,size=16m]` split the options on commas, so Docker
treated `size=16m` as a mount path. Quoting the value fixed every service, and
`tests/unit/test_packaging.py` now guards the compose file.

One environmental note: an unrelated local container already held host port
`5433`. Verification used a temporary override mapping only the host side to
`15433`; the committed mapping is unchanged and `docker compose config -q` passes.

CI still runs only `docker compose config -q` and `docker compose build`; it does
not start the stack. The runtime results above are a local point-in-time record.

## Known non-blocking findings

- The dev-only `npm audit` findings are transitive lint dependencies. The
  production dependency tree reports zero findings.
- The site has Vitest and a production build, not browser automation.
- The synthetic evaluation is a pipeline check, not a real-world detection score.
