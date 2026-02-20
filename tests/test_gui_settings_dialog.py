"""
GUI tests for SettingsDialog.
Run with: xvfb-run python -m pytest tests/test_gui_settings_dialog.py -v
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QDialogButtonBox
from src.settings_dialog import SettingsDialog


class TestSettingsDialogCreation:
    """Test that SettingsDialog creates and populates correctly."""

    def test_dialog_creates_without_error(self, qtbot, tmp_settings):
        dlg = SettingsDialog(tmp_settings)
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_window_title(self, qtbot, tmp_settings):
        dlg = SettingsDialog(tmp_settings)
        qtbot.addWidget(dlg)
        assert dlg.windowTitle() == "Settings"

    def test_initial_theme_combo_reflects_settings(self, qtbot, tmp_settings):
        tmp_settings.set('theme', 'dark')
        dlg = SettingsDialog(tmp_settings)
        qtbot.addWidget(dlg)
        assert dlg.theme_combo.currentText().lower() == 'dark'

    def test_initial_theme_combo_light(self, qtbot, tmp_settings):
        tmp_settings.set('theme', 'light')
        dlg = SettingsDialog(tmp_settings)
        qtbot.addWidget(dlg)
        assert dlg.theme_combo.currentText().lower() == 'light'

    def test_initial_max_recent_spinbox(self, qtbot, tmp_settings):
        tmp_settings.set('max_recent_files', 7)
        dlg = SettingsDialog(tmp_settings)
        qtbot.addWidget(dlg)
        assert dlg.max_recent_spinbox.value() == 7

    def test_initial_default_input_path(self, qtbot, tmp_settings):
        tmp_settings.set('default_input_path', '/some/path')
        dlg = SettingsDialog(tmp_settings)
        qtbot.addWidget(dlg)
        assert dlg.default_input_field.text() == '/some/path'

    def test_initial_auto_save_checkbox(self, qtbot, tmp_settings):
        tmp_settings.set('auto_save_preset', True)
        dlg = SettingsDialog(tmp_settings)
        qtbot.addWidget(dlg)
        assert dlg.auto_save_checkbox.isChecked()

    def test_initial_show_tooltips_checkbox(self, qtbot, tmp_settings):
        tmp_settings.set('show_tooltips', False)
        dlg = SettingsDialog(tmp_settings)
        qtbot.addWidget(dlg)
        assert not dlg.show_tooltips_checkbox.isChecked()

    def test_initial_auto_scroll_checkbox(self, qtbot, tmp_settings):
        tmp_settings.set('auto_scroll_logs', True)
        dlg = SettingsDialog(tmp_settings)
        qtbot.addWidget(dlg)
        assert dlg.auto_scroll_checkbox.isChecked()

    def test_initial_confirm_overwrite_checkbox(self, qtbot, tmp_settings):
        tmp_settings.set('confirm_overwrite', False)
        dlg = SettingsDialog(tmp_settings)
        qtbot.addWidget(dlg)
        assert not dlg.confirm_overwrite_checkbox.isChecked()


class TestSettingsDialogAccept:
    """Test saving settings via accept."""

    def test_accept_saves_theme(self, qtbot, tmp_settings):
        dlg = SettingsDialog(tmp_settings)
        qtbot.addWidget(dlg)
        dlg.theme_combo.setCurrentText('Dark')
        dlg._on_accept()
        assert tmp_settings.get('theme') == 'dark'

    def test_accept_saves_max_recent(self, qtbot, tmp_settings):
        dlg = SettingsDialog(tmp_settings)
        qtbot.addWidget(dlg)
        dlg.max_recent_spinbox.setValue(5)
        dlg._on_accept()
        assert tmp_settings.get('max_recent_files') == 5

    def test_accept_saves_default_input_path(self, qtbot, tmp_settings):
        dlg = SettingsDialog(tmp_settings)
        qtbot.addWidget(dlg)
        dlg.default_input_field.setText('/new/input/path')
        dlg._on_accept()
        assert tmp_settings.get('default_input_path') == '/new/input/path'

    def test_accept_saves_auto_save(self, qtbot, tmp_settings):
        dlg = SettingsDialog(tmp_settings)
        qtbot.addWidget(dlg)
        dlg.auto_save_checkbox.setChecked(True)
        dlg._on_accept()
        assert tmp_settings.get('auto_save_preset') is True

    def test_accept_saves_auto_scroll(self, qtbot, tmp_settings):
        dlg = SettingsDialog(tmp_settings)
        qtbot.addWidget(dlg)
        dlg.auto_scroll_checkbox.setChecked(False)
        dlg._on_accept()
        assert tmp_settings.get('auto_scroll_logs') is False

    def test_accept_saves_confirm_overwrite(self, qtbot, tmp_settings):
        dlg = SettingsDialog(tmp_settings)
        qtbot.addWidget(dlg)
        dlg.confirm_overwrite_checkbox.setChecked(False)
        dlg._on_accept()
        assert tmp_settings.get('confirm_overwrite') is False

    def test_accept_saves_default_output_path(self, qtbot, tmp_settings):
        dlg = SettingsDialog(tmp_settings)
        qtbot.addWidget(dlg)
        dlg.default_output_field.setText('/new/output')
        dlg._on_accept()
        assert tmp_settings.get('default_output_path') == '/new/output'

    def test_accept_saves_json_path(self, qtbot, tmp_settings):
        dlg = SettingsDialog(tmp_settings)
        qtbot.addWidget(dlg)
        dlg.default_json_field.setText('/configs')
        dlg._on_accept()
        assert tmp_settings.get('default_json_path') == '/configs'

    def test_accept_saves_dataset_path(self, qtbot, tmp_settings):
        dlg = SettingsDialog(tmp_settings)
        qtbot.addWidget(dlg)
        dlg.default_dataset_field.setText('/datasets')
        dlg._on_accept()
        assert tmp_settings.get('default_dataset_path') == '/datasets'


class TestSettingsDialogRestoreDefaults:
    """Test restore defaults functionality."""

    def test_restore_defaults_resets_theme(self, qtbot, tmp_settings):
        tmp_settings.set('theme', 'dark')
        dlg = SettingsDialog(tmp_settings)
        qtbot.addWidget(dlg)
        dlg._on_restore_defaults()
        assert dlg.theme_combo.currentText().lower() == 'light'

    def test_restore_defaults_resets_max_recent(self, qtbot, tmp_settings):
        tmp_settings.set('max_recent_files', 3)
        dlg = SettingsDialog(tmp_settings)
        qtbot.addWidget(dlg)
        dlg._on_restore_defaults()
        assert dlg.max_recent_spinbox.value() == 10


class TestSettingsDialogClearRecent:
    """Test clearing recent files from the dialog."""

    def test_clear_recent_files(self, qtbot, tmp_settings):
        tmp_settings.recent_files = ['/a.onnx', '/b.onnx']
        dlg = SettingsDialog(tmp_settings)
        qtbot.addWidget(dlg)
        dlg._on_clear_recent_files()
        assert tmp_settings.get_recent_files() == []
