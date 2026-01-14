# Quick Fix: OAuth HTTPS Redirect Error

## The Error

When running `egnyte-cli auth login`, you see:
```
{"formErrors":[{"code":"INVALID_CALLBACK","msg":"Invalid redirect uri redirect uri must be a valid https url."}]
```

## Quick Solution (Manual Code Entry)

1. **Run the command**:
   ```bash
   egnyte-cli auth login
   ```

2. **Copy the authorization URL** that's displayed

3. **Open it in your browser** and complete the login

4. **After authorization**, you'll see an error page, but the URL will contain:
   ```
   http://localhost:8080/callback?code=AUTHORIZATION_CODE_HERE&...
   ```

5. **Copy the code** (the value after `code=`)

6. **Run again with the code**:
   ```bash
   egnyte-cli auth login --code AUTHORIZATION_CODE_HERE
   ```

   Or if you're in the interactive prompt, just paste the code when asked.

## Example

```bash
$ egnyte-cli auth login

Starting authentication...
============================================================
Egnyte requires HTTPS redirect URIs.
Please follow these steps:
============================================================

1. Open this URL in your browser:
   https://yourdomain.egnyte.com/puboauth/authorize?client_id=...

2. Log in and authorize the application
3. After authorization, you'll be redirected to an error page
4. Look at the URL - it will contain 'code=...' parameter
5. Copy the code value and run:
   egnyte-cli auth login --code YOUR_CODE

Or enter the code now (press Ctrl+C to cancel):
Authorization code: [PASTE CODE HERE]
Authentication successful!
```

## Why This Happens

Egnyte requires HTTPS redirect URIs for security. For localhost development, HTTP is typically used, which causes this error. The manual code entry method works around this limitation.

## Alternative: Use HTTPS (ngrok)

For automated authentication, you can use ngrok:

1. Install ngrok: `sudo snap install ngrok`
2. Start tunnel: `ngrok http 8080`
3. Update Developer Portal redirect URI to your ngrok HTTPS URL
4. Update config: `egnyte-cli config set redirect_uri https://your-ngrok-url.ngrok.io/callback`
5. Run: `egnyte-cli auth login`

See [OAUTH_SETUP.md](OAUTH_SETUP.md) for more details.

