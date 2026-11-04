install:
	uv sync --extra dev

test:
	uv run pytest -q

coverage:
	uv run pytest -q --cov=ghostnet --cov-report=term-missing

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy src

format:
	uv run ruff format src tests

containment:
	uv run python -m ghostnet.orchestrator.containment_check

evaluate:
	uv run python -m ghostnet.evaluation

fixtures:
	uv run python site/scripts/export_fixtures.py

generated: evaluate fixtures
	git diff --exit-code -- docs/evaluation.json docs/evaluation.md site/src/data/results.generated.json site/src/features/simulator/__fixtures__

site:
	cd site && npm ci && npm run lint && npm run typecheck && npm test -- --run && npm run build

verify: lint coverage containment generated site
