# Egnyte Developer and User Portal Setup Instructions

This document provides detailed instructions for setting up your application in both the Egnyte Developer Portal and User Portal.

## Part 1: Developer Portal Setup

### Step 1: Access Developer Portal

1. Navigate to [Egnyte Developer Portal](https://developers.egnyte.com)
2. Click **"Sign In"** or **"Register"** if you don't have an account
3. Use the email address associated with your Egnyte sandbox admin account

### Step 2: Register Developer Account

If you're registering for the first time:

1. Go to [Developer Registration](https://developers.egnyte.com/member/register)
2. Fill in the registration form:
   - **Email**: Use the email from your Egnyte sandbox invitation
   - **Password**: Create a strong password
   - **Company Name**: Your company or organization name
   - **First Name** and **Last Name**: Your name
3. Click **"Register"**
4. Check your email for verification link
5. Click the verification link to activate your account

### Step 3: Create New Application

1. **Log in** to the Developer Portal
2. Click on your **username** in the top right corner
3. Select **"Apps"** from the dropdown menu
4. Click **"Create New App"** or **"Add App"** button

### Step 4: Configure Application Details

Fill in the application form with the following information:

#### Basic Information

- **App Name**: 
  ```
  Egnyte Desktop Client for Linux
  ```
  (Or your preferred name)

- **Description**: 
  ```
  Native Linux desktop application for Egnyte with GUI and CLI interfaces. 
  Provides bidirectional file synchronization, file management, and seamless 
  integration with the Linux desktop environment.
  ```

- **App Type**: 
  - Select **"Publicly Available Application"**
  - ⚠️ **Important**: This is required for certification and public distribution

#### Domain Configuration

- **Domain**: 
  - Enter your **Egnyte sandbox domain** (provided by Egnyte representative)
  - Example: `yourdomain` (without `.egnyte.com`)
  - ⚠️ **Note**: Initially, your app will only work with this sandbox domain

#### API Products

Select the API products you need:

- ✅ **Connect** (Egnyte File Server) - **REQUIRED**
  - Provides file system operations (upload, download, list, etc.)
  - This is essential for the desktop client functionality

- ⬜ **Secure & Govern** (Optional)
  - Only needed if you require compliance and governance features
  - Not required for basic file sync operations

#### OAuth Configuration

- **Redirect URI**: 
  ```
  http://localhost:8080/callback
  ```
  - ⚠️ **Important**: Egnyte requires HTTPS redirect URIs
  - For development, you can use HTTP and manually enter the auth code
  - For automated flow, use an HTTPS redirect URI (e.g., via ngrok)
  - Must match exactly what's configured in the application
  - See [OAUTH_SETUP.md](OAUTH_SETUP.md) for detailed setup instructions

- **Scopes**: 
  - `Egnyte.filesystem` - Required for file operations
  - `Egnyte.user` - Required for user information

### Step 5: Save and Get Credentials

1. Click **"Create"** or **"Save"** button
2. You'll be redirected to the app details page
3. **Copy your Client ID (API Key)** immediately
   - This is your unique API key
   - Store it securely
   - You'll need it to configure the desktop application

### Step 6: API Key Activation

1. After creating the app, your API key will be in **"Pending"** status
2. Egnyte team will review and activate it (usually within a few days)
3. You'll receive an email notification when activated
4. Until activation, you can still use it for development in your sandbox

### Step 7: Configure Application Settings

In your app settings page, verify:

- ✅ Domain is correct
- ✅ Redirect URI matches your application configuration
- ✅ API products are selected correctly
- ✅ App type is "Publicly Available Application"

## Part 2: User Portal Setup (For End Users)

### For End Users Installing Your Application

Once your application is certified and published, end users will need to:

#### Step 1: Install the Application

Follow the installation instructions in `INSTALL.md`

#### Step 2: Configure Domain

Users need to know their Egnyte domain:

```bash
egnyte-cli config set domain THEIR_DOMAIN
```

**How users find their domain:**
- It's usually part of their Egnyte URL: `https://THEIR_DOMAIN.egnyte.com`
- They can ask their Egnyte administrator
- It's visible in their Egnyte web interface URL

#### Step 3: Configure Client ID

Users need to enter the Client ID:

```bash
egnyte-cli config set client_id YOUR_CLIENT_ID
```

**Note**: After certification, you may want to:
- Pre-configure the Client ID in the application
- Or provide it in installation instructions
- Or make it configurable through the GUI

#### Step 4: Authenticate

Users authenticate with their Egnyte credentials:

```bash
egnyte-cli auth login
```

This will:
1. Open a browser window
2. Prompt for Egnyte username and password
3. Ask for permission to access files
4. Complete authentication automatically

#### Step 5: Set Up Sync Paths

Users configure which folders to sync:

```bash
egnyte-cli sync add /home/user/Documents /Shared/Documents
```

Or use the GUI to add sync paths through the menu.

## Part 3: Pre-Certification Checklist

Before submitting for certification, ensure:

### Technical Requirements

- ✅ OAuth2 flow is implemented and working
- ✅ Application handles token refresh automatically
- ✅ Error handling is robust
- ✅ API rate limits are respected
- ✅ Security best practices are followed
- ✅ Tokens are stored securely

### Configuration

- ✅ Application works with sandbox domain
- ✅ All file operations work correctly
- ✅ Sync functionality is tested
- ✅ GUI and CLI both functional

### Documentation

- ✅ User documentation is complete
- ✅ Installation instructions are clear
- ✅ Configuration steps are documented
- ✅ Troubleshooting guide is available

## Part 4: Certification Submission

### Technical Certification Form

When ready, submit the Technical Certification Form:

1. **Application Details**:
   - App name
   - Description
   - Supported platforms (Linux/Ubuntu)
   - Installation method

2. **Technical Information**:
   - OAuth implementation details
   - API endpoints used
   - Security measures
   - Error handling approach

3. **Testing Information**:
   - Test scenarios covered
   - Known issues (if any)
   - Performance characteristics

### App Content Form

Submit marketing content for the Apps & Integrations page:

1. **App Name**: As it should appear publicly
2. **Description**: Clear, user-friendly description
3. **Features**: Key features and benefits
4. **Screenshots**: Application screenshots (if applicable)
5. **Support Information**: How users can get help

**Important**: The Apps & Integrations page is viewed by:
- Existing Egnyte customers
- Egnyte team members
- Potential new users

Make sure content explains:
- What the application does
- Why users should use it
- How it benefits them

## Part 5: Post-Certification

### After Certification Approval

1. **Production Access**:
   - Your app will be available in the Apps & Integrations catalog
   - Users can discover and install it
   - App works with any Egnyte domain (not just sandbox)

2. **Rate Limit Requests**:
   - You can request increased API rate limits
   - Provide use case and justification
   - Usually approved for production apps

3. **Updates**:
   - You can update your app listing
   - Submit new versions
   - Update marketing content

### Maintaining Your Application

1. **Monitor Usage**:
   - Check API usage in Developer Portal
   - Monitor for errors or issues
   - Track user feedback

2. **Updates**:
   - Release updates as needed
   - Test thoroughly before release
   - Document changes

3. **Support**:
   - Provide user support
   - Address issues promptly
   - Update documentation

## Part 6: Common Issues and Solutions

### Issue: API Key Not Activated

**Symptom**: Getting authentication errors even with correct credentials

**Solution**:
- Wait for Egnyte team to activate the key (usually 1-3 days)
- Check email for activation notification
- Contact Egnyte support if it's been more than a week

### Issue: Redirect URI Mismatch

**Symptom**: OAuth fails with "redirect_uri_mismatch" error

**Solution**:
- Ensure redirect URI in Developer Portal matches exactly
- Default: `http://localhost:8080/callback`
- Check for trailing slashes or protocol differences
- Update both Developer Portal and application config

### Issue: Domain Not Found

**Symptom**: Cannot connect to API

**Solution**:
- Verify domain is correct (without `.egnyte.com`)
- Ensure domain is accessible
- Check if using sandbox vs production domain

### Issue: Rate Limit Exceeded

**Symptom**: 429 Too Many Requests errors

**Solution**:
- Default limit: 2 QPS, 1000 daily calls
- Implement better rate limiting in application
- Request increased limits if needed
- Optimize API usage (batch operations, caching)

## Part 7: Best Practices

### Security

- ✅ Never commit API keys or tokens to version control
- ✅ Use secure storage for tokens (keyring)
- ✅ Implement proper error handling
- ✅ Validate all user inputs
- ✅ Use HTTPS for all API calls

### Performance

- ✅ Respect API rate limits
- ✅ Implement efficient sync algorithms
- ✅ Use file hashing to detect changes
- ✅ Debounce file system events
- ✅ Cache metadata when possible

### User Experience

- ✅ Provide clear error messages
- ✅ Show sync status clearly
- ✅ Handle conflicts gracefully
- ✅ Provide both GUI and CLI options
- ✅ Make configuration simple

## Part 8: Support and Resources

### Egnyte Resources

- **API Documentation**: https://developers.egnyte.com/api-docs
- **Integrations Cookbook**: https://egnyte.github.io/integrations-cookbook/
- **Developer Support**: partners@egnyte.com
- **Developer Portal**: https://developers.egnyte.com

### Application Resources

- **Installation Guide**: See `INSTALL.md`
- **Developer Setup**: See `DEVELOPER_SETUP.md`
- **README**: See `README.md`

## Summary Checklist

### Developer Portal

- [ ] Created developer account
- [ ] Registered and verified email
- [ ] Created new application
- [ ] Set app type to "Publicly Available Application"
- [ ] Selected "Connect" API product
- [ ] Configured redirect URI: `http://localhost:8080/callback`
- [ ] Copied and saved Client ID
- [ ] Verified all settings

### Application Configuration

- [ ] Installed application dependencies
- [ ] Configured domain: `egnyte-cli config set domain YOUR_DOMAIN`
- [ ] Configured client ID: `egnyte-cli config set client_id YOUR_CLIENT_ID`
- [ ] Tested authentication: `egnyte-cli auth login`
- [ ] Verified API connection: `egnyte-cli ls /`
- [ ] Added test sync path
- [ ] Tested file operations

### Pre-Certification

- [ ] All features tested and working
- [ ] OAuth flow working correctly
- [ ] Error handling implemented
- [ ] Documentation complete
- [ ] Ready for certification submission

### Post-Certification

- [ ] App listed in catalog
- [ ] User documentation available
- [ ] Support process established
- [ ] Monitoring in place

