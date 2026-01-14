"""FUSE filesystem mount for Egnyte"""

import os
import stat
import errno
import logging
from pathlib import Path
from typing import Dict, List

# Set FUSE Python API version via environment (must be done before importing fuse)
# Use API version 0.1 (0.2 has compatibility issues with fuse-python 1.0.9)
if 'FUSE_PYTHON_API' not in os.environ:
    os.environ['FUSE_PYTHON_API'] = '0.1'

# Try fusepy first (better API), fall back to fuse-python
USE_FUSEPY = False
try:
    from fusepy import FUSE, Operations, FuseOSError
    USE_FUSEPY = True
except ImportError:
    # Fall back to fuse-python
    try:
        import fuse
        # Set API version - use 0.1 for compatibility with fuse-python 1.0.9
        if 'FUSE_PYTHON_API' not in os.environ:
            os.environ['FUSE_PYTHON_API'] = '0.1'
        if not hasattr(fuse, 'fuse_python_api') or fuse.fuse_python_api is None:
            fuse.fuse_python_api = (0, 1)
        
        # Try to import Fuse (note: might be Fuse or FUSE depending on version)
        # fuse-python 1.0.9 has FUSE (uppercase) as a function, not a class
        if hasattr(fuse, 'Fuse'):
            from fuse import Fuse as FuseClass, FuseError
            FUSE_CLASS = FuseClass
        elif hasattr(fuse, 'FUSE'):
            # FUSE might be a function in some versions
            FUSE_CLASS = fuse.FUSE
            # Try to get FuseError
            try:
                from fuse import FuseError
            except ImportError:
                FuseError = Exception  # Fallback
        else:
            raise ImportError("fuse module doesn't have Fuse or FUSE")
        
        # Create alias for compatibility
        FUSE = FUSE_CLASS
        
        # Check for Operations base class
        try:
            from fuse.compat_0_1 import Operations
        except ImportError:
            # For newer fuse-python, Operations might not exist
            # We'll create our own base class
            class Operations:
                pass
        
        FuseOSError = FuseError  # Alias
    except ImportError as e:
        raise ImportError(f"Neither fusepy nor fuse-python working. Error: {e}. Install with: pip install fusepy")

from .api_client import EgnyteAPIClient
from .config import Config
from .auth import OAuthHandler

logger = logging.getLogger(__name__)


class EgnyteFuse(Operations):
    """FUSE filesystem implementation for Egnyte"""
    
    def __init__(self, api_client: EgnyteAPIClient):
        self.api_client = api_client
        self.fd = 0
        self.cache = {}  # Cache file contents
        self.file_attrs = {}  # Cache file attributes
    
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
        if path in self.file_attrs:
            return self.file_attrs[path]
        
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
            
            self.file_attrs[path] = attrs
            return attrs
        except Exception as e:
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
            if path == '/':
                items = self.api_client.list_folder('/')
            else:
                items = self.api_client.list_folder(path)
            
            # Build list (fuse-python expects list, not generator)
            entries = ['.', '..']
            for item in items:
                name = item.get('name', '')
                if name:  # Skip empty names
                    entries.append(name)
            
            return entries
        except Exception as e:
            logger.error(f"Error reading directory {path}: {e}")
            # Return at least . and .. on error
            return ['.', '..']
    
    def read(self, path: str, size: int, offset: int, fh):
        """Read file content"""
        try:
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
