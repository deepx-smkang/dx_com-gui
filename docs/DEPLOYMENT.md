# Deployment Guide - DXCom GUI

Complete guide for deploying the DXCom GUI application to end users.

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Deployment Methods](#deployment-methods)
4. [Target Platform Testing](#target-platform-testing)
5. [Distribution Strategies](#distribution-strategies)
6. [Post-Deployment Support](#post-deployment-support)

## Deployment Overview

### Deployment Architecture

```
┌─────────────────────────────────────────────────┐
│  DXCom GUI Application Package                  │
├─────────────────────────────────────────────────┤
│  • Python source code (src/)                    │
│  • Entry point script (main.py)                 │
│  • Dependencies (PySide6)                       │
│  • Resources (icons, themes)                    │
│  • Documentation (README, guides)               │
│  • Installation scripts                         │
└─────────────────────────────────────────────────┘
         │
         ├─> Local Installation (virtualenv)
         ├─> System Installation (pip)
         ├─> Desktop Integration (.desktop file)
         └─> Binary Package (.deb, .rpm)
```

### Supported Platforms

**Primary Support:**
- Ubuntu 18.04 LTS (Bionic Beaver)
- Ubuntu 20.04 LTS (Focal Fossa)
- Ubuntu 22.04 LTS (Jammy Jellyfish)

**Secondary Support:**
- Debian 10 (Buster) and newer
- Linux Mint 19+ (Ubuntu-based)
- Pop!_OS 20.04+
- Elementary OS 5.1+

**Compatibility:**
- Any Linux distribution with Python 3.8+ and Qt 6 support
- X11 or Wayland display server

## Pre-Deployment Checklist

### Code Quality

```bash
# Run all tests
cd dx_com_gui
python -m pytest tests/ -v --cov=src

# Check code style
flake8 src/

# Type checking
mypy src/

# Format check
black --check src/
```

### Documentation Review

- [ ] README.md is complete and accurate
- [ ] INSTALLATION.md covers all platforms
- [ ] USER_GUIDE.md is comprehensive
- [ ] API documentation is up to date
- [ ] CHANGELOG.md includes all changes
- [ ] License information is correct

### Functional Testing

- [ ] Application launches without errors
- [ ] All UI elements render correctly
- [ ] File selection and browsing works
- [ ] Compilation process completes successfully
- [ ] Error handling works as expected
- [ ] Settings persistence works
- [ ] Theme switching works
- [ ] Keyboard shortcuts function
- [ ] Help/About dialogs display correctly

### Performance Testing

- [ ] Startup time is acceptable (<3 seconds)
- [ ] UI remains responsive during compilation
- [ ] Memory usage is reasonable (<200 MB idle)
- [ ] No memory leaks during extended use
- [ ] Progress updates are smooth

### Integration Testing

- [ ] DXCom compiler detection works
- [ ] Environment validation runs correctly
- [ ] Sample ONNX models compile successfully
- [ ] Output files are generated correctly
- [ ] Recent files list populates

### Security Review

- [ ] No hardcoded credentials or secrets
- [ ] File paths are validated
- [ ] User input is sanitized
- [ ] External processes are safely spawned
- [ ] File permissions are checked

## Deployment Methods

### Method 1: Source Distribution

**For developers and advanced users**

```bash
# Create source distribution
python setup.py sdist

# Package is created in dist/
# dist/dxcom-gui-1.0.0.tar.gz

# Users install with:
pip install dxcom-gui-1.0.0.tar.gz
```

**Pros:**
- Simple to create
- Works on any platform with Python
- Users can inspect source

**Cons:**
- Requires Python environment
- Dependencies must be installed
- No desktop integration by default

### Method 2: Wheel Distribution

**For easier installation**

```bash
# Create wheel package
python setup.py bdist_wheel

# Package is created in dist/
# dist/dxcom_gui-1.0.0-py3-none-any.whl

# Users install with:
pip install dxcom_gui-1.0.0-py3-none-any.whl
```

**Pros:**
- Faster installation than source
- Standard Python package format
- Works with pip

**Cons:**
- Still requires Python environment
- No system integration

### Method 3: Installation Script

**For end users (recommended)**

Provide `install/install.sh`:

```bash
# Users run:
git clone https://github.com/yourusername/dx_com_gui.git
cd dx_com_gui
./install/install.sh
```

**What it does:**
1. Checks system requirements
2. Installs system dependencies (with sudo)
3. Creates virtual environment
4. Installs Python dependencies
5. Sets up desktop integration
6. Creates launcher script
7. Runs verification tests

**Pros:**
- One-command installation
- Handles all dependencies
- Desktop integration included
- User-friendly

**Cons:**
- Requires internet connection
- Requires sudo for system packages

### Method 4: Debian Package (.deb)

**For Ubuntu/Debian users**

Create `.deb` package:

```bash
# Install packaging tools
sudo apt install dh-make devscripts

# Create package structure
mkdir -p dxcom-gui-1.0.0/DEBIAN
mkdir -p dxcom-gui-1.0.0/opt/dxcom-gui
mkdir -p dxcom-gui-1.0.0/usr/share/applications
mkdir -p dxcom-gui-1.0.0/usr/share/pixmaps
mkdir -p dxcom-gui-1.0.0/usr/bin

# Copy files
cp -r src main.py requirements.txt dxcom-gui-1.0.0/opt/dxcom-gui/
cp install/dxcom-gui.desktop dxcom-gui-1.0.0/usr/share/applications/
cp resources/icon.png dxcom-gui-1.0.0/usr/share/pixmaps/dxcom-gui.png

# Create launcher
cat > dxcom-gui-1.0.0/usr/bin/dxcom-gui << 'EOF'
#!/bin/bash
cd /opt/dxcom-gui
python3 main.py "$@"
EOF
chmod +x dxcom-gui-1.0.0/usr/bin/dxcom-gui

# Create control file
cat > dxcom-gui-1.0.0/DEBIAN/control << 'EOF'
Package: dxcom-gui
Version: 1.0.0
Section: science
Priority: optional
Architecture: all
Depends: python3 (>= 3.8), python3-pip, libgl1-mesa-glx, libxcb-icccm4
Maintainer: Your Name <contact@example.com>
Description: ONNX to DXNN Model Compiler GUI
 Professional desktop application for compiling ONNX models
 to DXNN format using the DXCom compiler.
EOF

# Create postinst script
cat > dxcom-gui-1.0.0/DEBIAN/postinst << 'EOF'
#!/bin/bash
cd /opt/dxcom-gui
pip3 install -r requirements.txt --target /opt/dxcom-gui/lib
update-desktop-database
EOF
chmod +x dxcom-gui-1.0.0/DEBIAN/postinst

# Build package
dpkg-deb --build dxcom-gui-1.0.0

# Users install with:
sudo dpkg -i dxcom-gui-1.0.0.deb
sudo apt install -f  # Fix dependencies
```

**Pros:**
- Native package manager integration
- Automatic dependency resolution
- Easy installation and removal
- Professional deployment

**Cons:**
- Platform-specific
- More complex to create
- Requires package signing for repos

### Method 5: AppImage

**For maximum compatibility**

```bash
# Install appimagetool
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

# Create AppDir structure
mkdir -p DXComGUI.AppDir/usr/{bin,lib,share}

# Copy application
cp -r src main.py DXComGUI.AppDir/usr/lib/dxcom-gui/

# Create AppRun
cat > DXComGUI.AppDir/AppRun << 'EOF'
#!/bin/bash
APPDIR="$(dirname "$(readlink -f "${0}")")"
export PYTHONPATH="$APPDIR/usr/lib:$PYTHONPATH"
cd "$APPDIR/usr/lib/dxcom-gui"
python3 main.py "$@"
EOF
chmod +x DXComGUI.AppDir/AppRun

# Copy icon and desktop file
cp resources/icon.png DXComGUI.AppDir/dxcom-gui.png
cp install/dxcom-gui.desktop DXComGUI.AppDir/

# Build AppImage
./appimagetool-x86_64.AppImage DXComGUI.AppDir

# Users run:
chmod +x DXCom_GUI-1.0.0-x86_64.AppImage
./DXCom_GUI-1.0.0-x86_64.AppImage
```

**Pros:**
- Single file distribution
- No installation required
- Works on any Linux distribution
- Portable

**Cons:**
- Larger file size
- Requires FUSE
- May have permission issues

## Target Platform Testing

### Ubuntu 18.04 LTS Testing

```bash
# Spin up Ubuntu 18.04 container or VM
docker run -it ubuntu:18.04 bash

# Or use multipass
multipass launch 18.04 --name dxcom-test

# Install and test
apt update && apt install -y git python3 python3-pip
git clone https://github.com/yourusername/dx_com_gui.git
cd dx_com_gui
./install/install.sh

# Run tests
python3 -m pytest tests/

# Manual testing
python3 main.py
```

**Test checklist:**
- [ ] Python 3.8 available
- [ ] PySide6 installs correctly
- [ ] Qt libraries compatible
- [ ] Application launches
- [ ] All features work
- [ ] No deprecated API usage

### Ubuntu 20.04 LTS Testing

```bash
# Similar to 18.04 but with:
multipass launch 20.04 --name dxcom-test

# Test Python 3.8+ features
# Test newer Qt features
# Verify Wayland compatibility
```

### Ubuntu 22.04 LTS Testing

```bash
multipass launch 22.04 --name dxcom-test

# Test with Python 3.10
# Test with latest PySide6
# Verify Wayland default behavior
# Test modern Qt features
```

### Automated Testing Script

```bash
#!/bin/bash
# test_all_platforms.sh

PLATFORMS=("18.04" "20.04" "22.04")

for platform in "${PLATFORMS[@]}"; do
    echo "Testing on Ubuntu $platform..."
    
    # Create container
    docker run -d --name "dxcom-test-$platform" ubuntu:$platform sleep infinity
    
    # Install app
    docker exec "dxcom-test-$platform" bash -c "
        apt update && apt install -y git python3 python3-pip
        git clone /app /test-app
        cd /test-app
        ./install/install.sh
        python3 -m pytest tests/
    "
    
    # Cleanup
    docker stop "dxcom-test-$platform"
    docker rm "dxcom-test-$platform"
    
    echo "Ubuntu $platform testing complete"
done
```

## Distribution Strategies

### Strategy 1: GitHub Releases

1. **Create Release on GitHub:**
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

2. **Upload Artifacts:**
   - Source tarball
   - Wheel package
   - Installation script
   - Documentation PDF

3. **Release Notes:**
   - Feature highlights
   - Bug fixes
   - Known issues
   - Installation instructions

### Strategy 2: PyPI Distribution

```bash
# Install tools
pip install twine

# Build distributions
python setup.py sdist bdist_wheel

# Check packages
twine check dist/*

# Upload to PyPI
twine upload dist/*

# Users install with:
pip install dxcom-gui
```

### Strategy 3: PPA (Personal Package Archive)

For Ubuntu users:

```bash
# Create PPA on Launchpad
# Build .deb package
# Upload to PPA

# Users add PPA and install:
sudo add-apt-repository ppa:username/dxcom-gui
sudo apt update
sudo apt install dxcom-gui
```

### Strategy 4: Direct Download

Host on website:

```
https://example.com/downloads/
  ├── dxcom-gui-1.0.0.tar.gz
  ├── dxcom-gui-1.0.0-py3-none-any.whl
  ├── dxcom-gui_1.0.0_all.deb
  ├── DXCom_GUI-1.0.0-x86_64.AppImage
  └── install.sh
```

## Post-Deployment Support

### User Support Channels

1. **Documentation**
   - README.md
   - Installation guide
   - User guide
   - FAQ

2. **Issue Tracking**
   - GitHub Issues for bugs
   - Feature requests
   - Questions

3. **Community Support**
   - Discussion forum
   - Mailing list
   - Chat (Slack/Discord)

### Monitoring & Analytics

**Installation Analytics:**
- Download counts
- Platform distribution
- Version adoption rate

**Error Reporting:**
- Automatic crash reports (opt-in)
- Error logs
- Usage statistics

### Update Strategy

**Version Scheme:**
- Major.Minor.Patch (1.0.0)
- Major: Breaking changes
- Minor: New features
- Patch: Bug fixes

**Update Distribution:**
```bash
# In-app update checker
# Notify users of new versions
# Direct download links
# Change log display
```

**Backward Compatibility:**
- Maintain settings compatibility
- Deprecation warnings
- Migration scripts

### Support Documentation

Create support matrix:

| Platform | Python | Qt | Status | Notes |
|----------|--------|-----|--------|-------|
| Ubuntu 18.04 | 3.8-3.9 | 6.4+ | ✓ Supported | LTS |
| Ubuntu 20.04 | 3.8-3.10 | 6.4+ | ✓ Supported | LTS |
| Ubuntu 22.04 | 3.10+ | 6.4+ | ✓ Supported | LTS |
| Debian 10 | 3.8+ | 6.4+ | ⚠ Partial | Community |
| Other Linux | 3.8+ | 6.4+ | ⚠ Experimental | Best effort |

## Deployment Checklist

### Pre-Release

- [ ] All tests passing
- [ ] Documentation complete
- [ ] Version number updated
- [ ] CHANGELOG.md updated
- [ ] No debug code or logs
- [ ] Security audit complete

### Release

- [ ] Git tag created
- [ ] GitHub release published
- [ ] Packages uploaded
- [ ] PyPI package published
- [ ] Documentation deployed
- [ ] Announcement posted

### Post-Release

- [ ] Monitor for issues
- [ ] Respond to user feedback
- [ ] Track installation metrics
- [ ] Plan next version

---

**Deployment Ready!** Follow this guide for successful distribution.
