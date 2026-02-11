# Development Setup

## Prerequisites

- Linux (Ubuntu/Debian recommended)
- Python 3.8+
- Git

## Clone and install

```bash
git clone https://github.com/secho/egnyte-cli.git
cd egnyte-cli
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Optional system dependencies

FUSE mount support:
```bash
sudo apt-get update
sudo apt-get install -y fuse libfuse-dev
```

Keyring backend (recommended):
```bash
sudo apt-get install -y gnome-keyring libsecret-1-0
```

## Run tests and lint

```bash
pytest tests/
ruff check .
```

## Run from source

```bash
egnyte-cli --help
```

## Build distributions

```bash
python -m build
```
