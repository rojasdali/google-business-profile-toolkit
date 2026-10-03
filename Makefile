.PHONY: test lint format install graph check

graph:
	python3 scripts/build_graph.py

check: lint test

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/
