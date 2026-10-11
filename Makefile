install:
	uv sync --extra dev
test:
	uv run pytest
lint:
	uv run ruff check .
format:
	uv run ruff format ghostnet tests
containment:
	uv run python -m ghostnet.orchestrator.containment_check
