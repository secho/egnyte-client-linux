# 2026 Jan Sechovec from Revolgy and Remangu
"""Config sync entry behavior tests."""

from pathlib import Path

from egnyte_desktop.config import Config


def _patch_config_paths(tmp_path):
    Config.CONFIG_DIR = tmp_path / "config"
    Config.CONFIG_FILE = Config.CONFIG_DIR / "config.json"
    Config.TOKEN_FILE = Config.CONFIG_DIR / "tokens.json"


def test_sync_entries_roundtrip(tmp_path):
    _patch_config_paths(tmp_path)
    cfg = Config()

    cfg.add_sync_path("/local", "/remote")
    cfg.set_sync_path_policy("/local", {"conflict_policy": "remote"})

    entries = cfg.get_sync_entries()
    assert entries["/local"]["remote"] == "/remote"
    assert entries["/local"]["policy"]["conflict_policy"] == "remote"


def test_sync_entries_backward_compat(tmp_path):
    _patch_config_paths(tmp_path)
    cfg = Config()

    cfg.set("sync_paths", {"/local": "/remote"})

    entries = cfg.get_sync_entries()
    assert entries["/local"]["remote"] == "/remote"
    assert entries["/local"]["policy"] == {}
