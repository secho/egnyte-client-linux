"""Configuration management for Egnyte Desktop Client"""

import os
import json
from pathlib import Path
from typing import Dict, Optional


class Config:
    """Manages application configuration"""
    
    CONFIG_DIR = Path.home() / ".config" / "egnyte-desktop"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    TOKEN_FILE = CONFIG_DIR / "tokens.json"
    
    # Default API endpoints
    API_BASE_URL = "https://{domain}.egnyte.com"
    AUTH_URL = "https://{domain}.egnyte.com/puboauth/token"
    AUTHORIZE_URL = "https://{domain}.egnyte.com/puboauth/authorize"
    
    # Rate limiting (2 QPS default)
    RATE_LIMIT_QPS = 2
    RATE_LIMIT_DAILY = 1000
    
    def __init__(self):
        """Initialize configuration"""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from file"""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}
    
    def _save_config(self):
        """Save configuration to file"""
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump(self._config, f, indent=2)
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self._config.get(key, default)
    
    def set(self, key: str, value):
        """Set configuration value"""
        self._config[key] = value
        self._save_config()
    
    def get_domain(self) -> Optional[str]:
        """Get Egnyte domain"""
        return self.get('domain')
    
    def set_domain(self, domain: str):
        """Set Egnyte domain"""
        self.set('domain', domain)
    
    def get_client_id(self) -> Optional[str]:
        """Get OAuth client ID"""
        return self.get('client_id')
    
    def set_client_id(self, client_id: str):
        """Set OAuth client ID"""
        self.set('client_id', client_id)
    
    def get_client_secret(self) -> Optional[str]:
        """Get OAuth client secret"""
        return self.get('client_secret')
    
    def set_client_secret(self, client_secret: str):
        """Set OAuth client secret"""
        self.set('client_secret', client_secret)
    
    def get_redirect_uri(self) -> str:
        """Get OAuth redirect URI
        
        Note: Egnyte requires HTTPS redirect URIs. For localhost development,
        you may need to use a tool like ngrok or manually enter the auth code.
        """
        return self.get('redirect_uri', 'https://localhost:8080/callback')
    
    def set_redirect_uri(self, redirect_uri: str):
        """Set OAuth redirect URI"""
        self.set('redirect_uri', redirect_uri)
    
    def get_sync_paths(self) -> Dict[str, str]:
        """Get configured sync paths (local -> remote)"""
        return self.get('sync_paths', {})
    
    def add_sync_path(self, local_path: str, remote_path: str):
        """Add a sync path"""
        sync_paths = self.get_sync_paths()
        sync_paths[local_path] = remote_path
        self.set('sync_paths', sync_paths)
    
    def remove_sync_path(self, local_path: str):
        """Remove a sync path"""
        sync_paths = self.get_sync_paths()
        sync_paths.pop(local_path, None)
        self.set('sync_paths', sync_paths)

