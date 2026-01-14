# Developer Setup Instructions

This document provides step-by-step instructions for setting up the Egnyte Desktop Client for development and deployment.

## Prerequisites

- Ubuntu 20.04+ or similar Linux distribution with GNOME
- Python 3.8 or higher
- Git (for cloning the repository)
- Internet connection for API access

## Part 1: Egnyte Developer Portal Setup

### Step 1: Create Developer Account

1. Go to [Egnyte Developer Registration](https://developers.egnyte.com/member/register)
2. Sign up with your email address
3. Verify your email address by clicking the link in the confirmation email
4. Log in to your developer account

### Step 2: Create Application

1. After logging in, click on your username in the top right corner
2. Select **"Apps"** from the dropdown menu
3. Click **"Create New App"** or **"Add App"**
4. Fill in the application details:
   - **App Name**: `Egnyte Desktop Client for Linux` (or your preferred name)
   - **Description**: Describe your application
   - **Domain**: Use the Egnyte sandbox domain provided by Egnyte (e.g., `yourdomain`)
   - **Type**: Select **"Publicly Available Application"** (required for certification)
   - **API Products**: Select **"Connect"** (Egnyte File Server) - this is required for file operations
   - **Redirect URI**: `http://localhost:8080/callback` (default for OAuth callback)

5. Click **"Create"** or **"Save"**

### Step 3: Get API Credentials

1. After creating the app, you'll be shown your **Client ID** (API Key)
2. **Copy and save this Client ID** - you'll need it for configuration
key: e1egs2eG1WhulNmXNOm60VVxxif2n8OzXV5qIgBhLZ9RHIja
secret: lSRIb0OAaUb5JawvGys8ASaaImxPqaSL70dtUi8uxyamBGvzAUmybfzAwKokKXM4

3. Note: The API key will be tied to your sandbox environment initially
4. The key will be activated after verification by Egnyte team (usually within a few days)

### Step 4: Configure Redirect URI

1. In your app settings, ensure the Redirect URI is set to: `http://localhost:8080/callback`
2. This is the default callback URL for OAuth authentication
3. If you need a different port, update both the app settings and the application configuration

## Part 2: Application Configuration

### Step 1: Install System Dependencies

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
    build-essential \
    python3-dev \
    libgirepository1.0-dev \
    gobject-introspection \
    pkg-config \
    libcairo2-dev
```

### Step 2: Install Python Dependencies

**Important**: If using a virtual environment, it must be created with `--system-site-packages` to access PyGObject:

```bash
cd /path/to/egnyte-desktop

# If using venv, recreate with system site packages:
# rm -rf .venv
# python3 -m venv .venv --system-site-packages
# source .venv/bin/activate

# Or if venv already exists, enable system site packages:
# Edit .venv/pyvenv.cfg and set: include-system-site-packages = true

pip3 install -r requirements.txt
```

Or install in development mode:

```bash
pip3 install -e .
```

**Note**: See [VENV_SETUP.md](VENV_SETUP.md) for detailed virtual environment setup instructions.

### Step 3: Configure the Application

Set your Egnyte domain:

```bash
egnyte-cli config set domain YOUR_DOMAIN
```

Set your Client ID (from Step 3 above):

```bash
egnyte-cli config set client_id YOUR_CLIENT_ID
```

Verify configuration:

```bash
egnyte-cli config list
```

### Step 4: Authenticate

**Important**: Egnyte requires HTTPS redirect URIs. See [OAUTH_SETUP.md](OAUTH_SETUP.md) for detailed instructions.

#### Quick Start (Manual Code Entry):

Run the authentication command:

```bash
egnyte-cli auth login
```

The application will:
1. Show you an authorization URL
2. Open it in your browser (or you can copy/paste it)
3. After you log in and authorize, you'll see an error page
4. Copy the `code` parameter from the URL
5. Enter it when prompted (or use `--code` option)

**Example**:
```bash
$ egnyte-cli auth login
Starting authentication...
[Authorization URL shown]
Or enter the code now: abc123xyz456
Authentication successful!
```

**Alternative**: Use the `--code` option if you already have the code:
```bash
egnyte-cli auth login --code YOUR_AUTHORIZATION_CODE
```

**Note**: For automated authentication, you can use ngrok or another HTTPS tunnel. See [OAUTH_SETUP.md](OAUTH_SETUP.md) for details.

### Step 5: Test the Connection

List files in your Egnyte account:

```bash
egnyte-cli ls /
```

If successful, you should see a list of folders and files.

## Part 3: Setting Up Sync Paths

### Add a Sync Path

A sync path maps a local directory to a remote Egnyte path:

```bash
egnyte-cli sync add /home/user/Documents /Shared/Documents
```

This will:
- Sync files from `/home/user/Documents` to `/Shared/Documents` in Egnyte
- Automatically upload local changes
- Download remote changes

### List Sync Paths

```bash
egnyte-cli sync list
```

### Remove a Sync Path

```bash
egnyte-cli sync remove /home/user/Documents
```

## Part 4: Running the Application

### GUI Mode

Launch the graphical interface:

```bash
egnyte-desktop
```

The GUI provides:
- File browser for remote files
- Sync status monitoring
- Upload/download operations
- Sync path management

### CLI Mode

All operations can be performed via command line:

```bash
# Upload a file
egnyte-cli upload /path/to/local/file.txt /Shared/Documents/file.txt

# Download a file
egnyte-cli download /Shared/Documents/file.txt /path/to/local/

# Sync all configured paths
egnyte-cli sync now

# List remote files
egnyte-cli ls /Shared/
```

## Part 5: API Rate Limits

**Important**: Egnyte enforces rate limits:

- **Default**: 2 Queries Per Second (QPS) and 1,000 calls per day per user
- These limits apply per Egnyte user
- Usage by one user doesn't affect other users' quotas

### Requesting Higher Limits

If you need increased rate limits:

1. Send an email to Egnyte support with:
   - Your API key (Client ID)
   - Use case description (which APIs you're using)
   - Type of operations (upload, download, metadata, etc.)
   - Reasoning for increased rates

2. Increased rates are usually provided for:
   - Production applications (post-certification)
   - Pre-certification testing (in certain cases)

## Part 6: Certification Process

To make your application publicly available, you must complete certification:

### Requirements

1. **OAuth Flow**: Your app must implement OAuth2 (already implemented)
2. **Security**: Application must maintain security when accessing APIs
3. **User Experience**: Provide seamless experience for customers

### Steps

1. **Complete Development**: Ensure all features work correctly
2. **Test Thoroughly**: Test with your sandbox environment
3. **Submit Technical Certification Form**:
   - Egnyte team will review your application
   - They'll verify authentication and security protocols
   - Review can take up to 3 weeks (usually faster)
4. **Submit App Content Form**:
   - Marketing form for your app listing
   - Content will appear on Egnyte's Apps & Integrations page
   - Should explain benefits for Egnyte users

### Post-Certification

After certification:
- Your app will be available in Egnyte's Apps & Integrations page
- You can request increased API rate limits
- Your app can be used by any Egnyte customer

## Part 7: Troubleshooting

### Authentication Issues

**Problem**: "Not authenticated" error

**Solution**:
```bash
egnyte-cli auth login
```

**Problem**: Authentication fails with "redirect_uri mismatch"

**Solution**: 
1. Check that redirect URI in app settings matches configuration
2. Default should be: `http://localhost:8080/callback`
3. Update if needed: `egnyte-cli config set redirect_uri http://localhost:8080/callback`

### API Errors

**Problem**: 401 Unauthorized

**Solution**: 
- Tokens may have expired
- Run `egnyte-cli auth login` again
- The app should auto-refresh tokens, but manual refresh may be needed

**Problem**: 429 Too Many Requests

**Solution**:
- You've hit the rate limit (2 QPS or 1,000 daily)
- Wait a moment and try again
- Consider implementing better rate limiting in your code
- Request higher limits if needed

### File Sync Issues

**Problem**: Files not syncing

**Solution**:
1. Check sync paths: `egnyte-cli sync list`
2. Verify permissions on local folders
3. Check Egnyte folder permissions
4. Review sync logs for errors

**Problem**: Conflicts (both local and remote changed)

**Solution**:
- Current strategy: newer file wins
- Manual resolution may be needed for important files
- Consider implementing conflict resolution UI

## Part 8: Development Tips

### Testing

Test with your sandbox environment before production:
- Create test files and folders
- Test upload/download operations
- Test sync functionality
- Verify error handling

### Logging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Optimization

The application includes:
- Rate limiting to respect API limits
- Efficient file hashing (MD5) for change detection
- Debounced file watching to reduce API calls
- Async operations where possible

### Security

- Tokens are stored securely using keyring
- Access tokens stored in config (expire quickly)
- Refresh tokens stored in system keyring
- Never commit tokens to version control

## Part 9: Deployment

### Create Distribution Package

```bash
python3 setup.py sdist bdist_wheel
```

### Install System-Wide

```bash
sudo pip3 install .
```

### Create Desktop Entry

Create `~/.local/share/applications/egnyte-desktop.desktop`:

```ini
[Desktop Entry]
Name=Egnyte Desktop
Comment=Egnyte Desktop Client for Linux
Exec=egnyte-desktop
Icon=egnyte-desktop
Terminal=false
Type=Application
Categories=Network;FileTransfer;
```

## Support

For issues or questions:
- Check Egnyte API documentation: https://developers.egnyte.com/api-docs
- Check Egnyte Integrations Cookbook: https://egnyte.github.io/integrations-cookbook/
- Contact Egnyte support: partners@egnyte.com

