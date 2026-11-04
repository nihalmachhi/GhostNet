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

site:
	cd site && npm ci && npm run lint && npm run typecheck && npm test -- --run && npm run build

verify: lint coverage containment evaluate site
