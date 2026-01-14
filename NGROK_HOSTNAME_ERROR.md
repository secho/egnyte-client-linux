# Fixing "Request hostname and redirect url hostname do not match" Error

## The Problem

Even when the redirect URI in Developer Portal matches your config exactly, you get:
```json
{"errorMessage":"Request hostname and redirect url hostname do not match"}
```

This is a security validation that Egnyte performs, and it can be problematic with ngrok or other tunneling services.

## Solution: Use Localhost Callback (Automatic)

Since Egnyte's hostname validation is causing issues with ngrok, the most reliable solution is to use manual code entry with `https://localhost:8080/callback`.

### Step 1: Update Developer Portal

1. Go to https://developers.egnyte.com
2. Log in → Apps → Your App
3. Set "Registered OAuth Redirect URI" to: `https://localhost:8080/callback`
4. **Save**

### Step 2: Update Application Config

```bash
egnyte-cli config set redirect_uri https://localhost:8080/callback
```

### Step 3: Authenticate (Automatic Callback)

```bash
egnyte-cli auth login
```

This will:
1. Show you an authorization URL
2. Open it in your browser
3. You'll see a security warning (because localhost HTTPS uses a self-signed certificate) - click "Advanced" → "Proceed"
4. Complete authorization
5. The app receives the callback and finishes login automatically

If the callback server can't start, the CLI will prompt for manual code entry as a fallback.

## Why This Works

Manual code entry bypasses the hostname validation because:
- You're copying the code directly from the browser
- The token exchange uses the same redirect_uri that was in the authorization request
- Egnyte validates the redirect_uri matches, but doesn't check the request origin

## Alternative: Contact Egnyte Support

If you need automated OAuth flow (without manual code entry), you may need to:
1. Contact Egnyte support: partners@egnyte.com
2. Explain you're using ngrok for development
3. Ask if they can whitelist your ngrok domain or provide guidance

## Why ngrok Fails

Egnyte's hostname validation checks:
- The redirect_uri hostname
- Possibly the request Origin/Referer header
- Some internal whitelist or validation

With ngrok:
- The ngrok domain is external
- It might not be on an allowed list
- The validation might be too strict

Using `localhost` with manual code entry avoids these validation issues.

