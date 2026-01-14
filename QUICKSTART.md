# Quick Start Guide

Get up and running with Egnyte Desktop Client in 5 minutes!

## Prerequisites

- Ubuntu 20.04+ with GNOME
- Python 3.8+
- Egnyte sandbox account (provided by Egnyte)

## Step 1: Install Dependencies

```bash
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0 \
    gir1.2-glib-2.0 \
    gir1.2-gdkpixbuf-2.0 \
    gir1.2-pango-1.0 \
    libgirepository1.0-dev \
    gobject-introspection \
    pkg-config \
    libcairo2-dev
```

## Step 2: Install Application

```bash
cd /path/to/egnyte-desktop
pip3 install --user -r requirements.txt
pip3 install --user -e .
```

## Step 3: Get API Credentials

1. Go to [Egnyte Developer Portal](https://developers.egnyte.com/member/register)
2. Create account and verify email
3. Create new app:
   - Name: `Egnyte Desktop Client for Linux`
   - Type: `Publicly Available Application`
   - API Product: Select `Connect`
   - Redirect URI: `http://localhost:8080/callback`
   - Domain: Your sandbox domain
4. Copy your **Client ID**

## Step 4: Configure Application

```bash
# Set your Egnyte domain
egnyte-cli config set domain YOUR_DOMAIN

# Set your Client ID
egnyte-cli config set client_id YOUR_CLIENT_ID

# Verify configuration
egnyte-cli config list
```

## Step 5: Authenticate

**Note**: Egnyte requires HTTPS redirect URIs. For development, use manual code entry:

```bash
egnyte-cli auth login
```

Follow the instructions:
1. Open the authorization URL shown
2. Log in and authorize in browser
3. Copy the `code` parameter from the error page URL
4. Enter the code when prompted

Or use the code directly:
```bash
egnyte-cli auth login --code YOUR_AUTHORIZATION_CODE
```

See [OAUTH_SETUP.md](OAUTH_SETUP.md) for detailed instructions and HTTPS setup options.

## Step 6: Test Connection

```bash
# List files in your Egnyte account
egnyte-cli ls /

# Should show folders like /Shared, /Private, etc.
```

## Step 7: Set Up Sync

```bash
# Add a sync path (local folder <-> remote folder)
egnyte-cli sync add /home/user/Documents /Shared/Documents

# Sync now
egnyte-cli sync now
```

## Step 8: Launch GUI

```bash
egnyte-desktop
```

You should see:
- File browser on the left
- Sync status on the right
- Menu bar with options

## Common Commands

```bash
# Upload a file
egnyte-cli upload /path/to/file.txt /Shared/Documents/

# Download a file
egnyte-cli download /Shared/Documents/file.txt /path/to/local/

# List remote files
egnyte-cli ls /Shared/

# Check status
egnyte-cli status

# Sync all paths
egnyte-cli sync now
```

## Troubleshooting

**Authentication fails?**
- Check domain and client ID are correct
- Ensure redirect URI matches: `http://localhost:8080/callback`
- Make sure port 8080 is available

**Can't connect to API?**
- Verify domain is correct (without `.egnyte.com`)
- Check internet connection
- Ensure API key is activated (may take a few days)

**Files not syncing?**
- Check sync paths: `egnyte-cli sync list`
- Verify folder permissions
- Check sync logs for errors

## Next Steps

- Read [DEVELOPER_SETUP.md](DEVELOPER_SETUP.md) for detailed setup
- Read [EGNYTE_PORTAL_SETUP.md](EGNYTE_PORTAL_SETUP.md) for portal configuration
- See [README.md](README.md) for full documentation

## Getting Help

- Check Egnyte API docs: https://developers.egnyte.com/api-docs
- Check Cookbook: https://egnyte.github.io/integrations-cookbook/
- Contact Egnyte: partners@egnyte.com

