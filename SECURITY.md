## Security Policy

### Supported Versions

We support the latest released version of egnyte-cli and the current `main` branch.

### Reporting a Vulnerability

Please report security issues privately via GitHub Security Advisories for this repository. If you are unable to use GitHub, open a regular issue with minimal detail and we will follow up to move the conversation to a private channel.

### Security Practices

- OAuth tokens are stored in the system keyring when available
- Configuration and token files are restricted to the user (0600)
- Authentication flows follow Egnyte OAuth guidance
