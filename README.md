# Egnyte CLI for Linux

[![PyPI](https://img.shields.io/pypi/v/egnyte-cli)](https://pypi.org/project/egnyte-cli/)
[![Python](https://img.shields.io/pypi/pyversions/egnyte-cli)](https://pypi.org/project/egnyte-cli/)
[![License](https://img.shields.io/github/license/secho/egnyte-cli)](LICENSE)
[![CI](https://github.com/secho/egnyte-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/secho/egnyte-cli/actions/workflows/ci.yml)
[![Downloads](https://img.shields.io/pypi/dm/egnyte-cli)](https://pypi.org/project/egnyte-cli/)

Professional command-line client for Egnyte on Linux with OAuth authentication, sync, and optional FUSE mounting.

## Features

- OAuth2 authentication (Authorization Code and Resource Owner Password for internal apps)
- Bidirectional sync engine with conflict policies
- CLI for upload, download, list, and status
- Optional FUSE filesystem mount
- Rate-limited API client with retry/backoff

## Quick Start

```bash
# 1) Install (recommended)
pipx install egnyte-cli

# 2) Configure
egnyte-cli config set domain YOUR_DOMAIN
egnyte-cli config set client_id YOUR_CLIENT_ID
egnyte-cli config set client_secret YOUR_CLIENT_SECRET

# 3) Authenticate
egnyte-cli auth login

# Example commands
egnyte-cli ls /Shared/
egnyte-cli upload ./file.txt /Shared/Documents/
```

## Installation

### System requirements

- Python 3.8+
- Linux (Ubuntu/Debian tested)

### Recommended install (no virtualenv)

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install egnyte-cli
```

### Alternative (pip)

```bash
python3 -m pip install --user egnyte-cli
```

### Optional system dependencies

FUSE mount support (optional):
```bash
sudo apt-get update
sudo apt-get install -y fuse libfuse-dev
```

Keyring backend (recommended for storing tokens and secrets securely):
```bash
sudo apt-get install -y gnome-keyring libsecret-1-0
```

## Authentication

### Authorization Code (default)

```bash
egnyte-cli auth login
```

If your redirect URI is HTTPS localhost, you may see a certificate warning on callback. For alternatives, see [docs/oauth-setup.md](docs/oauth-setup.md).

### Resource Owner Password (internal apps only)

```bash
egnyte-cli auth login --password-flow --username USERNAME
```

This flow is supported only for internal application keys, as per Egnyte documentation.

## Usage

```bash
# Sync paths
egnyte-cli sync add /local/path /Shared/Folder
egnyte-cli sync list
egnyte-cli sync now

# File operations
egnyte-cli ls /Shared/
egnyte-cli upload ./file.txt /Shared/Documents/
egnyte-cli download /Shared/Documents/file.txt ./file.txt

# Status
egnyte-cli auth status
egnyte-cli status
```

## Configuration

Configuration and tokens are stored under:
```
~/.config/egnyte-desktop/
```

## Documentation

- OAuth setup: [docs/oauth-setup.md](docs/oauth-setup.md)
- Development setup: [docs/development.md](docs/development.md)

## Security

Security-related information and reporting instructions are in [SECURITY.md](SECURITY.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT. See [LICENSE](LICENSE).
