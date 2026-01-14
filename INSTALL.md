# Installation Guide

## Quick Installation

### Ubuntu/Debian

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

# Install application
pip3 install --user egnyte-desktop

# Or install from source
git clone <repository-url>
cd egnyte-desktop
pip3 install --user -r requirements.txt
pip3 install --user -e .
```

## Initial Setup

1. **Configure Domain and Client ID**:
   ```bash
   egnyte-cli config set domain YOUR_DOMAIN
   egnyte-cli config set client_id YOUR_CLIENT_ID
   ```

2. **Authenticate**:
   ```bash
   egnyte-cli auth login
   ```

3. **Add Sync Path**:
   ```bash
   egnyte-cli sync add /home/user/Documents /Shared/Documents
   ```

4. **Launch GUI**:
   ```bash
   egnyte-desktop
   ```

## System Requirements

- **OS**: Ubuntu 20.04+ or similar Linux with GNOME
- **Python**: 3.8 or higher
- **GTK**: 3.0 or higher
- **Disk Space**: ~50 MB for application + space for synced files
- **Network**: Internet connection for API access

## Uninstallation

```bash
pip3 uninstall egnyte-desktop
rm -rf ~/.config/egnyte-desktop
```

