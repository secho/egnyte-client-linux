# Manual Authentication Guide - Step by Step

## The Process

When using `https://localhost:8080/callback`, you'll see a connection error in the browser - **this is normal and expected**. The important part is getting the code from the URL.

## Step-by-Step Instructions

### Step 1: Start Authentication

```bash
egnyte-cli auth login
```

This will show you an authorization URL and open it in your browser.

### Step 2: Authorize in Browser

1. **Log in** to Egnyte if prompted
2. **Click "Allow"** or "Authorize" to grant permissions
3. You'll be redirected to `localhost:8080/callback?code=XXXXX&state=`

### Step 3: Copy the Code IMMEDIATELY

**Important**: Authorization codes expire in 1-2 minutes!

1. **Look at the browser address bar** (even if the page shows an error)
2. The URL will be: `localhost:8080/callback?code=YOUR_CODE_HERE&state=`
3. **Copy the code** - it's the value after `code=` and before `&`
4. **Use it immediately** - don't wait!

### Step 4: Use the Code

```bash
egnyte-cli auth login --code YOUR_CODE_HERE
```

**Example**:
```bash
# From the URL: localhost:8080/callback?code=V48VD8Ck&state=
# Use:
egnyte-cli auth login --code V48VD8Ck
```

## Common Issues

### Issue 1: "Connection Refused" Error

**What you see**: Browser shows "This site can't be reached" or "ERR_CONNECTION_REFUSED"

**This is NORMAL!** You don't need the page to load. Just:
1. Look at the address bar
2. Copy the code from the URL
3. Use it in the command

### Issue 2: Code Expired

**Error**: `400 Bad Request` or token exchange fails

**Cause**: You waited too long before using the code

**Solution**: 
1. Get a fresh code: `egnyte-cli auth login`
2. Copy the code immediately
3. Use it right away: `egnyte-cli auth login --code FRESH_CODE`

### Issue 3: Redirect URI Mismatch

**Error**: `400 Bad Request` with redirect_uri error

**Solution**:
1. Check Developer Portal redirect URI
2. Check your config: `egnyte-cli config list`
3. They must match EXACTLY: `https://localhost:8080/callback`

### Issue 4: Can't See the Code in URL

**Solution**:
- The code is in the address bar, even if the page shows an error
- Look for `?code=` in the URL
- Copy everything after `code=` until `&` (or end of URL)

## Quick Reference

```bash
# 1. Start auth
egnyte-cli auth login

# 2. Authorize in browser (ignore connection error)

# 3. Copy code from URL (e.g., V48VD8Ck)

# 4. Use immediately
egnyte-cli auth login --code V48VD8Ck
```

## Tips

- **Work fast**: Codes expire in 1-2 minutes
- **Ignore browser errors**: The connection error is expected
- **Check the address bar**: The code is always in the URL
- **Verify redirect URI**: Must match exactly in both places

## Verification

After successful authentication:

```bash
egnyte-cli auth status
# Should show: Authenticated

egnyte-cli ls /
# Should list your Egnyte files
```

