# 2026 Jan Sechovec from Revolgy and Remangu
"""Sync engine policy tests."""

from pathlib import Path

from egnyte_desktop.sync_engine import SyncEngine


class DummyConfig:
    def __init__(self, tmp_path):
        self.CONFIG_DIR = tmp_path

    def get_sync_conflict_policy(self):
        return "newest"

    def get_delete_local_on_remote_missing(self):
        return False

    def get_delete_remote_on_local_missing(self):
        return False

    def get_sync_entries(self):
        return {}


class DummyApiClient:
    def __init__(self):
        self.deleted = []

    def get_file_info(self, path):
        raise Exception("404")

    def delete_file(self, path):
        self.deleted.append(path)


def test_delete_local_on_remote_missing(tmp_path):
    local_file = tmp_path / "file.txt"
    local_file.write_text("hello")

    api = DummyApiClient()
    cfg = DummyConfig(tmp_path)
    engine = SyncEngine(api, cfg)
    engine.sync_state[f"{local_file}:/remote/file.txt"] = {
        "local_hash": "old",
        "remote_hash": "was-here",
    }

    result = engine.sync_file(
        local_file,
        "/remote/file.txt",
        policy={"delete_local_on_remote_missing": True},
    )

    assert result["action"] == "delete_local"
    assert not local_file.exists()


def test_conflict_policy_local(tmp_path):
    local_file = tmp_path / "file.txt"
    local_file.write_text("v1")

    class ConflictApi(DummyApiClient):
        def get_file_info(self, path):
            return {
                "size": 2,
                "modified_time": "2030-01-01T00:00:00Z",
                "checksum": "remote-hash",
                "is_folder": False,
            }

    api = ConflictApi()
    cfg = DummyConfig(tmp_path)
    engine = SyncEngine(api, cfg)
    engine.sync_state[f"{local_file}:/remote/file.txt"] = {
        "local_hash": "old-local",
        "remote_hash": "old-remote",
    }

    needs_sync, direction = engine._should_sync_file(
        local_file, "/remote/file.txt", policy={"conflict_policy": "local"}
    )

    assert needs_sync is True
    assert direction == "up"
