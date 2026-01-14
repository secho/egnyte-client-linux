# Egnyte Desktop Client for Linux

A native Linux desktop application for Egnyte with both GUI and CLI interfaces, built with GTK3 and optimized for speed.

## Features

- **Bidirectional File Sync**: Automatic synchronization between local and Egnyte cloud storage
- **GTK3 GUI**: Native GNOME/Ubuntu interface with file browser
- **CLI Interface**: Full command-line access to all operations
- **OAuth2 Authentication**: Secure authentication flow
- **File Watching**: Real-time monitoring of local file changes
- **Efficient Sync**: Optimized algorithms for fast synchronization
- **Status Indicators**: Visual feedback for sync status

## Requirements

- Python 3.8+
- GTK3 development libraries
- Ubuntu 20.04+ / GNOME 3.36+

## Installation

```bash
# Install system dependencies
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

# Install Python dependencies
pip3 install -r requirements.txt

# Install the application
python3 setup.py install
```

**Note**: If using a virtual environment, it must be created with `--system-site-packages` to access PyGObject. See [VENV_SETUP.md](VENV_SETUP.md) for details.

## Quick Start

### GUI Mode
```bash
egnyte-desktop
```

### CLI Mode
```bash
# Authenticate
egnyte-cli auth login

# Sync a folder
egnyte-cli sync /path/to/local/folder /Shared/Folder

# Upload a file
egnyte-cli upload /path/to/file.txt /Shared/Documents/

# Download a file
egnyte-cli download /Shared/Documents/file.txt /path/to/local/

# List files
egnyte-cli ls /Shared/

# Status
egnyte-cli status
```

## Configuration

The application stores configuration in `~/.config/egnyte-desktop/`

## Development

See [DEVELOPER_SETUP.md](DEVELOPER_SETUP.md) for detailed setup instructions.

## License

MIT

# egnyte-client-linux
# egnyte-client-linux
