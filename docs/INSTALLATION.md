# Installation Guide - DXCom GUI

Complete guide for installing and configuring the DXCom GUI application.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
3. [DXCom Compiler Setup](#dxcom-compiler-setup)
4. [Desktop Integration](#desktop-integration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

#### Operating System
- **Ubuntu**: 18.04 LTS or newer (recommended: 20.04 or 22.04)
- **Other Linux**: Debian 10+, Fedora 32+, or equivalent distributions
- **Display Server**: X11 or Wayland

#### Hardware
- **CPU**: x86_64 processor
- **RAM**: Minimum 512 MB, recommended 1 GB
- **Disk**: 50 MB for application, plus space for models
- **Display**: 1024x768 minimum resolution

### Software Dependencies

#### Python
```bash
# Check Python version (requires 3.8+)
python3 --version

# If Python not installed or too old
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

#### System Libraries (Ubuntu/Debian)
```bash
# Install Qt dependencies
sudo apt install -y \
    libgl1-mesa-glx \
    libxkbcommon-x11-0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-xfixes0 \
    libdbus-1-3

# Install additional dependencies
sudo apt install -y \
    libfontconfig1 \
    libx11-xcb1 \
    libegl1-mesa \
    libglib2.0-0
```

#### System Libraries (Fedora/RHEL)
```bash
# Install Qt dependencies
sudo dnf install -y \
    mesa-libGL \
    libxkbcommon-x11 \
    xcb-util-image \
    xcb-util-keysyms \
    xcb-util-renderutil \
    xcb-util-wm \
    dbus-libs

# Install additional dependencies
sudo dnf install -y \
    fontconfig \
    libX11-xcb \
    mesa-libEGL \
    glib2
```

## Installation Methods

### Method 1: From Source (Recommended for Development)

#### Step 1: Clone Repository
```bash
# Clone the project
git clone https://github.com/yourusername/dx_com_gui.git
cd dx_com_gui

# Or download and extract ZIP
wget https://github.com/yourusername/dx_com_gui/archive/main.zip
unzip main.zip
cd dx_com_gui-main
```

#### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Verify activation (should show .venv path)
which python
```

#### Step 3: Install Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify installation
pip list | grep PySide6
```

#### Step 4: Run Application
```bash
# From project directory with venv activated
python main.py
```

### Method 2: Using pip (When Published)

```bash
# Create virtual environment (recommended)
python3 -m venv ~/.venvs/dxcom-gui
source ~/.venvs/dxcom-gui/bin/activate

# Install from PyPI
pip install dxcom-gui

# Run application
dxcom-gui
```

### Method 3: System-Wide Installation

```bash
# Install system-wide (requires sudo)
sudo pip3 install dxcom-gui

# Or install from source
cd dx_com_gui
sudo python3 setup.py install

# Run application
dxcom-gui
```

### Method 4: Using setup.py

```bash
# From project directory
cd dx_com_gui

# Install in development mode
pip install -e .

# Or regular installation
pip install .

# Run application
dxcom-gui
```

## DXCom Compiler Setup

The DXCom GUI requires the DXCom compiler to be installed separately.

### Installation Locations

The application automatically searches these locations:

1. Environment variable: `$DXCOM_PATH`
2. `/opt/dxcom/bin/dxcom`
3. `/usr/local/bin/dxcom`
4. `/usr/bin/dxcom`
5. `~/dxcom/bin/dxcom`
6. System PATH directories

### Installing DXCom Compiler

```bash
# Example: Install to /opt/dxcom
sudo mkdir -p /opt/dxcom/bin
sudo cp /path/to/dxcom /opt/dxcom/bin/
sudo chmod +x /opt/dxcom/bin/dxcom

# Add to PATH (add to ~/.bashrc for persistence)
export PATH="/opt/dxcom/bin:$PATH"
```

### Setting DXCOM_PATH Environment Variable

```bash
# Temporary (current session only)
export DXCOM_PATH=/path/to/dxcom

# Permanent (add to ~/.bashrc or ~/.profile)
echo 'export DXCOM_PATH=/path/to/dxcom' >> ~/.bashrc
source ~/.bashrc
```

### Verifying DXCom Installation

```bash
# Check if dxcom is found
which dxcom

# Or check environment variable
echo $DXCOM_PATH

# Test dxcom execution
dxcom --version
```

## Desktop Integration

### Install Desktop Entry (Linux)

```bash
# From project directory
cd dx_com_gui

# Copy desktop entry
sudo cp install/dxcom-gui.desktop /usr/share/applications/

# Copy icon
sudo mkdir -p /usr/share/pixmaps
sudo cp resources/icon.png /usr/share/pixmaps/dxcom-gui.png

# Update desktop database
sudo update-desktop-database

# The application now appears in application menu
```

### Create Custom Launcher Script

```bash
# Create launcher script
cat > ~/bin/dxcom-gui << 'EOF'
#!/bin/bash
cd /path/to/dx_com_gui
source .venv/bin/activate
python main.py "$@"
EOF

# Make executable
chmod +x ~/bin/dxcom-gui

# Ensure ~/bin is in PATH
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Now you can run from anywhere
dxcom-gui
```

### Creating Application Shortcut

Edit the desktop entry file as needed:

```bash
# Edit desktop entry
nano ~/.local/share/applications/dxcom-gui.desktop
```

Example desktop entry:
```ini
[Desktop Entry]
Name=DXCom GUI
Comment=ONNX to DXNN Model Compiler
Exec=/path/to/dx_com_gui/.venv/bin/python /path/to/dx_com_gui/main.py
Icon=/path/to/dx_com_gui/resources/icon.png
Terminal=false
Type=Application
Categories=Development;Science;
```

## Verification

### Verify Installation

```bash
# Check Python installation
python3 --version

# Check PySide6 installation
python3 -c "from PySide6.QtWidgets import QApplication; print('PySide6 OK')"

# Check application can be imported
cd dx_com_gui
python3 -c "from src.main_window import MainWindow; print('Import OK')"

# Run application
python3 main.py
```

### Run Tests

```bash
# Install pytest (if not already installed)
pip install pytest

# Run all tests
cd dx_com_gui
python -m pytest tests/

# Expected output: All tests passing
```

### Check DXCom Detection

```bash
# Run detection test
cd dx_com_gui
python3 -c "
from src.dxcom_detector import DXComDetector
detector = DXComDetector()
result = detector.detect_dxcom()
print(f'DXCom found: {result[\"found\"]}')
if result['found']:
    print(f'Path: {result[\"paths\"][0]}')
    print(f'Version: {result.get(\"version\", \"unknown\")}')
"
```

## Troubleshooting

### Common Installation Issues

#### Issue: Python version too old
```bash
# Error: Python 3.6 or 3.7
# Solution: Install Python 3.8+
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev
```

#### Issue: PySide6 installation fails
```bash
# Error: Failed building wheel for PySide6
# Solution: Install build dependencies
sudo apt install -y python3-dev build-essential

# Try installing from conda (alternative)
conda install -c conda-forge pyside6
```

#### Issue: Qt platform plugin error
```bash
# Error: qt.qpa.plugin: Could not load the Qt platform plugin "xcb"
# Solution: Install Qt dependencies
sudo apt install -y libxcb-xinerama0 libxcb-cursor0

# Or set platform explicitly
export QT_QPA_PLATFORM=xcb
```

#### Issue: Display not available
```bash
# Error: cannot connect to X server
# Solution: Set DISPLAY variable
export DISPLAY=:0

# Or if using SSH
ssh -X user@host
```

#### Issue: Permission denied for DXCom
```bash
# Error: Permission denied: /opt/dxcom/bin/dxcom
# Solution: Make executable
sudo chmod +x /opt/dxcom/bin/dxcom

# Or change ownership
sudo chown $USER /opt/dxcom/bin/dxcom
```

### Uninstallation

#### Remove Application
```bash
# If installed with pip
pip uninstall dxcom-gui

# If installed system-wide
sudo pip3 uninstall dxcom-gui
```

#### Remove Configuration Files
```bash
# Remove user settings
rm -rf ~/.dxcom_gui

# Remove desktop integration
sudo rm /usr/share/applications/dxcom-gui.desktop
sudo rm /usr/share/pixmaps/dxcom-gui.png
sudo update-desktop-database
```

#### Remove Virtual Environment
```bash
# From project directory
rm -rf .venv

# Or if installed elsewhere
rm -rf ~/.venvs/dxcom-gui
```

### Getting Additional Help

- **Documentation**: See `docs/user_guide.md` for usage instructions
- **GitHub Issues**: https://github.com/yourusername/dx_com_gui/issues
- **Email Support**: support@example.com

## Next Steps

After successful installation:

1. **Read the User Guide**: See `docs/user_guide.md`
2. **Configure Settings**: Launch app and open Settings dialog
3. **Set DXCom Path**: Ensure compiler is detected
4. **Test with Sample Model**: Try compiling a simple ONNX model
5. **Explore Features**: Try presets, themes, and advanced options

---

**Installation Complete!** You're ready to start compiling ONNX models.
