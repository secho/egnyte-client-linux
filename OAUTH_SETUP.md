# OAuth Authentication Setup Guide

Egnyte requires **HTTPS redirect URIs** for OAuth authentication. This guide explains how to set up authentication for the desktop client.

## The Problem

Egnyte's OAuth implementation requires HTTPS redirect URIs. However, for localhost development, we typically use HTTP. This creates a conflict.

## Solutions

### Solution 1: Manual Code Entry (Recommended for Development)

This is the simplest solution for development and testing.

#### Steps:

1. **Start authentication**:
   ```bash
   egnyte-cli auth login
   ```

2. **The application will show you an authorization URL**. Open it in your browser:
   ```
   https://yourdomain.egnyte.com/puboauth/authorize?client_id=...&redirect_uri=...
   ```

3. **Log in and authorize** the application in the browser.

4. **After authorization**, you'll be redirected to an error page (because the redirect URI is HTTP). 

5. **Look at the URL** in your browser's address bar. It will look like:
   ```
   http://localhost:8080/callback?code=AUTHORIZATION_CODE_HERE&...
   ```

6. **Copy the `code` parameter** value (everything after `code=` and before `&`).

7. **Enter the code**:
   ```bash
   egnyte-cli auth login --code AUTHORIZATION_CODE_HERE
   ```

   Or if you're already in the interactive prompt, just paste the code when asked.

#### Example:

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
Authorization code: abc123xyz456
Authentication successful!
```

### Solution 2: Use HTTPS Redirect URI with ngrok

For a more automated experience, you can use ngrok to create an HTTPS tunnel to localhost.

#### Steps:

1. **Install ngrok**:
   ```bash
   # Download from https://ngrok.com/download
   # Or use snap:
   sudo snap install ngrok
   ```

2. **Start ngrok tunnel**:
   ```bash
   ngrok http 8080
   ```

3. **Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

4. **Update Developer Portal**:
   - Go to your app settings in Egnyte Developer Portal
   - Set Redirect URI to: `https://abc123.ngrok.io/callback`

5. **Update application config**:
   ```bash
   egnyte-cli config set redirect_uri https://abc123.ngrok.io/callback
   ```

6. **Authenticate**:
   ```bash
   egnyte-cli auth login
   ```

   Now the automatic callback will work!

**Note**: The ngrok URL changes each time you restart ngrok (unless you have a paid account). You'll need to update both the Developer Portal and your config each time.

### Solution 3: Use a Custom Domain with HTTPS

If you have a domain with HTTPS, you can use it:

1. **Set up a web server** that redirects to your local application
2. **Update Developer Portal** with your HTTPS redirect URI
3. **Update application config** with the same URI
4. **Authenticate normally**

## Updating Redirect URI in Developer Portal

1. Go to [Egnyte Developer Portal](https://developers.egnyte.com)
2. Log in and go to **Apps**
3. Select your application
4. Edit the **Redirect URI** field
5. Enter your HTTPS redirect URI (or keep HTTP for manual code entry)
6. Save changes

## Updating Redirect URI in Application

```bash
# For ngrok
egnyte-cli config set redirect_uri https://your-ngrok-url.ngrok.io/callback

# For custom domain
egnyte-cli config set redirect_uri https://yourdomain.com/callback

# For HTTP (manual code entry)
egnyte-cli config set redirect_uri http://localhost:8080/callback
```

## Troubleshooting

### Error: "Invalid redirect uri redirect uri must be a valid https url"

**Cause**: Egnyte requires HTTPS redirect URIs.

**Solutions**:
1. Use manual code entry (Solution 1 above)
2. Use ngrok (Solution 2 above)
3. Update Developer Portal to use an HTTPS redirect URI

### Error: "redirect_uri_mismatch"

**Cause**: The redirect URI in Developer Portal doesn't match the one in your config.

**Solution**:
1. Check Developer Portal redirect URI
2. Check application config: `egnyte-cli config list`
3. Ensure they match exactly (including protocol, domain, port, and path)

### Can't find the authorization code in the URL

**Solution**:
- The code is in the URL after `code=`
- It's usually a long alphanumeric string
- Copy everything from `code=` to the next `&` (or end of URL)
- Example: If URL is `http://localhost:8080/callback?code=abc123&state=xyz`, the code is `abc123`

## Best Practices

1. **For Development**: Use manual code entry (Solution 1) - it's simplest
2. **For Testing**: Use ngrok (Solution 2) - more automated
3. **For Production**: Use a proper HTTPS domain with a web server that handles the callback

## Security Notes

- Authorization codes are single-use and expire quickly
- Never share your authorization codes
- The application stores tokens securely using keyring
- Refresh tokens are stored in system keyring (most secure)
- Access tokens are stored in config file (expire quickly)

## Additional Resources

- [Egnyte API Documentation](https://developers.egnyte.com/api-docs)
- [Egnyte Integrations Cookbook - Authentication](https://egnyte.github.io/integrations-cookbook/auth.html)
- [ngrok Documentation](https://ngrok.com/docs)

