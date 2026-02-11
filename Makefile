.PHONY: install install-dev clean test lint format build

install:
	pip3 install -e .

install-dev:
	pip3 install -e ".[dev]"

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

test:
	pytest tests/ -v

lint:
	ruff check egnyte_desktop/ tests/

format:
	ruff format egnyte_desktop/ tests/

build:
	python3 -m build

