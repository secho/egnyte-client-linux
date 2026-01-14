"""Utility functions"""

import os
from pathlib import Path
from typing import Optional


def format_file_size(size: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def ensure_dir(path: Path):
    """Ensure directory exists"""
    path.mkdir(parents=True, exist_ok=True)


def get_home_dir() -> Path:
    """Get user home directory"""
    return Path.home()


def get_config_dir() -> Path:
    """Get application config directory"""
    return Path.home() / ".config" / "egnyte-desktop"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for filesystem"""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def get_relative_path(base: Path, target: Path) -> Optional[str]:
    """Get relative path from base to target"""
    try:
        return str(target.relative_to(base))
    except ValueError:
        return None

