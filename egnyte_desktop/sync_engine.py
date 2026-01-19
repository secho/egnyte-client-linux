# 2026 Jan Sechovec from Revolgy and Remangu
"""File synchronization engine with bidirectional sync"""

import hashlib
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
import logging
from .api_client import EgnyteAPIClient
from .config import Config


logger = logging.getLogger(__name__)


class SyncEngine:
    """Handles bidirectional file synchronization"""
    
    def __init__(self, api_client: EgnyteAPIClient, config: Config):
        """Create a sync engine bound to config and API client."""
        self.api_client = api_client
        self.config = config
        self.sync_state_file = config.CONFIG_DIR / "sync_state.json"
        self.sync_state = self._load_sync_state()
    
    def _load_sync_state(self) -> Dict:
        """Load sync state (file hashes, timestamps)"""
        import json
        if self.sync_state_file.exists():
            try:
                with open(self.sync_state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}
    
    def _save_sync_state(self):
        """Save sync state"""
        import json
        with open(self.sync_state_file, 'w') as f:
            json.dump(self.sync_state, f, indent=2)
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (IOError, OSError):
            return ""
    
    def _get_local_file_info(self, local_path: Path) -> Optional[Dict]:
        """Get local file metadata"""
        if not local_path.exists():
            return None
        
        stat = local_path.stat()
        return {
            'path': str(local_path),
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'hash': self._get_file_hash(local_path) if local_path.is_file() else None,
            'is_dir': local_path.is_dir(),
        }
    
    def _get_remote_file_info(self, remote_path: str) -> Optional[Dict]:
        """Get remote file metadata"""
        try:
            info = self.api_client.get_file_info(remote_path)
            return {
                'path': remote_path,
                'size': info.get('size', 0),
                'modified': info.get('modified_time', ''),
                'hash': info.get('checksum'),
                'is_dir': info.get('is_folder', False),
            }
        except Exception as e:
            logger.debug(f"Error getting remote file info for {remote_path}: {e}")
            return None
    
    def _should_sync_file(self, local_path: Path, remote_path: str, policy: Optional[Dict] = None):
        """Determine if file needs syncing and in which direction
        Returns: (needs_sync, direction) where direction is 'up', 'down',
        'delete_local', 'delete_remote', or 'both'
        """
        local_info = self._get_local_file_info(local_path)
        remote_info = self._get_remote_file_info(remote_path)
        
        # Get last known state
        state_key = f"{local_path}:{remote_path}"
        last_state = self.sync_state.get(state_key, {})
        last_local_hash = last_state.get('local_hash')
        last_remote_hash = last_state.get('remote_hash')
        policy = policy or {}
        conflict_policy = policy.get('conflict_policy') or self.config.get_sync_conflict_policy()
        delete_local_on_remote_missing = (
            policy.get('delete_local_on_remote_missing')
            if policy.get('delete_local_on_remote_missing') is not None
            else self.config.get_delete_local_on_remote_missing()
        )
        delete_remote_on_local_missing = (
            policy.get('delete_remote_on_local_missing')
            if policy.get('delete_remote_on_local_missing') is not None
            else self.config.get_delete_remote_on_local_missing()
        )
        
        # File doesn't exist locally
        if not local_info:
            if remote_info:
                if delete_remote_on_local_missing and last_local_hash:
                    return (True, 'delete_remote')
                return (True, 'down')  # Download
            return (False, 'none')  # Both missing
        
        # File doesn't exist remotely
        if not remote_info:
            if delete_local_on_remote_missing and last_remote_hash:
                return (True, 'delete_local')
            if local_info and not local_info['is_dir']:
                return (True, 'up')  # Upload
            return (False, 'none')
        
        # Both exist - check for changes
        local_hash = local_info.get('hash')
        remote_hash = remote_info.get('hash')
        
        local_changed = local_hash != last_local_hash
        remote_changed = remote_hash != last_remote_hash
        
        if local_changed and remote_changed:
            # Conflict - both changed
            if conflict_policy == 'local':
                return (True, 'up')
            if conflict_policy == 'remote':
                return (True, 'down')
            
            # default: newest wins
            local_mtime = datetime.fromisoformat(local_info['modified'].replace('Z', '+00:00'))
            remote_mtime = datetime.fromisoformat(remote_info['modified'].replace('Z', '+00:00'))
            
            if local_mtime > remote_mtime:
                return (True, 'up')
            else:
                return (True, 'down')
        elif local_changed:
            return (True, 'up')
        elif remote_changed:
            return (True, 'down')
        
        return (False, 'none')
    
    def sync_file(self, local_path: Path, remote_path: str, policy: Optional[Dict] = None) -> Dict[str, any]:
        """Sync a single file"""
        result = {
            'local_path': str(local_path),
            'remote_path': remote_path,
            'action': 'none',
            'success': False,
            'error': None,
        }
        
        try:
            needs_sync, direction = self._should_sync_file(local_path, remote_path, policy=policy)
            
            if not needs_sync:
                result['action'] = 'skip'
                result['success'] = True
                return result
            
            if direction == 'up':
                # Upload local to remote
                if local_path.is_file():
                    self.api_client.upload_file(local_path, remote_path)
                    result['action'] = 'upload'
                elif local_path.is_dir():
                    self.api_client.create_folder(remote_path)
                    result['action'] = 'create_folder'
            
            elif direction == 'down':
                # Download remote to local
                remote_info = self._get_remote_file_info(remote_path)
                if remote_info and not remote_info['is_dir']:
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    self.api_client.download_file(remote_path, local_path)
                    result['action'] = 'download'
                elif remote_info and remote_info['is_dir']:
                    local_path.mkdir(parents=True, exist_ok=True)
                    result['action'] = 'create_folder'
            
            elif direction == 'delete_local':
                if local_path.exists():
                    if local_path.is_dir():
                        import shutil
                        shutil.rmtree(local_path, ignore_errors=True)
                    else:
                        local_path.unlink(missing_ok=True)
                result['action'] = 'delete_local'
            
            elif direction == 'delete_remote':
                self.api_client.delete_file(remote_path)
                result['action'] = 'delete_remote'
            
            # Update sync state
            local_info = self._get_local_file_info(local_path)
            remote_info = self._get_remote_file_info(remote_path)
            
            state_key = f"{local_path}:{remote_path}"
            self.sync_state[state_key] = {
                'local_hash': local_info.get('hash') if local_info else None,
                'remote_hash': remote_info.get('hash') if remote_info else None,
                'last_sync': datetime.now().isoformat(),
            }
            self._save_sync_state()
            
            result['success'] = True
            
        except Exception as e:
            logger.error(f"Error syncing {local_path} <-> {remote_path}: {e}")
            result['error'] = str(e)
        
        return result
    
    def sync_folder(self, local_path: Path, remote_path: str, recursive: bool = True, policy: Optional[Dict] = None) -> List[Dict]:
        """Sync a folder recursively"""
        results = []
        
        # Ensure local folder exists
        local_path.mkdir(parents=True, exist_ok=True)
        
        # Get remote folder contents
        try:
            remote_items = self.api_client.list_folder(remote_path)
        except Exception as e:
            logger.error(f"Error listing remote folder {remote_path}: {e}")
            remote_items = []
        
        # Create set of remote paths for comparison
        remote_paths = {item['path'] for item in remote_items}
        
        # Sync remote items
        for item in remote_items:
            item_remote_path = item['path']
            relative_path = item_remote_path.replace(remote_path.rstrip('/'), '').lstrip('/')
            item_local_path = local_path / relative_path
            
            if item.get('is_folder', False):
                if recursive:
                    # Recursively sync subfolder
                    sub_results = self.sync_folder(item_local_path, item_remote_path, recursive, policy=policy)
                    results.extend(sub_results)
                else:
                    # Just create folder
                    item_local_path.mkdir(parents=True, exist_ok=True)
            else:
                # Sync file
                result = self.sync_file(item_local_path, item_remote_path, policy=policy)
                results.append(result)
        
        # Check for local-only files (upload them)
        if recursive:
            for local_item in local_path.rglob('*'):
                if local_item.is_file():
                    relative_path = local_item.relative_to(local_path)
                    item_remote_path = f"{remote_path.rstrip('/')}/{str(relative_path).replace(os.sep, '/')}"
                    
                    # Check if already synced
                    if item_remote_path not in remote_paths:
                        result = self.sync_file(local_item, item_remote_path, policy=policy)
                        results.append(result)
        
        return results
    
    def sync_all(self) -> List[Dict]:
        """Sync all configured sync paths"""
        results = []
        sync_entries = self.config.get_sync_entries()
        
        for local_path_str, entry in sync_entries.items():
            local_path = Path(local_path_str)
            folder_results = self.sync_folder(local_path, entry.get('remote', ''), policy=entry.get('policy'))
            results.extend(folder_results)
        
        return results

