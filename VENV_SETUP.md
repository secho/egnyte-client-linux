# Virtual Environment Setup for Egnyte Desktop

## Problem

When using a virtual environment, PyGObject (`gi` module) may not be available because it's installed as a system package (`python3-gi`).

## Solution: Use System Site Packages

PyGObject must be installed as a system package and accessed from the virtual environment.

### Option 1: Recreate Venv with System Site Packages (Recommended)

```bash
# Remove existing venv
rm -rf .venv

# Create new venv with system site packages
python3 -m venv .venv --system-site-packages

# Activate venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install application
pip install -e .
```

### Option 2: Modify Existing Venv

If you want to keep your existing venv:

1. **Edit the venv's pyvenv.cfg**:
   ```bash
   # In .venv/pyvenv.cfg, change:
   include-system-site-packages = false
   # to:
   include-system-site-packages = true
   ```

2. **Reinstall packages**:
   ```bash
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install -e .
   ```

### Option 3: Install Without Virtual Environment

If you prefer not to use a venv:

```bash
# Install system dependencies (if not already installed)
sudo apt-get install -y python3-gi python3-gi-cairo \
    gir1.2-gtk-3.0 gir1.2-glib-2.0 gir1.2-gdkpixbuf-2.0 \
    gir1.2-pango-1.0

# Install Python packages (use --user to avoid system-wide install)
pip3 install --user -r requirements.txt
pip3 install --user -e .
```

## Verify Installation

After setup, verify PyGObject is available:

```bash
python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk; print('PyGObject working!')"
```

## Why This Is Needed

PyGObject (the `gi` module) is tightly integrated with system libraries (GTK, GLib, etc.) and must be installed via system packages (`apt-get install python3-gi`). Virtual environments don't include system packages by default, so we need to enable `--system-site-packages` to access them.

## Alternative: Install PyGObject in Venv

You can also install PyGObject directly in the venv, but this requires all system dependencies:

```bash
source .venv/bin/activate

# Ensure system dependencies are installed
sudo apt-get install -y libgirepository1.0-dev gobject-introspection \
    pkg-config libcairo2-dev build-essential python3-dev

# Install PyGObject in venv
pip install PyGObject
```

However, using `--system-site-packages` is simpler and recommended.

