.PHONY: install install-dev clean test run-gui run-cli

install:
	pip3 install -r requirements.txt
	pip3 install -e .

install-dev: install
	pip3 install pytest pytest-cov black flake8 mypy

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

test:
	pytest tests/

run-gui:
	python3 -m egnyte_desktop.gui.main

run-cli:
	python3 -m egnyte_desktop.cli.main

format:
	black egnyte_desktop/

lint:
	flake8 egnyte_desktop/
	mypy egnyte_desktop/

