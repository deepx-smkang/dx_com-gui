"""
Shared pytest fixtures for DXCom GUI tests.
GUI tests require a display; run with: xvfb-run pytest tests/
"""
import os
import sys
import shutil
import tempfile
from pathlib import Path

import pytest

# Ensure src package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def tmp_settings(tmp_path):
    """Return a SettingsManager backed by a temp dir (isolated from user data)."""
    from src.settings_manager import SettingsManager
    mgr = SettingsManager()
    mgr.settings_dir = tmp_path / '.dxcom_gui'
    mgr.settings_file = mgr.settings_dir / 'settings.json'
    mgr.recent_files_file = mgr.settings_dir / 'recent_files.json'
    mgr._ensure_settings_dir()
    mgr.settings = SettingsManager.DEFAULT_SETTINGS.copy()
    mgr.recent_files = []
    return mgr


@pytest.fixture
def tmp_json_file(tmp_path):
    """Return a path to a valid temp JSON file."""
    import json
    p = tmp_path / 'config.json'
    p.write_text(json.dumps({"key": "value", "num": 42}, indent=2))
    return str(p)
