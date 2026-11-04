# Final QA

This is a point-in-time record, not a permanent guarantee. Re-run the commands
below on the commit you intend to show.

## Scope

- Date: 2026-11-04
- Branch: `main`
- Commit tested: `bbc8938` (`feat(site): rebuild the portfolio site around GhostNet evidence`)
- Local environment: Windows, Python 3.13.7, Node.js 22.19.0, npm 10.9.3
- Fresh-clone environment: `uv` resolved CPython 3.12.12

## Local checks

| Check | Command | Result |
|---|---|---|
| Python lint | `uv run ruff check .` | pass |
| Python format | `uv run ruff format --check .` | pass, 91 files |
| Python types | `uv run mypy src` | pass, 56 files |
| Python tests | `uv run pytest -q --cov=ghostnet --cov-report=term-missing` | 83 passed |
| Coverage gate | same as above | 84.81% branch coverage (gate 80%) |
| Evaluation | `uv run python -m ghostnet.evaluation` | pass, 90.91% accuracy, 91.67% macro F1 |
| Fixture export | `uv run python site/scripts/export_fixtures.py` | pass, no content diff |
| Site lint | `npm run lint` | pass |
| Site types | `npm run typecheck` | pass |
| Site tests | `npm test -- --run` | 18 passed |
| Site build | `npm run build` | pass |
| Production audit | `npm audit --omit=dev` | 0 findings |
| Dev audit | `npm audit` | 7 moderate findings in lint tooling, no fix available |

Re-running the evaluation and fixture exporter produced no content diff in
`docs/evaluation.json`, `docs/evaluation.md`, `site/src/data/results.generated.json`
or `site/src/features/simulator/__fixtures__/`. The generated numbers on the site
therefore match the committed report.

## Fresh-clone check

A clean clone of `origin/main` at `bbc8938` was created outside the working tree
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

## Docker verification gap

Static configuration passed with CI-style secrets:

```bash
docker compose config -q
```

Image build and live container inspection could not run on this machine:

```text
error during connect: ... open //./pipe/dockerDesktopLinuxEngine:
The system cannot find the file specified.
```

Consequences:

- `docker compose build` and container startup are unverified locally.
- Runtime controls in `check_runtime` (non-root, read-only root, dropped
  capabilities, resource limits, internal decoy network) are covered by unit tests
  against fixture data, not by an inspection of live containers.
- CI runs `docker compose config -q` and `docker compose build`, but it does not
  start the stack or inspect live containers.
- Do not claim a live end-to-end container run until this is executed and recorded.

## Known non-blocking findings

- The dev-only `npm audit` findings are transitive lint dependencies. The
  production dependency tree reports zero findings.
- The site has Vitest and a production build, not browser automation.
- The synthetic evaluation is a pipeline check, not a real-world detection score.
