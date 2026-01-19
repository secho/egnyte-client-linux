# 2026 Jan Sechovec from Revolgy and Remangu
"""Background sync service for Egnyte"""

import threading
import time
import logging
from pathlib import Path
from typing import Dict, Optional

from .auth import OAuthHandler
from .config import Config
from .api_client import EgnyteAPIClient
from .sync_engine import SyncEngine
from .file_watcher import FileWatcher

logger = logging.getLogger(__name__)


class EgnyteSyncService:
    """Runs background sync for local + remote changes"""

    def __init__(self, config: Config, remote_interval: int = 15):
        """Initialize a service instance with polling interval."""
        self.config = config
        self.remote_interval = remote_interval
        self.auth = OAuthHandler(config)
        self.api_client = EgnyteAPIClient(config, self.auth)
        self.sync_engine = SyncEngine(self.api_client, config)
        self.file_watcher = FileWatcher(self.sync_engine, config)
        self._stop_event = threading.Event()
        self._remote_state: Dict[str, Dict[str, str]] = {}
        self._remote_backoff_seconds = 0

    def start(self):
        """Start background sync"""
        if not self.auth.is_authenticated():
            raise RuntimeError("Not authenticated. Run 'egnyte-cli auth login' first.")

        logger.info("Starting local file watcher...")
        self.file_watcher.start()

        logger.info("Starting remote polling...")
        thread = threading.Thread(target=self._remote_poll_loop, daemon=True)
        thread.start()

        logger.info("Egnyte sync service running.")
        try:
            while not self._stop_event.is_set():
                time.sleep(1)
        finally:
            self.stop()

    def stop(self):
        """Stop background sync"""
        self._stop_event.set()
        self.file_watcher.stop()
        logger.info("Egnyte sync service stopped.")

    def _remote_poll_loop(self):
        """Poll remote state in a loop with backoff on errors."""
        while not self._stop_event.is_set():
            try:
                self._poll_remote_changes()
                self._remote_backoff_seconds = 0
            except Exception as e:
                logger.error(f"Remote polling error: {e}")
                if "429" in str(e):
                    if self._remote_backoff_seconds == 0:
                        self._remote_backoff_seconds = max(self.remote_interval, 30)
                    else:
                        self._remote_backoff_seconds = min(self._remote_backoff_seconds * 2, 300)
            time.sleep(self._remote_backoff_seconds or self.remote_interval)

    def _poll_remote_changes(self):
        """Compare remote state to previous snapshot and sync on changes."""
        sync_entries = self.config.get_sync_entries()
        if not sync_entries:
            return

        for local_path_str, entry in sync_entries.items():
            local_path = Path(local_path_str)
            if not local_path.exists():
                continue

            remote_path = entry.get('remote', '')
            policy = entry.get('policy', {})
            current_state = self._build_remote_state(remote_path)
            previous_state = self._remote_state.get(remote_path, {})

            if current_state != previous_state:
                logger.info(f"Remote changes detected in {remote_path}. Syncing...")
                self.sync_engine.sync_folder(local_path, remote_path, policy=policy)
                self._remote_state[remote_path] = current_state

    def _build_remote_state(self, remote_path: str) -> Dict[str, str]:
        """Return a flat map of remote paths to a simple fingerprint."""
        state: Dict[str, str] = {}

        def walk(path: str):
            items = self.api_client.list_folder(path)
            for item in items:
                item_path = item.get("path")
                if not item_path:
                    name = item.get("name", "")
                    base = path.rstrip("/") or "/"
                    item_path = f"{base}/{name}" if base != "/" else f"/{name}"

                modified = item.get("modified_time", "")
                size = str(item.get("size", 0))
                is_folder = str(bool(item.get("is_folder")))
                checksum = item.get("checksum", "")
                fingerprint = f"{modified}|{size}|{checksum}|{is_folder}"
                state[item_path] = fingerprint

                if item.get("is_folder"):
                    walk(item_path)

        walk(remote_path)
        return state
