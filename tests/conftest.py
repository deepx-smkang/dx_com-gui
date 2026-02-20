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


@pytest.fixture(autouse=True)
def suppress_unsaved_changes_dialog(monkeypatch):
    """Prevent 'Unsaved changes' QMessageBox from popping during qtbot cleanup.

    setPlainText() fires textChanged → modified/has_unsaved_changes = True.
    When qtbot tears down each test it calls dlg.close() → closeEvent fires the
    real QMessageBox.question if no mock is active.  This fixture returns Yes
    (discard changes) by default so cleanup is always silent.

    Tests that explicitly mock QMessageBox.question inside a ``with patch.object``
    block are unaffected — the context-manager mock takes precedence inside the
    block; once the block exits, this fixture's version is restored for cleanup.
    """
    from PySide6.QtWidgets import QMessageBox
    monkeypatch.setattr(
        QMessageBox,
        'question',
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
