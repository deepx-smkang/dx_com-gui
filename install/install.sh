#!/bin/bash
# Installation script for DXCom GUI on Ubuntu/Debian systems

set -e  # Exit on error

echo "======================================"
echo "DXCom GUI Installation Script"
echo "======================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "Please do not run this script as root"
    echo "Run as: ./install.sh"
    exit 1
fi

# Detect script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_DIR="$SCRIPT_DIR/.."

# Step 1: Check Python version
echo "Step 1: Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

# Check if version is >= 3.8
REQUIRED_VERSION="3.8"
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "Error: Python 3.8 or higher is required"
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi
echo "✓ Python version OK"
echo ""

# Step 2: Install system dependencies
echo "Step 2: Installing system dependencies..."
echo "This step requires sudo privileges"

sudo apt update
sudo apt install -y \
    python3-venv \
    python3-pip \
    libgl1 \
    libxkbcommon-x11-0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libdbus-1-3 \
    libfontconfig1

echo "✓ System dependencies installed"
echo ""

# Step 3: Create virtual environment
echo "Step 3: Creating virtual environment..."
cd "$APP_DIR"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Step 4: Install Python dependencies
echo "Step 4: Installing Python dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Python dependencies installed"
echo ""

# Step 5: Install desktop integration
echo "Step 5: Installing desktop integration..."
DESKTOP_FILE="$SCRIPT_DIR/dxcom-gui.desktop"
LAUNCHER_SCRIPT="$SCRIPT_DIR/launcher.sh"

# Make launcher executable
chmod +x "$LAUNCHER_SCRIPT"

# Update desktop file with correct paths
TEMP_DESKTOP=$(mktemp)
sed "s|Exec=dxcom-gui|Exec=$LAUNCHER_SCRIPT|g" "$DESKTOP_FILE" > "$TEMP_DESKTOP"

# Install desktop entry
mkdir -p ~/.local/share/applications
cp "$TEMP_DESKTOP" ~/.local/share/applications/dxcom-gui.desktop
rm "$TEMP_DESKTOP"

# Install icon if exists
if [ -f "$APP_DIR/resources/deepx.png" ]; then
    mkdir -p ~/.local/share/pixmaps
    cp "$APP_DIR/resources/deepx.png" ~/.local/share/pixmaps/dxcom-gui.png
fi

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database ~/.local/share/applications
fi

echo "✓ Desktop integration installed"
echo ""

# Step 6: Create launcher symlink
echo "Step 6: Creating launcher symlink..."
mkdir -p ~/bin

# Create wrapper script in ~/bin
cat > ~/bin/dxcom-gui << EOF
#!/bin/bash
$LAUNCHER_SCRIPT "\$@"
EOF

chmod +x ~/bin/dxcom-gui

# Add ~/bin to PATH if not already there
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
    echo "Note: Please restart your terminal or run: source ~/.bashrc"
fi

echo "✓ Launcher symlink created"
echo ""

# Step 7: Run tests
echo "Step 7: Running tests..."
if python -m pytest tests/ -v; then
    echo "✓ All tests passed"
else
    echo "⚠ Some tests failed (non-critical)"
fi
echo ""

# Installation complete
echo "======================================"
echo "Installation Complete!"
echo "======================================"
echo ""
echo "You can now run DXCom GUI by:"
echo "  1. Searching for 'DXCom GUI' in your application menu"
echo "  2. Running: dxcom-gui"
echo "  3. Running: $LAUNCHER_SCRIPT"
echo ""
echo "Configuration directory: ~/.dxcom_gui"
echo ""
echo "For more information, see:"
echo "  - README.md: Project overview"
echo "  - docs/INSTALLATION.md: Detailed installation guide"
echo "  - docs/USER_GUIDE.md: Usage instructions"
echo ""
