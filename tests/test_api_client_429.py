# 2026 Jan Sechovec from Revolgy and Remangu
"""API client rate limit retry tests."""

import time

from egnyte_desktop.api_client import EgnyteAPIClient


class DummyAuth:
    def get_valid_access_token(self):
        return "token"

    def load_tokens(self):
        return {}


class DummyConfig:
    RATE_LIMIT_QPS = 100

    def get_domain(self):
        return "example"


class FakeResponse:
    def __init__(self, status_code, headers=None, payload=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._payload = payload or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


def test_request_retries_on_429(monkeypatch):
    client = EgnyteAPIClient(DummyConfig(), DummyAuth())
    calls = {"count": 0}

    def fake_request(method, url, headers=None, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            return FakeResponse(429)
        return FakeResponse(200, payload={"ok": True})

    sleeps = []

    def fake_sleep(seconds):
        sleeps.append(seconds)

    monkeypatch.setattr(client.session, "request", fake_request)
    monkeypatch.setattr(time, "sleep", fake_sleep)

    resp = client._request("GET", "/pubapi/v1/fs/")
    assert resp.json()["ok"] is True
    assert calls["count"] == 2
    assert sleeps
