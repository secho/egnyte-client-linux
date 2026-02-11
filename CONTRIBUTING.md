## Contributing

Thanks for your interest in contributing to egnyte-cli.

### Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

### Run tests and lint

```bash
pytest tests/
ruff check .
```

### Pull requests

- Keep changes focused and scoped.
- Add or update tests where appropriate.
- Update documentation if behavior changes.
- Ensure `ruff` and `pytest` pass before submitting.

### Code style

- Follow existing conventions.
- Prefer small, readable functions.
- Avoid introducing new dependencies unless necessary.
