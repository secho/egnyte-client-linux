#!/usr/bin/env python3
# 2026 Jan Sechovec from Revolgy and Remangu
"""Test script to debug token exchange"""

import sys
import requests
import json
from egnyte_desktop.config import Config

if len(sys.argv) < 2:
    print("Usage: python3 test_token_exchange.py <authorization_code>")
    sys.exit(1)

auth_code = sys.argv[1]
config = Config()

domain = config.get_domain()
client_id = config.get_client_id()
redirect_uri = config.get_redirect_uri()

token_url = f"https://{domain}.egnyte.com/puboauth/token"

data = {
    'grant_type': 'authorization_code',
    'code': auth_code,
    'redirect_uri': redirect_uri,
    'client_id': client_id,
}

print("=" * 60)
print("Token Exchange Debug")
print("=" * 60)
print(f"\nToken URL: {token_url}")
print(f"\nRequest Data:")
for key, value in data.items():
    if key == 'code':
        print(f"  {key}: {value[:10]}... (length: {len(value)})")
    elif key == 'client_id':
        print(f"  {key}: {value[:20]}... (length: {len(value)})")
    else:
        print(f"  {key}: {value}")

print(f"\nSending request...")
response = requests.post(token_url, data=data)

print(f"\nResponse Status: {response.status_code}")
print(f"Response Headers:")
for key, value in response.headers.items():
    print(f"  {key}: {value}")

print(f"\nResponse Body:")
try:
    error_data = response.json()
    print(json.dumps(error_data, indent=2))
except:
    print(response.text)

if not response.ok:
    print("\n" + "=" * 60)
    print("ERROR - Token exchange failed!")
    print("=" * 60)
    print("\nPlease check:")
    print(f"1. Redirect URI in config: {redirect_uri}")
    print("2. Redirect URI in Developer Portal (must match exactly)")
    print("3. Code is fresh (used within 1-2 minutes)")
    print("4. Code hasn't been used before (single-use)")
else:
    print("\n" + "=" * 60)
    print("SUCCESS - Token exchange worked!")
    print("=" * 60)

