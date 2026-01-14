# OAuth Token Exchange Troubleshooting

## Error: 400 Bad Request during token exchange

If you see `400 Client Error: Bad Request` when running `egnyte-cli auth login --code YOUR_CODE`, here are the most common causes and solutions:

## Common Causes

### 1. Redirect URI Mismatch

**Problem**: The redirect URI used in the token exchange doesn't match what's registered in the Egnyte Developer Portal.

**Solution**:
1. Check your Developer Portal redirect URI:
   - Go to https://developers.egnyte.com
   - Log in and go to your app settings
   - Check the "Redirect URI" field

2. Check your application config:
   ```bash
   egnyte-cli config list
   ```

3. Ensure they match exactly:
   - Protocol (http vs https)
   - Domain/hostname
   - Port
   - Path

4. Update your config if needed:
   ```bash
   egnyte-cli config set redirect_uri https://your-registered-uri.com/callback
   ```

**Important**: The redirect URI in the token exchange **must match exactly** what was used in the authorization request AND what's registered in the Developer Portal.

### 2. Expired or Invalid Authorization Code

**Problem**: Authorization codes are single-use and expire quickly (usually within 1-2 minutes).

**Solution**:
1. Get a fresh authorization code:
   ```bash
   egnyte-cli auth login
   ```
2. Immediately copy the code from the browser URL
3. Use it right away:
   ```bash
   egnyte-cli auth login --code FRESH_CODE
   ```

**Tip**: Don't wait between getting the code and using it. Copy and paste immediately.

### 3. HTTPS Requirement

**Problem**: Egnyte requires HTTPS redirect URIs, but you might be using HTTP.

**Solution Options**:

**Option A: Use HTTPS Redirect URI (Recommended)**
1. Set up an HTTPS redirect URI (e.g., using ngrok or a custom domain)
2. Update Developer Portal with the HTTPS URI
3. Update your config:
   ```bash
   egnyte-cli config set redirect_uri https://your-https-domain.com/callback
   ```

**Option B: Manual Code Entry with Matching URI**
Even with manual code entry, the redirect_uri in the token exchange must match what's in the Developer Portal. If your portal has HTTPS, you need to use HTTPS in your config too.

### 4. Client ID Mismatch

**Problem**: The client ID doesn't match what's registered.

**Solution**:
1. Verify your client ID:
   ```bash
   egnyte-cli config list
   ```
2. Check Developer Portal for the correct Client ID
3. Update if needed:
   ```bash
   egnyte-cli config set client_id YOUR_CORRECT_CLIENT_ID
   ```

## Step-by-Step Debugging

1. **Check your configuration**:
   ```bash
   egnyte-cli config list
   ```

2. **Verify Developer Portal settings**:
   - Go to https://developers.egnyte.com
   - Check your app's redirect URI
   - Ensure it matches your config

3. **Get a fresh authorization code**:
   ```bash
   egnyte-cli auth login
   ```
   - Copy the authorization URL
   - Open in browser
   - Complete authorization
   - Copy the code from the URL immediately

4. **Use the code immediately**:
   ```bash
   egnyte-cli auth login --code YOUR_CODE
   ```

5. **Check the error message**:
   - The improved error handling will show detailed information
   - Look for specific error codes or messages

## Example: Fixing Redirect URI Mismatch

If your Developer Portal has:
```
https://abc123.ngrok.io/callback
```

But your config has:
```
http://localhost:8080/callback
```

**Fix**:
```bash
# Update config to match Developer Portal
egnyte-cli config set redirect_uri https://abc123.ngrok.io/callback

# Then try authentication again
egnyte-cli auth login --code YOUR_CODE
```

## Example: Using ngrok for HTTPS

1. **Start ngrok**:
   ```bash
   ngrok http 8080
   ```

2. **Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

3. **Update Developer Portal**:
   - Set redirect URI to: `https://abc123.ngrok.io/callback`

4. **Update your config**:
   ```bash
   egnyte-cli config set redirect_uri https://abc123.ngrok.io/callback
   ```

5. **Authenticate**:
   ```bash
   egnyte-cli auth login
   ```
   Now it should work automatically!

## Getting Help

If you're still having issues:

1. **Check the detailed error message** - it will show specific error codes
2. **Verify all settings match**:
   - Developer Portal redirect URI
   - Application config redirect URI
   - Client ID
3. **Use a fresh authorization code** - codes expire quickly
4. **Check Egnyte documentation**: https://developers.egnyte.com/api-docs
5. **Contact Egnyte support**: partners@egnyte.com

## Quick Checklist

- [ ] Redirect URI in config matches Developer Portal exactly
- [ ] Using a fresh authorization code (not expired)
- [ ] Client ID is correct
- [ ] If using HTTPS in portal, using HTTPS in config
- [ ] Code was used immediately after getting it

