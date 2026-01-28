# 2026 Jan Sechovec from Revolgy and Remangu
"""CLI auth status tests."""

from datetime import datetime, timezone

from click.testing import CliRunner

import egnyte_desktop.cli.main as cli_main


class DummyAuth:
    def __init__(self, config):
        self.config = config

    def is_authenticated(self):
        return True

    def load_tokens(self):
        return {"issued_at": 1700000000, "expires_in": 3600}


class DummyConfig:
    def __init__(self):
        pass


def test_auth_status_shows_user(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(cli_main, "OAuthHandler", DummyAuth)
    monkeypatch.setattr(cli_main, "Config", DummyConfig)

    def fake_get_user_info(self):
        return {"username": "alice@example.com"}

    monkeypatch.setattr(cli_main.EgnyteAPIClient, "get_user_info", fake_get_user_info)

    result = runner.invoke(cli_main.cli, ["auth", "status"])
    assert result.exit_code == 0
    assert "alice@example.com" in result.output
