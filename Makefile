.PHONY: install test lint format

install:
	uv sync --locked

test:
	uv run --locked ruff check .
	uv run --locked ruff format --check .
	uv run --locked pytest

lint:
	uv run --locked ruff check .
	uv run --locked ruff format --check .

format:
	uv run --locked ruff check --fix .
	uv run --locked ruff format .
