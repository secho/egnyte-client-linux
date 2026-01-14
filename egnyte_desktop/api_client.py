"""Egnyte API client with rate limiting and efficient operations"""

import time
import json
import requests
from typing import Optional, Dict, List, BinaryIO
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque
from .config import Config
from .auth import OAuthHandler


class RateLimiter:
    """Rate limiter for API calls (2 QPS default)"""
    
    def __init__(self, qps: float = 2.0):
        self.qps = qps
        self.min_interval = 1.0 / qps
        self.last_call_time = 0
        self.call_times = deque(maxlen=100)  # Track recent calls
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limit"""
        now = time.time()
        elapsed = now - self.last_call_time
        
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)
        
        self.last_call_time = time.time()
        self.call_times.append(self.last_call_time)


class EgnyteAPIClient:
    """Client for Egnyte API with rate limiting"""
    
    def __init__(self, config: Config, auth: OAuthHandler):
        self.config = config
        self.auth = auth
        self.rate_limiter = RateLimiter(config.RATE_LIMIT_QPS)
        self.domain = config.get_domain()
        self.base_url = f"https://{self.domain}.egnyte.com"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        token = self.auth.get_valid_access_token()
        if not token:
            raise Exception("Not authenticated. Please run 'egnyte-cli auth login'")
        
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }
    
    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make API request with rate limiting and error handling"""
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        headers.update(kwargs.pop('headers', {}))
        
        response = requests.request(method, url, headers=headers, **kwargs)
        
        # Handle token refresh on 401
        if response.status_code == 401:
            tokens = self.auth.load_tokens()
            if tokens and 'refresh_token' in tokens:
                self.auth.refresh_access_token(tokens['refresh_token'])
                # Retry once
                headers = self._get_headers()
                headers.update(kwargs.pop('headers', {}))
                response = requests.request(method, url, headers=headers, **kwargs)
            else:
                raise Exception("Authentication expired. Please run 'egnyte-cli auth login'")
        
        response.raise_for_status()
        return response
    
    def list_folder(self, path: str = "/") -> List[Dict]:
        """List contents of a folder"""
        endpoint = f"/pubapi/v1/fs{path}"
        response = self._request('GET', endpoint)
        data = response.json()
        return data.get('folders', []) + data.get('files', [])
    
    def get_file_info(self, path: str) -> Dict:
        """Get file metadata"""
        endpoint = f"/pubapi/v1/fs{path}"
        response = self._request('GET', endpoint)
        return response.json()
    
    def download_file(self, remote_path: str, local_path: Optional[Path] = None) -> bytes:
        """Download a file"""
        endpoint = f"/pubapi/v1/fs-content{remote_path}"
        response = self._request('GET', endpoint, stream=True)
        
        content = response.content
        if local_path:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(content)
        
        return content
    
    def upload_file(self, local_path: Path, remote_path: str, 
                   overwrite: bool = True, create_folders: bool = True) -> Dict:
        """Upload a file
        
        Args:
            local_path: Local file path
            remote_path: Remote path including filename (e.g., /Shared/file.txt)
            overwrite: Whether to overwrite existing file
            create_folders: Whether to create parent folders if they don't exist
        """
        # Ensure remote_path includes the filename
        if remote_path.endswith('/'):
            # If remote_path is a directory, append the local filename
            remote_path = remote_path.rstrip('/') + '/' + local_path.name
        
        # Handle Shared folder restrictions - must upload to subfolder
        if remote_path.startswith('/Shared/') and remote_path.count('/') == 2:
            # Trying to upload directly to /Shared/ - not allowed
            # Default to /Shared/Documents/
            remote_path = '/Shared/Documents/' + local_path.name
            if create_folders:
                # Ensure Documents folder exists
                try:
                    self.create_folder('/Shared/Documents')
                except:
                    pass  # Folder might already exist
        
        # Create parent folders if needed
        if create_folders:
            parent_path = '/'.join(remote_path.split('/')[:-1])
            if parent_path and parent_path != '/':
                try:
                    # Try to create the folder (might already exist)
                    self.create_folder(parent_path)
                except:
                    pass  # Folder might already exist
        
        endpoint = f"/pubapi/v1/fs-content{remote_path}"
        
        headers = {'Content-Type': 'application/octet-stream'}
        if not overwrite:
            headers['If-None-Match'] = '*'
        
        try:
            with open(local_path, 'rb') as f:
                # Try POST first
                response = self._request('POST', endpoint, 
                                       data=f, 
                                       headers=headers)
            
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                # Conflict - file exists, try PUT for overwrite
                if overwrite:
                    try:
                        with open(local_path, 'rb') as f:
                            # Use PUT method to overwrite existing file
                            response = self._request('PUT', endpoint,
                                                   data=f,
                                                   headers=headers)
                        return response.json()
                    except requests.exceptions.HTTPError as put_error:
                        # PUT also failed, show original error
                        pass
                
                # Conflict - file exists and we can't overwrite
                error_msg = f"Upload failed: Conflict (409) - File already exists"
                try:
                    error_data = e.response.json()
                    if 'errorMessage' in error_data:
                        error_msg += f"\n{error_data.get('errorMessage')}"
                    if 'error' in error_data:
                        error_msg += f"\nError: {error_data.get('error')}"
                    # Show full response for debugging
                    error_msg += f"\n\nFull response: {json.dumps(error_data, indent=2)}"
                except:
                    error_msg += f"\nResponse: {e.response.text[:200]}"
                
                error_msg += f"\n\nSolutions:"
                error_msg += f"\n1. Delete existing file first (if delete command available)"
                error_msg += f"\n2. Upload to a different path/name"
                error_msg += f"\n3. Check if file exists: egnyte-cli ls {remote_path}"
                
                raise Exception(error_msg) from e
            raise
    
    def create_folder(self, path: str) -> Dict:
        """Create a folder"""
        endpoint = f"/pubapi/v1/fs{path}"
        response = self._request('POST', endpoint, json={})
        return response.json()
    
    def delete_file(self, path: str) -> Dict:
        """Delete a file or folder"""
        endpoint = f"/pubapi/v1/fs{path}"
        response = self._request('DELETE', endpoint)
        return response.json() if response.content else {}
    
    def move_file(self, source_path: str, destination_path: str) -> Dict:
        """Move or rename a file/folder"""
        endpoint = f"/pubapi/v1/fs{source_path}"
        data = {'action': 'move', 'destination': destination_path}
        response = self._request('POST', endpoint, json=data)
        return response.json()
    
    def copy_file(self, source_path: str, destination_path: str) -> Dict:
        """Copy a file/folder"""
        endpoint = f"/pubapi/v1/fs{source_path}"
        data = {'action': 'copy', 'destination': destination_path}
        response = self._request('POST', endpoint, json=data)
        return response.json()
    
    def get_file_checksum(self, path: str) -> Optional[str]:
        """Get file checksum (MD5)"""
        try:
            info = self.get_file_info(path)
            return info.get('checksum')
        except Exception:
            return None
    
    def search(self, query: str, folder: str = "/") -> List[Dict]:
        """Search for files and folders"""
        endpoint = f"/pubapi/v1/search"
        params = {'query': query, 'folder': folder}
        response = self._request('GET', endpoint, params=params)
        return response.json().get('results', [])

