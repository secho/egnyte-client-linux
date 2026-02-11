# OAuth Setup

Egnyte uses OAuth 2.0. This project supports:

- Authorization Code flow (default)
- Resource Owner Password Credentials flow (internal apps only)

## Developer Portal Setup

1. Create or sign in to your developer account: https://developers.egnyte.com
2. Create a new app:
   - App Type: Publicly Available Application (for public distribution)
   - API Product: Connect
   - Scopes: `Egnyte.filesystem` and `Egnyte.user`
3. Set the Redirect URI (see options below).
4. Save the Client ID and Client Secret. Keep them private.

## Authorization Code Flow (default)

### Option 1: Manual Code Entry (simplest)

```bash
egnyte-cli auth login
```

Steps:
1. The CLI prints an authorization URL.
2. Open the URL in a browser and authorize the app.
3. The browser will redirect to the callback URL.
4. Copy the `code=` value from the URL.
5. Paste it into the CLI prompt, or run:
   ```bash
   egnyte-cli auth login --code YOUR_CODE
   ```

Notes:
- Authorization codes expire quickly (1-2 minutes).
- The redirect URI used in the token exchange must match your Developer Portal setting.

### Option 2: Local HTTPS Callback (self-signed)

1. Set redirect URI to:
   ```bash
   egnyte-cli config set redirect_uri https://localhost:8080/callback
   ```
2. Run:
   ```bash
   egnyte-cli auth login
   ```
3. Accept the browser's self-signed certificate warning.

The CLI will start a local HTTPS server and capture the code automatically.

### Option 3: ngrok (HTTPS tunnel)

1. Start ngrok:
   ```bash
   ngrok http 8080
   ```
2. Set Developer Portal redirect URI to the ngrok HTTPS URL:
   ```
   https://<your-subdomain>.ngrok.io/callback
   ```
3. Update CLI config:
   ```bash
   egnyte-cli config set redirect_uri https://<your-subdomain>.ngrok.io/callback
   ```
4. Run:
   ```bash
   egnyte-cli auth login
   ```

## Resource Owner Password Flow (internal apps only)

For internal application keys only:

```bash
egnyte-cli auth login --password-flow --username USERNAME
```

Egnyte will not enable this flow for public application keys.

## Troubleshooting

### INVALID_CALLBACK / HTTPS required
- Egnyte requires HTTPS redirect URIs.
- Use ngrok or the local HTTPS callback option.

### redirect_uri_mismatch
- Ensure the Redirect URI in Developer Portal matches your CLI config exactly.

### 400 Bad Request on token exchange
- The authorization code is expired or already used.
- Get a new code and use it immediately.

### 401 Unauthorized
- Access token expired or revoked.
- Re-authenticate with `egnyte-cli auth login`.

### 429 Too Many Requests
- Egnyte rate limits apply (2 QPS and 1000 daily by default).
- Retry later or request higher limits after certification.

## Security Notes

- Never commit Client ID/Secret or tokens to source control.
- Tokens are stored in the system keyring when available.
- Config and token files are restricted to user-only (0600).
