"""OAuth2 authentication for Egnyte API"""

import json
import webbrowser
import http.server
import socketserver
import urllib.parse
from typing import Optional, Dict
from pathlib import Path
import keyring
import requests
from .config import Config


class OAuthHandler:
    """Handles OAuth2 authentication flow"""
    
    def __init__(self, config: Config):
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
    
    def start_callback_server(self, port: int = 8080):
        """Start local HTTP server to receive OAuth callback"""
        class CallbackHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                params = urllib.parse.parse_qs(parsed.query)
                
                if 'code' in params:
                    self.server.auth_code = params['code'][0]
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
        
        handler = CallbackHandler
        handler.server = type('server', (), {})()
        
        with socketserver.TCPServer(("", port), handler) as httpd:
            httpd.auth_code = None
            httpd.timeout = 300  # 5 minutes timeout
            httpd.handle_request()
            return httpd.auth_code
    
    def authenticate(self, manual_code: Optional[str] = None) -> Dict[str, str]:
        """Complete OAuth2 authentication flow
        
        Args:
            manual_code: Optional authorization code if manually entered
        """
        redirect_uri = self.config.get_redirect_uri()
        
        # Check if using HTTPS redirect (required by Egnyte)
        if redirect_uri.startswith('https://'):
            # Use automatic callback server (if HTTPS is properly configured)
            auth_url = self.get_authorization_url()
            print(f"Opening browser for authentication...")
            print(f"If browser doesn't open, visit: {auth_url}")
            webbrowser.open(auth_url)
            
            # Try to start callback server (only works if HTTPS is properly set up)
            # For now, fall back to manual entry
            try:
                auth_code = self.start_callback_server()
                if auth_code:
                    return self.exchange_code_for_tokens(auth_code)
            except Exception:
                pass
            
            # Fall through to manual entry
            print("\n" + "="*60)
            print("IMPORTANT: Egnyte requires HTTPS for redirect URIs.")
            print("Please use one of these options:")
            print("="*60)
            print("\nOption 1: Manual Code Entry (Recommended)")
            print("1. Complete authorization in the browser")
            print("2. After authorization, you'll see an error page")
            print("3. Copy the 'code' parameter from the URL")
            print("4. Run: egnyte-cli auth login --code YOUR_CODE")
            print("\nOption 2: Use HTTPS Redirect URI")
            print("1. Set up an HTTPS redirect URI (e.g., using ngrok)")
            print("2. Update redirect URI in Developer Portal")
            print("3. Update config: egnyte-cli config set redirect_uri https://your-domain.com/callback")
            print("="*60)
            
            if manual_code:
                auth_code = manual_code
            else:
                # Prompt for manual code entry
                print("\nEnter the authorization code from the URL (or press Ctrl+C to cancel):")
                auth_code = input("Code: ").strip()
        else:
            # HTTP redirect - use manual entry flow
            auth_url = self.get_authorization_url()
            print(f"\n{'='*60}")
            print("Egnyte requires HTTPS redirect URIs.")
            print("Please follow these steps:")
            print(f"{'='*60}\n")
            print(f"1. Open this URL in your browser:")
            print(f"   {auth_url}\n")
            print("2. Log in and authorize the application")
            print("3. After authorization, you'll be redirected to an error page")
            print("4. Look at the URL - it will contain 'code=...' parameter")
            print("5. Copy the code value and run:")
            print("   egnyte-cli auth login --code YOUR_CODE\n")
            
            if manual_code:
                auth_code = manual_code
            else:
                print("Or enter the code now (press Ctrl+C to cancel):")
                auth_code = input("Authorization code: ").strip()
        
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
        }
        
        with open(self.config.TOKEN_FILE, 'w') as f:
            json.dump(token_data, f)
    
    def load_tokens(self) -> Optional[Dict[str, str]]:
        """Load tokens from storage"""
        if not self.config.TOKEN_FILE.exists():
            return None
        
        try:
            with open(self.config.TOKEN_FILE, 'r') as f:
                token_data = json.load(f)
            
            refresh_token = keyring.get_password("egnyte-desktop", "refresh_token")
            if refresh_token:
                token_data['refresh_token'] = refresh_token
            
            return token_data
        except (json.JSONDecodeError, IOError, Exception):
            return None
    
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

