#!/bin/bash
# DXCom GUI Launcher Script
# Activates virtual environment and launches the application

# Determine script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_DIR="$SCRIPT_DIR/.."

# Activate virtual environment if it exists
if [ -f "$APP_DIR/.venv/bin/activate" ]; then
    source "$APP_DIR/.venv/bin/activate"
elif [ -f "$HOME/.venvs/dxcom-gui/bin/activate" ]; then
    source "$HOME/.venvs/dxcom-gui/bin/activate"
fi

# Set up environment
export PYTHONPATH="$APP_DIR:$PYTHONPATH"

# Change to app directory
cd "$APP_DIR"

# Launch application
python3 main.py "$@"
