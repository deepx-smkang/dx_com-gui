# Installation Guide

## Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 18.04+)
- **Python**: 3.8 or higher
- **Display**: X11 or Wayland

### System Libraries (Ubuntu/Debian)

```bash
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
```

### DXCom Compiler

The DXCom compiler must be installed separately and available on your system `PATH`:

```bash
# Verify it is accessible
which dxcom
dxcom --version
```

To use a compiler at a non-standard path, pass `--dxcom-path` at launch (see Usage).

---

## Installation

### Method 1: pip install (Recommended)

```bash
git clone https://github.com/DEEPX-AI/dx_com-gui.git
cd dx_com-gui

python3 -m venv .venv
source .venv/bin/activate

pip install .

# Launch
dxcom-gui
```

### Method 2: Run Without Installing

```bash
cd dx_com-gui
pip install PySide6
python main.py
```

---

## Verification

```bash
# Check PySide6
python3 -c "from PySide6.QtWidgets import QApplication; print('PySide6 OK')"

# Run tests
cd dx_com-gui
pip install -r tests/requirements.txt
python -m pytest tests/ -v
```

---

## Troubleshooting

**Qt platform plugin error**
```bash
sudo apt install libxcb-xinerama0 libxcb-cursor0
# or
export QT_QPA_PLATFORM=xcb
```

**PySide6 installation fails**
```bash
sudo apt install python3-dev build-essential
pip install PySide6
```

**Python version too old**
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.10 python3.10-venv
```

---

## Uninstallation

```bash
pip uninstall dxcom-gui
rm -rf ~/.dxcom_gui
```
