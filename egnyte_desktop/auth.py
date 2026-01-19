# 2026 Jan Sechovec from Revolgy and Remangu
"""OAuth2 authentication for Egnyte API"""

import json
import time
import webbrowser
import http.server
import socketserver
import urllib.parse
import ssl
import subprocess
import shutil
import threading
from typing import Optional, Dict, Tuple
from pathlib import Path
import keyring
import requests
from .config import Config


class OAuthHandler:
    """Handles OAuth2 authentication flow"""
    
    def __init__(self, config: Config):
        """Bind auth handler to the current config."""
        self.config = config
        self.callback_server = None
        self.auth_code = None
    
    def get_authorization_url(self) -> str:
        """Generate authorization URL"""
        domain = self.config.get_domain()
        if not domain:
            raise ValueError("Domain not configured")
        
        client_id = self.config.get_client_id()
        if not client_id:
            raise ValueError("Client ID not configured")
        
        redirect_uri = self.config.get_redirect_uri()
        
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'Egnyte.filesystem Egnyte.user',
        }
        
        authorize_url = f"https://{domain}.egnyte.com/puboauth/authorize"
        url = f"{authorize_url}?{urllib.parse.urlencode(params)}"
        return url
    
    def _parse_redirect_uri(self, redirect_uri: str) -> Tuple[str, str, int, str]:
        """Parse redirect URI into components"""
        parsed = urllib.parse.urlparse(redirect_uri)
        scheme = parsed.scheme or "http"
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if scheme == "https" else 80)
        path = parsed.path or "/"
        return scheme, host, port, path
    
    def _is_localhost(self, host: str) -> bool:
        return host in {"localhost", "127.0.0.1", "::1"}
    
    def _ensure_localhost_cert(self, cert_path: Path, key_path: Path):
        """Generate a self-signed certificate for localhost if missing"""
        if cert_path.exists() and key_path.exists():
            return
        
        openssl = shutil.which("openssl")
        if not openssl:
            raise RuntimeError("OpenSSL is required to generate a local HTTPS certificate")
        
        cert_path.parent.mkdir(parents=True, exist_ok=True)
        
        base_cmd = [
            openssl,
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(key_path),
            "-out",
            str(cert_path),
            "-days",
            "365",
            "-subj",
            "/CN=localhost",
        ]
        
        # Try to include SAN for modern browsers; fall back if unsupported
        try:
            subprocess.run(
                base_cmd + ["-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            subprocess.run(
                base_cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    
    def start_callback_server(self, redirect_uri: str, timeout: int = 300):
        """Start local HTTP/HTTPS server to receive OAuth callback"""
        scheme, host, port, path = self._parse_redirect_uri(redirect_uri)
        
        if not self._is_localhost(host):
            raise RuntimeError("Callback server only supports localhost redirect URIs")
        
        class CallbackHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                
                if parsed.path != path:
                    self.send_response(404)
                    self.end_headers()
                    return
                
                params = urllib.parse.parse_qs(parsed.query)
                
                if 'code' in params:
                    self.server.auth_code = params['code'][0]
                    self.server.auth_event.set()
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"""
                    <html>
                    <body>
                    <h1>Authentication Successful!</h1>
                    <p>You can close this window and return to the application.</p>
                    </body>
                    </html>
                    """)
                else:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Error: No authorization code received")
            
            def log_message(self, format, *args):
                pass  # Suppress server logs
        
        class ReusableTCPServer(socketserver.TCPServer):
            allow_reuse_address = True
        
        httpd = ReusableTCPServer(("", port), CallbackHandler)
        httpd.auth_code = None
        httpd.auth_event = threading.Event()
        
        if scheme == "https":
            cert_dir = self.config.CONFIG_DIR / "certs"
            cert_path = cert_dir / "localhost.crt"
            key_path = cert_dir / "localhost.key"
            self._ensure_localhost_cert(cert_path, key_path)
            
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))
            httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        
        def serve():
            try:
                httpd.serve_forever(poll_interval=0.25)
            except Exception:
                pass
        
        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        
        if not httpd.auth_event.wait(timeout):
            httpd.shutdown()
            httpd.server_close()
            return None
        
        httpd.shutdown()
        httpd.server_close()
        return httpd.auth_code
    
    def authenticate(self, manual_code: Optional[str] = None, allow_manual_fallback: bool = True) -> Dict[str, str]:
        """Complete OAuth2 authentication flow
        
        Args:
            manual_code: Optional authorization code if manually entered
            allow_manual_fallback: Whether to prompt for manual code entry
        """
        redirect_uri = self.config.get_redirect_uri()
        
        if manual_code:
            return self.exchange_code_for_tokens(manual_code, redirect_uri_override=redirect_uri)
        
        auth_url = self.get_authorization_url()
        print("Opening browser for authentication...")
        print(f"If browser doesn't open, visit: {auth_url}")
        
        try:
            webbrowser.open(auth_url)
        except Exception:
            pass
        
        # Try automatic local callback when possible
        auth_code = None
        scheme, host, _, _ = self._parse_redirect_uri(redirect_uri)
        if self._is_localhost(host):
            try:
                if scheme == "https":
                    print("Waiting for secure local callback (https://localhost)...")
                    print("If you see a certificate warning, choose 'Advanced' and proceed.")
                else:
                    print("Waiting for local callback (http://localhost)...")
                
                auth_code = self.start_callback_server(redirect_uri)
                if auth_code:
                    return self.exchange_code_for_tokens(auth_code, redirect_uri_override=redirect_uri)
            except Exception as e:
                auth_code = None
                callback_error = str(e)
        
        if not allow_manual_fallback:
            if 'callback_error' in locals():
                raise Exception(f"Automatic callback failed: {callback_error}")
            raise Exception("Automatic callback failed or timed out")
        
        # Fall back to manual entry
        print("\n" + "="*60)
        print("Automatic callback failed or is unavailable.")
        if 'callback_error' in locals():
            print(f"Reason: {callback_error}")
        print("Please complete the authorization and paste the code below.")
        print("="*60)
        print("1. Complete authorization in the browser")
        print("2. After authorization, you'll see a page with a URL containing 'code=...'")
        print("3. Copy the code value from the URL")
        print("4. Paste it here (or run: egnyte-cli auth login --code YOUR_CODE)")
        print("="*60)
        
        print("\nEnter the authorization code from the URL (or press Ctrl+C to cancel):")
        auth_code = input("Code: ").strip()
        
        if not auth_code:
            raise Exception("Authentication failed: No authorization code provided")
        
        # Exchange code for tokens
        # Use the same redirect_uri that was used in the authorization request
        redirect_uri = self.config.get_redirect_uri()
        return self.exchange_code_for_tokens(auth_code, redirect_uri_override=redirect_uri)
    
    def exchange_code_for_tokens(self, auth_code: str, redirect_uri_override: Optional[str] = None) -> Dict[str, str]:
        """Exchange authorization code for access and refresh tokens
        
        Args:
            auth_code: Authorization code from OAuth flow
            redirect_uri_override: Optional redirect URI to use (must match authorization request)
        """
        domain = self.config.get_domain()
        client_id = self.config.get_client_id()
        client_secret = self.config.get_client_secret()
        redirect_uri = redirect_uri_override or self.config.get_redirect_uri()
        
        if not client_secret:
            raise ValueError("Client secret not configured. Please set it with: egnyte-cli config set client_secret YOUR_SECRET")
        
        token_url = f"https://{domain}.egnyte.com/puboauth/token"
        
        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'client_secret': client_secret,
        }
        
        response = requests.post(token_url, data=data)
        
        # Provide detailed error information
        if not response.ok:
            error_msg = f"Token exchange failed: {response.status_code} {response.reason}"
            try:
                error_data = response.json()
                if 'error' in error_data:
                    error_msg += f"\nError: {error_data.get('error')}"
                if 'error_description' in error_data:
                    error_msg += f"\nDescription: {error_data.get('error_description')}"
                if 'errorMessage' in error_data:
                    error_msg += f"\nError Message: {error_data.get('errorMessage')}"
                if 'formErrors' in error_data:
                    for form_error in error_data.get('formErrors', []):
                        error_msg += f"\n{form_error.get('code', '')}: {form_error.get('msg', '')}"
                # Show full response for debugging
                error_msg += f"\n\nFull response: {json.dumps(error_data, indent=2)}"
            except Exception as e:
                error_msg += f"\nResponse: {response.text[:500]}"
                error_msg += f"\n(Could not parse JSON: {e})"
            
            error_msg += f"\n\nTroubleshooting:"
            error_msg += f"\n- Ensure redirect_uri matches EXACTLY what's registered in Developer Portal"
            error_msg += f"\n- Current redirect_uri: {redirect_uri}"
            error_msg += f"\n- Authorization codes expire in ~1-2 minutes - use immediately"
            error_msg += f"\n- Check Developer Portal: https://developers.egnyte.com"
            error_msg += f"\n- Request details:"
            error_msg += f"\n  - Token URL: {token_url}"
            error_msg += f"\n  - Client ID: {client_id[:10]}..."
            error_msg += f"\n  - Redirect URI: {redirect_uri}"
            
            raise Exception(error_msg)
        
        tokens = response.json()
        
        # Store tokens securely
        self.save_tokens(tokens)
        
        return tokens
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """Refresh access token using refresh token"""
        domain = self.config.get_domain()
        client_id = self.config.get_client_id()
        client_secret = self.config.get_client_secret()
        
        if not client_secret:
            raise ValueError("Client secret not configured")
        
        token_url = f"https://{domain}.egnyte.com/puboauth/token"
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': client_id,
            'client_secret': client_secret,
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        
        tokens = response.json()
        self.save_tokens(tokens)
        
        return tokens
    
    def save_tokens(self, tokens: Dict[str, str]):
        """Save tokens securely using keyring"""
        # Store refresh token in keyring (more secure)
        keyring.set_password("egnyte-desktop", "refresh_token", tokens.get('refresh_token', ''))
        
        # Store access token and expiry in config (less sensitive, expires quickly)
        token_data = {
            'access_token': tokens.get('access_token'),
            'expires_in': tokens.get('expires_in'),
            'token_type': tokens.get('token_type', 'Bearer'),
            'issued_at': int(time.time()),
        }
        
        with open(self.config.TOKEN_FILE, 'w') as f:
            json.dump(token_data, f)

    def revoke_tokens(self):
        """Remove stored tokens locally"""
        try:
            keyring.delete_password("egnyte-desktop", "refresh_token")
        except Exception:
            pass
        
        try:
            if self.config.TOKEN_FILE.exists():
                self.config.TOKEN_FILE.unlink()
        except Exception:
            pass
    
    def load_tokens(self) -> Optional[Dict[str, str]]:
        """Load tokens from storage"""
        if not self.config.TOKEN_FILE.exists():
            return None
        
        try:
            with open(self.config.TOKEN_FILE, 'r') as f:
                token_data = json.load(f)
        except (json.JSONDecodeError, IOError, Exception):
            return None
        
        # Load refresh token from keyring if available, but don't fail if keyring isn't usable
        try:
            refresh_token = keyring.get_password("egnyte-desktop", "refresh_token")
            if refresh_token:
                token_data['refresh_token'] = refresh_token
        except Exception:
            pass
        
        return token_data
    
    def get_valid_access_token(self) -> Optional[str]:
        """Get a valid access token, refreshing if necessary"""
        tokens = self.load_tokens()
        if not tokens:
            return None
        
        # Check if token needs refresh (simplified - in production, check expiry)
        # For now, try to use existing token, refresh on 401
        
        return tokens.get('access_token')
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.get_valid_access_token() is not None

