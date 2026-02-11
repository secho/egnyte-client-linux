# AGENTS.md

Guidance for AI coding assistants working on egnyte-cli.

## Project Overview

**egnyte-cli** is a Python CLI for Egnyte on Linux. It provides OAuth authentication, bidirectional sync, file operations (ls, upload, download), and optional FUSE mounting.

- **Package name:** `egnyte-cli`
- **Python package:** `egnyte_desktop`
- **Entry point:** `egnyte-cli` → `egnyte_desktop.cli.main:main`
- **Python:** 3.8+

## Directory Structure

```
egnyte_desktop/     # Main package
├── cli/            # Click CLI (main.py)
├── api_client.py   # Egnyte REST API, rate limiting, retries
├── auth.py         # OAuth2 flows
├── config.py       # Config storage (~/.config/egnyte-desktop/)
├── file_watcher.py # Watchdog-based file monitoring
├── fuse_mount.py   # FUSE filesystem
├── sync_engine.py  # Sync logic and conflict policies
├── sync_service.py # Sync orchestration
└── utils.py        # Helpers
tests/              # pytest tests
docs/               # OAuth setup, development
examples/           # systemd service example
```

## Development Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Optional: `sudo apt-get install fuse libfuse-dev gnome-keyring libsecret-1-0` for FUSE and keyring.

## Commands

| Task | Command |
|------|---------|
| Run tests | `pytest tests/` or `make test` |
| Lint | `ruff check egnyte_desktop/ tests/` or `make lint` |
| Format | `ruff format egnyte_desktop/ tests/` or `make format` |
| Build | `python -m build` or `make build` |

CI runs `pytest tests/` and `ruff check .` on push/PR.

## Code Conventions

- **Style:** Ruff for linting and formatting. No black/flake8.
- **Tests:** pytest. Add/update tests when changing behavior.
- **Dependencies:** Avoid new deps unless necessary; prefer stdlib or existing packages.
- **Structure:** Small, readable functions; follow existing patterns.
- **CLI:** Click. Use `click.echo` / `click.secho` for output; helpers like `_info`, `_error`, `_hint` in main.py.

## Key Patterns

- **Config:** `Config()` from `config.py`; stored under `~/.config/egnyte-desktop/`.
- **Auth:** `OAuthHandler` + `EgnyteAPIClient`; token storage via keyring.
- **API:** Rate-limited with retry/backoff; handle 429 responses.
- **Sync:** `SyncEngine` with conflict policies (`newer_wins`, `local_wins`, etc.).

## Documentation

- [docs/oauth-setup.md](docs/oauth-setup.md) — OAuth setup
- [docs/development.md](docs/development.md) — Development setup
- [CONTRIBUTING.md](CONTRIBUTING.md) — PR guidelines
- [SECURITY.md](SECURITY.md) — Security / vulnerability reporting

## Testing Tips

- Tests use pytest; fixtures and mocks where needed.
- Run `pytest tests/ -v` for verbose output.
- Ensure tests and `ruff check` pass before submitting.
