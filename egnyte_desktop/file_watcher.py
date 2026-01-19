# 2026 Jan Sechovec from Revolgy and Remangu
"""File system watcher for automatic sync on local changes"""

import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from typing import Callable, Optional
from .sync_engine import SyncEngine


logger = logging.getLogger(__name__)


class SyncFileHandler(FileSystemEventHandler):
    """Handles file system events and triggers sync"""
    
    def __init__(self, sync_engine: SyncEngine, sync_entries: dict, debounce_seconds: float = 2.0):
        """Track changes for a set of local sync roots."""
        self.sync_engine = sync_engine
        self.sync_entries = sync_entries
        self.debounce_seconds = debounce_seconds
        self.pending_changes = {}  # path -> timestamp
        self.sync_callback: Optional[Callable] = None
    
    def set_sync_callback(self, callback: Callable):
        """Set callback to be called when sync is triggered"""
        self.sync_callback = callback
    
    def _get_remote_path(self, local_path: Path) -> Optional[tuple]:
        """Get remote path and policy for a local path"""
        local_str = str(local_path)
        
        # Find matching sync path
        for sync_local, entry in self.sync_entries.items():
            sync_local_path = Path(sync_local)
            try:
                relative = local_path.relative_to(sync_local_path)
                # Convert to forward slashes for remote path
                relative_str = str(relative).replace('\\', '/')
                remote_base = entry.get('remote', '') if isinstance(entry, dict) else entry
                remote_path = f"{remote_base.rstrip('/')}/{relative_str}"
                policy = entry.get('policy', {}) if isinstance(entry, dict) else {}
                return remote_path.replace('//', '/'), policy
            except ValueError:
                # local_path is not relative to sync_local_path
                continue
        
        return None
    
    def _schedule_sync(self, local_path: Path):
        """Schedule a sync operation with debouncing"""
        remote_tuple = self._get_remote_path(local_path)
        if not remote_tuple:
            return
        remote_path, policy = remote_tuple
        
        # Debounce: only sync if no changes for debounce_seconds
        now = time.time()
        key = str(local_path)
        
        self.pending_changes[key] = now
        
        # Schedule sync after debounce period
        def delayed_sync():
            time.sleep(self.debounce_seconds)
            if self.pending_changes.get(key) == now:
                # No newer changes, proceed with sync
                try:
                    if local_path.exists():
                        if local_path.is_file():
                            result = self.sync_engine.sync_file(local_path, remote_path, policy=policy)
                            logger.info(f"Auto-synced {local_path}: {result['action']}")
                        elif local_path.is_dir():
                            # For directories, sync the folder
                            self.sync_engine.sync_folder(local_path, remote_path, recursive=False, policy=policy)
                            logger.info(f"Auto-synced folder {local_path}")
                    
                    if self.sync_callback:
                        self.sync_callback(local_path, remote_path)
                except Exception as e:
                    logger.error(f"Error in auto-sync for {local_path}: {e}")
        
        import threading
        thread = threading.Thread(target=delayed_sync, daemon=True)
        thread.start()
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification"""
        if event.is_directory:
            return
        
        local_path = Path(event.src_path)
        self._schedule_sync(local_path)
    
    def on_created(self, event: FileSystemEvent):
        """Handle file creation"""
        local_path = Path(event.src_path)
        self._schedule_sync(local_path)
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion"""
        # Note: We don't delete remote files automatically for safety
        # This can be configured if needed
        logger.debug(f"Local file deleted: {event.src_path} (not syncing deletion)")
    
    def on_moved(self, event: FileSystemEvent):
        """Handle file move/rename"""
        if event.is_directory:
            return
        
        # Treat as delete + create
        dest_path = Path(event.dest_path)
        self._schedule_sync(dest_path)


class FileWatcher:
    """Watches file system for changes and triggers sync"""
    
    def __init__(self, sync_engine: SyncEngine, config):
        """Initialize watcher with config-driven paths."""
        self.sync_engine = sync_engine
        self.config = config
        self.observer = Observer()
        self.handlers = []
        self.running = False
    
    def start(self, sync_callback: Optional[Callable] = None):
        """Start watching configured sync paths"""
        sync_entries = self.config.get_sync_entries()
        
        for local_path_str, entry in sync_entries.items():
            local_path = Path(local_path_str)
            if not local_path.exists():
                logger.warning(f"Sync path does not exist: {local_path}")
                continue
            
            handler = SyncFileHandler(self.sync_engine, {local_path_str: entry})
            if sync_callback:
                handler.set_sync_callback(sync_callback)
            
            self.observer.schedule(handler, str(local_path), recursive=True)
            self.handlers.append(handler)
        
        self.observer.start()
        self.running = True
        logger.info("File watcher started")
    
    def stop(self):
        """Stop watching"""
        if self.running:
            self.observer.stop()
            self.observer.join()
            self.running = False
            logger.info("File watcher stopped")
    
    def is_running(self) -> bool:
        """Check if watcher is running"""
        return self.running

