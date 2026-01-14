# Installation Fix for PyGObject Error

If you encountered the PyGObject installation error, follow these steps:

## Problem

The error occurs because PyGObject requires system-level dependencies that must be installed via `apt-get` before installing Python packages.

## Solution

### Step 1: Install All Required System Dependencies

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
    libcairo2-dev \
    build-essential \
    python3-dev
```

**Key packages added:**
- `libgirepository1.0-dev` - Development files for GObject Introspection
- `gobject-introspection` - GObject Introspection framework
- `pkg-config` - Package configuration tool
- `libcairo2-dev` - Cairo graphics library development files

### Step 2: Install Python Dependencies

After installing system dependencies, install Python packages:

```bash
pip3 install -r requirements.txt
```

**Note:** PyGObject has been removed from `requirements.txt` because it should be installed via the system package `python3-gi` (which you installed in Step 1).

### Step 3: Verify Installation

Test that PyGObject is available:

```bash
python3 -c "import gi; print('PyGObject installed successfully')"
```

### Step 4: Install Application

```bash
pip3 install -e .
```

## Alternative: If You Still Have Issues

If you still encounter issues, you can try installing PyGObject via pip after system dependencies:

```bash
# Install system dependencies first (as above)
# Then install PyGObject via pip
pip3 install PyGObject
```

However, using the system package (`python3-gi`) is recommended as it's better integrated with the system.

## Verification

After installation, verify everything works:

```bash
# Test CLI
egnyte-cli --help

# Test GUI (if in graphical environment)
egnyte-desktop
```

