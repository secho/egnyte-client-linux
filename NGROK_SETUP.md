# ngrok Setup for Egnyte OAuth

## The Error

`{"errorMessage":"Request hostname and redirect url hostname do not match"}`

This means the redirect URI in your Developer Portal doesn't match the one in your application config.

## Solution

### Step 1: Start ngrok

```bash
ngrok http 8080
```

You'll see output like:
```
Forwarding   https://abc123.ngrok.app -> http://localhost:8080
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok.app`)

### Step 2: Update Developer Portal

1. Go to https://developers.egnyte.com
2. Log in → Apps → Your App
3. Find "Registered OAuth Redirect URI"
4. Set it to: `https://abc123.ngrok.app/callback` (use YOUR ngrok URL)
5. **Save** the changes

### Step 3: Update Application Config

```bash
egnyte-cli config set redirect_uri https://abc123.ngrok.app/callback
```

**Important**: Use the EXACT same URL in both places!

### Step 4: Verify They Match

```bash
# Check your config
egnyte-cli config list

# Compare with Developer Portal
# They must match EXACTLY:
# - Protocol (https)
# - Domain (abc123.ngrok.app)
# - Port (none for ngrok)
# - Path (/callback)
```

### Step 5: Authenticate

```bash
egnyte-cli auth login
```

Now it should work automatically without manual code entry!

## Important Notes

### ngrok URL Changes

**Free ngrok accounts**: The URL changes every time you restart ngrok.

**Solution**: Each time you restart ngrok:
1. Get the new ngrok URL
2. Update BOTH Developer Portal AND your config
3. They must always match

### Static ngrok Domain (Paid)

If you have a paid ngrok account with a static domain:
- Set it once in Developer Portal
- Set it once in your config
- No need to update each time

### Troubleshooting

**Still getting the error?**

1. **Double-check exact match**:
   ```bash
   egnyte-cli config list
   ```
   Compare character-by-character with Developer Portal

2. **Check for typos**: 
   - `https://` not `http://`
   - `/callback` not `/callback/` (trailing slash)
   - Domain spelling

3. **Clear browser cache**: Sometimes browsers cache redirects

4. **Try incognito/private window**: To avoid cache issues

5. **Wait a moment**: After updating Developer Portal, wait 10-30 seconds for changes to propagate

## Quick Reference

```bash
# 1. Start ngrok
ngrok http 8080

# 2. Copy the HTTPS URL (e.g., https://abc123.ngrok.app)

# 3. Update Developer Portal with: https://abc123.ngrok.app/callback

# 4. Update config
egnyte-cli config set redirect_uri https://abc123.ngrok.app/callback

# 5. Verify
egnyte-cli config list

# 6. Authenticate
egnyte-cli auth login
```

## Alternative: Use Manual Code Entry

If ngrok is too cumbersome (URL changes each time), you can stick with manual code entry:

1. Set Developer Portal to: `https://localhost:8080/callback`
2. Set config to: `https://localhost:8080/callback`
3. Use manual code entry (copy code from browser URL)

This avoids the ngrok URL management issue.

