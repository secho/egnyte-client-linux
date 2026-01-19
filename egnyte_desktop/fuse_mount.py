# 2026 Jan Sechovec from Revolgy and Remangu
"""FUSE filesystem mount for Egnyte"""

import os
import stat
import errno
import logging
import time
import sys
import os
from pathlib import Path
from typing import Dict, List

# Set FUSE Python API version via environment (must be done before importing fuse)
# Use API version 0.1 (0.2 has compatibility issues with fuse-python 1.0.9)
if 'FUSE_PYTHON_API' not in os.environ:
    os.environ['FUSE_PYTHON_API'] = '0.1'

# Prefer fusepy only; fuse-python is unstable for our use-case
USE_FUSEPY = False
try:
    from fuse import FUSE, Operations, FuseOSError
    USE_FUSEPY = True
except ImportError as e:
    raise ImportError(f"fusepy is required. Install with: pip install fusepy. Error: {e}")

from .api_client import EgnyteAPIClient
from .config import Config
from .auth import OAuthHandler

logger = logging.getLogger(__name__)
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format='%(message)s')


class EgnyteFuse(Operations):
    """FUSE filesystem implementation for Egnyte"""
    
    def __init__(self, api_client: EgnyteAPIClient):
        """Keep caches and API client for FUSE callbacks."""
        self.api_client = api_client
        self.fd = 0
        self.cache = {}  # Cache file contents
        self.file_attrs = {}  # path -> (attrs, ts)
        self.dir_entries = {}  # path -> (entries, ts)
        self.attr_cache_ttl = 5
        self.dir_cache_ttl = 5
        self._ignored_names = {'.Trash', '.Trash-1000', '.xdg-volume-info', 'autorun.inf', 'System Volume Information'}
        self._rate_limit_fatal = False

    def _abort_on_rate_limit(self, error: Exception):
        """Stop the mount immediately on 429 to avoid request storms."""
        if "429" in str(error):
            if not self._rate_limit_fatal:
                self._rate_limit_fatal = True
                logger.error("Egnyte rate limit reached (HTTP 429).")
                logger.error("Aborting mount to avoid request storms. Please retry later or lower request rate.")
            os._exit(1)
    
    def __call__(self, operation: str, *args, **kwargs):
        """Make the object callable for fuse-python API compatibility"""
        # fuse-python might try to call operations('getattr', path, fh)
        # but we have methods, so route to the appropriate method
        if hasattr(self, operation):
            method = getattr(self, operation)
            return method(*args, **kwargs)
        raise AttributeError(f"Operation {operation} not supported")
    
    def getattr(self, path: str, fh=None):
        """Get file attributes"""
        basename = os.path.basename(path)
        if basename in self._ignored_names:
            raise FuseOSError(errno.ENOENT)
        
        cached = self.file_attrs.get(path)
        if cached:
            attrs, ts = cached
            if time.monotonic() - ts < self.attr_cache_ttl:
                return attrs
        
        try:
            if path == '/':
                # Root directory
                attrs = {
                    'st_mode': stat.S_IFDIR | 0o755,
                    'st_nlink': 2,
                    'st_size': 4096,
                    'st_ctime': 0,
                    'st_mtime': 0,
                    'st_atime': 0,
                }
            else:
                info = self.api_client.get_file_info(path)
                if info.get('is_folder', False):
                    attrs = {
                        'st_mode': stat.S_IFDIR | 0o755,
                        'st_nlink': 2,
                        'st_size': 4096,
                        'st_ctime': 0,
                        'st_mtime': 0,
                        'st_atime': 0,
                    }
                else:
                    attrs = {
                        'st_mode': stat.S_IFREG | 0o644,
                        'st_nlink': 1,
                        'st_size': info.get('size', 0),
                        'st_ctime': 0,
                        'st_mtime': 0,
                        'st_atime': 0,
                    }
            
            self.file_attrs[path] = (attrs, time.monotonic())
            return attrs
        except Exception as e:
            self._abort_on_rate_limit(e)
            # Log only if it's not a 404 (file not found is expected for special files)
            if '404' not in str(e):
                logger.debug(f"Error getting attributes for {path}: {e}")
            # Return ENOENT (No such file or directory) for missing files
            raise FuseOSError(errno.ENOENT)
    
    def readdir(self, path: str, fh):
        """Read directory contents
        
        Note: For fuse-python, this should return a list, not a generator
        """
        try:
            cached = self.dir_entries.get(path)
            if cached:
                entries, ts = cached
                if time.monotonic() - ts < self.dir_cache_ttl:
                    return entries

            if path == '/':
                items = self.api_client.list_folder('/')
            else:
                items = self.api_client.list_folder(path)
            
            # Build list (fuse-python expects list, not generator)
            entries = ['.', '..']
            for item in items:
                name = item.get('name', '')
                if not name or name in self._ignored_names:
                    continue
                entries.append(name)
            
            self.dir_entries[path] = (entries, time.monotonic())
            return entries
        except Exception as e:
            self._abort_on_rate_limit(e)
            logger.error(f"Error reading directory {path}: {e}")
            # Return at least . and .. on error
            return ['.', '..']

    def _is_egnyte_path(self, path: str) -> bool:
        """Return True for valid Egnyte paths we want to handle."""
        # Only allow Egnyte namespace paths, ignore other special files
        if not path.startswith('/'):
            return False
        # Prevent calls like /.Trash or /.xdg-volume-info
        basename = os.path.basename(path)
        if basename in self._ignored_names:
            return False
        return True
    
    def read(self, path: str, size: int, offset: int, fh):
        """Read file content"""
        try:
            if not self._is_egnyte_path(path):
                raise FuseOSError(errno.ENOENT)
            # Check cache first
            if path in self.cache:
                data = self.cache[path]
            else:
                # Download file
                data = self.api_client.download_file(path)
                self.cache[path] = data
            
            # Return requested slice
            return data[offset:offset + size]
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            raise FuseError(errno.EIO)
    
    def write(self, path: str, data: bytes, offset: int, fh):
        """Write file content"""
        try:
            if not self._is_egnyte_path(path):
                raise FuseOSError(errno.ENOENT)
            # For simplicity, we'll upload the entire file after write
            # In a production system, you'd want to handle partial writes better
            # For now, we'll just cache the write and upload on release
            if path not in self.cache:
                self.cache[path] = b''
            
            # Extend cache if needed
            current_size = len(self.cache[path])
            if offset + len(data) > current_size:
                self.cache[path] = self.cache[path].ljust(offset) + data
            else:
                # Replace at offset
                self.cache[path] = self.cache[path][:offset] + data + self.cache[path][offset + len(data):]
            
            return len(data)
        except Exception as e:
            logger.error(f"Error writing file {path}: {e}")
            raise FuseError(errno.EIO)
    
    def create(self, path: str, mode, fi=None):
        """Create a new file"""
        try:
            if not self._is_egnyte_path(path):
                raise FuseOSError(errno.ENOENT)
            # Create empty file in cache
            self.cache[path] = b''
            self.file_attrs[path] = {
                'st_mode': stat.S_IFREG | 0o644,
                'st_nlink': 1,
                'st_size': 0,
                'st_ctime': 0,
                'st_mtime': 0,
                'st_atime': 0,
            }
            return 0
        except Exception as e:
            logger.error(f"Error creating file {path}: {e}")
            raise FuseError(errno.EIO)
    
    def mkdir(self, path: str, mode):
        """Create a directory"""
        try:
            if not self._is_egnyte_path(path):
                raise FuseOSError(errno.ENOENT)
            self.api_client.create_folder(path)
            self.file_attrs[path] = {
                'st_mode': stat.S_IFDIR | 0o755,
                'st_nlink': 2,
                'st_size': 4096,
                'st_ctime': 0,
                'st_mtime': 0,
                'st_atime': 0,
            }
        except Exception as e:
            logger.error(f"Error creating directory {path}: {e}")
            raise FuseError(errno.EIO)
    
    def unlink(self, path: str):
        """Delete a file"""
        try:
            if not self._is_egnyte_path(path):
                raise FuseOSError(errno.ENOENT)
            self.api_client.delete_file(path)
            if path in self.cache:
                del self.cache[path]
            if path in self.file_attrs:
                del self.file_attrs[path]
        except Exception as e:
            logger.error(f"Error deleting file {path}: {e}")
            raise FuseError(errno.EIO)
    
    def rmdir(self, path: str):
        """Remove a directory"""
        try:
            if not self._is_egnyte_path(path):
                raise FuseOSError(errno.ENOENT)
            self.api_client.delete_file(path)
            if path in self.file_attrs:
                del self.file_attrs[path]
        except Exception as e:
            logger.error(f"Error removing directory {path}: {e}")
            raise FuseError(errno.EIO)
    
    def release(self, path: str, fh):
        """Release file handle - upload if file was modified"""
        try:
            if path in self.cache:
                # Upload the file
                from pathlib import Path
                import tempfile
                
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp.write(self.cache[path])
                    tmp_path = Path(tmp.name)
                
                try:
                    self.api_client.upload_file(tmp_path, path, overwrite=True)
                finally:
                    tmp_path.unlink()
                
                # Clear cache
                del self.cache[path]
        except Exception as e:
            logger.error(f"Error releasing file {path}: {e}")
        
        return 0
    
    def flush(self, path: str, fh):
        """Flush file - upload immediately"""
        if path in self.cache:
            self.release(path, fh)
        return 0


def mount_egnyte(mount_point: str, config: Config, api_client: EgnyteAPIClient, foreground: bool = False):
    """Mount Egnyte as a FUSE filesystem"""
    mount_path = Path(mount_point)
    
    if not mount_path.exists():
        mount_path.mkdir(parents=True, exist_ok=True)
    
    if not mount_path.is_dir():
        raise ValueError(f"Mount point must be a directory: {mount_point}")
    
    fuse_ops = EgnyteFuse(api_client)
    
    if USE_FUSEPY:
        # Use fusepy (simpler API)
        FUSE(
            fuse_ops,
            str(mount_path),
            foreground=foreground,
            nothreads=True,
            fsname="egnyte",
            subtype="egnyte",
            allow_other=False,
        )
    else:
        # Use fuse-python (has compatibility issues, but we'll try)
        # For fuse-python, FUSE might be a function that takes (ops, mountpoint, ...)
        import sys
        
        # Save original argv
        original_argv = list(sys.argv)
        try:
            # Set up argv for Fuse (it expects: program_name [options] mountpoint)
            new_argv = ['egnyte-cli']
            if foreground:
                new_argv.append('-f')
            new_argv.append(str(mount_path))
            
            # Replace sys.argv
            sys.argv[:] = new_argv
            
            # For fuse-python, FUSE requires (operations, mountpoint)
            # Even though it has bugs, we'll try to work around them
            fuse_instance = FUSE(fuse_ops, str(mount_path), foreground=foreground, nothreads=True)
            # The constructor should start the mount automatically
        except Exception as e:
            logger.error(f"FUSE mount error: {e}", exc_info=True)
            logger.error("Consider installing fusepy for better compatibility: pip install fusepy")
            raise
        finally:
            # Restore original argv
            sys.argv[:] = original_argv
