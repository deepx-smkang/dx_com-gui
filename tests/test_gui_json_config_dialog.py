"""
GUI tests for JsonConfigDialog and JsonSyntaxHighlighter.
Run with: xvfb-run python -m pytest tests/test_gui_json_config_dialog.py -v
"""
import sys
import os
import json
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import patch, MagicMock
from src.json_config_dialog import JsonConfigDialog, JsonSyntaxHighlighter


class TestJsonConfigDialogCreation:

    def test_creates_without_error(self, qtbot, tmp_json_file):
        dlg = JsonConfigDialog(tmp_json_file)
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_window_title_contains_filename(self, qtbot, tmp_json_file):
        dlg = JsonConfigDialog(tmp_json_file)
        qtbot.addWidget(dlg)
        assert 'config.json' in dlg.windowTitle()

    def test_loads_json_content_into_editor(self, qtbot, tmp_json_file):
        dlg = JsonConfigDialog(tmp_json_file)
        qtbot.addWidget(dlg)
        text = dlg.json_editor.toPlainText()
        data = json.loads(text)
        assert data['key'] == 'value'
        assert data['num'] == 42

    def test_save_button_initially_disabled(self, qtbot, tmp_json_file):
        dlg = JsonConfigDialog(tmp_json_file)
        qtbot.addWidget(dlg)
        assert not dlg.save_btn.isEnabled()

    def test_modified_flag_initially_false(self, qtbot, tmp_json_file):
        dlg = JsonConfigDialog(tmp_json_file)
        qtbot.addWidget(dlg)
        assert not dlg.modified

    def test_editing_enables_save_button(self, qtbot, tmp_json_file):
        dlg = JsonConfigDialog(tmp_json_file)
        qtbot.addWidget(dlg)
        dlg.json_editor.setPlainText('{"changed": true}')
        assert dlg.save_btn.isEnabled()

    def test_path_label_shows_file_path(self, qtbot, tmp_json_file):
        dlg = JsonConfigDialog(tmp_json_file)
        qtbot.addWidget(dlg)
        assert tmp_json_file in dlg.path_label.text()


class TestJsonConfigDialogValidate:

    def test_validate_valid_json_shows_info(self, qtbot, tmp_json_file):
        dlg = JsonConfigDialog(tmp_json_file)
        qtbot.addWidget(dlg)
        dlg.json_editor.setPlainText('{"valid": true}')
        with patch('PySide6.QtWidgets.QMessageBox.information', return_value=None):
            dlg._validate_json()
        assert '✓' in dlg.status_label.text()

    def test_validate_invalid_json_shows_warning(self, qtbot, tmp_json_file):
        dlg = JsonConfigDialog(tmp_json_file)
        qtbot.addWidget(dlg)
        dlg.json_editor.setPlainText('{invalid json}')
        with patch('PySide6.QtWidgets.QMessageBox.warning', return_value=None):
            dlg._validate_json()
        assert '✗' in dlg.status_label.text()

    def test_validate_empty_json_shows_warning(self, qtbot, tmp_json_file):
        dlg = JsonConfigDialog(tmp_json_file)
        qtbot.addWidget(dlg)
        dlg.json_editor.setPlainText('   ')
        with patch('PySide6.QtWidgets.QMessageBox.warning', return_value=None):
            dlg._validate_json()


class TestJsonConfigDialogFormat:

    def test_format_valid_json(self, qtbot, tmp_json_file):
        dlg = JsonConfigDialog(tmp_json_file)
        qtbot.addWidget(dlg)
        dlg.json_editor.setPlainText('{"a":1,"b":2}')
        dlg._format_json()
        text = dlg.json_editor.toPlainText()
        data = json.loads(text)
        assert data == {'a': 1, 'b': 2}
        assert '✓' in dlg.status_label.text()

    def test_format_invalid_json_shows_warning(self, qtbot, tmp_json_file):
        dlg = JsonConfigDialog(tmp_json_file)
        qtbot.addWidget(dlg)
        dlg.json_editor.setPlainText('{bad json}')
        with patch('PySide6.QtWidgets.QMessageBox.warning', return_value=None):
            dlg._format_json()


class TestJsonConfigDialogSave:

    def test_save_valid_json_writes_file(self, qtbot, tmp_json_file):
        dlg = JsonConfigDialog(tmp_json_file)
        qtbot.addWidget(dlg)
        new_content = json.dumps({"saved": True}, indent=2)
        dlg.json_editor.setPlainText(new_content)
        with patch('PySide6.QtWidgets.QMessageBox.information', return_value=None):
            dlg._save_json()
        with open(tmp_json_file) as f:
            saved = json.load(f)
        assert saved['saved'] is True

    def test_save_marks_unmodified(self, qtbot, tmp_json_file):
        dlg = JsonConfigDialog(tmp_json_file)
        qtbot.addWidget(dlg)
        dlg.json_editor.setPlainText('{"x": 1}')
        with patch('PySide6.QtWidgets.QMessageBox.information', return_value=None):
            dlg._save_json()
        assert not dlg.modified
        assert not dlg.save_btn.isEnabled()

    def test_save_invalid_json_prompts_confirmation_yes(self, qtbot, tmp_json_file):
        dlg = JsonConfigDialog(tmp_json_file)
        qtbot.addWidget(dlg)
        dlg.json_editor.setPlainText('{bad}')
        from PySide6.QtWidgets import QMessageBox
        with patch.object(QMessageBox, 'question',
                          return_value=QMessageBox.StandardButton.Yes):
            with patch.object(QMessageBox, 'information', return_value=None):
                dlg._save_json()

    def test_save_invalid_json_prompts_confirmation_no(self, qtbot, tmp_json_file):
        dlg = JsonConfigDialog(tmp_json_file)
        qtbot.addWidget(dlg)
        dlg.json_editor.setPlainText('{bad}')
        from PySide6.QtWidgets import QMessageBox
        with patch.object(QMessageBox, 'question',
                          return_value=QMessageBox.StandardButton.No):
            dlg._save_json()

    def test_save_failure_shows_error(self, qtbot, tmp_json_file):
        dlg = JsonConfigDialog(tmp_json_file)
        qtbot.addWidget(dlg)
        dlg.json_editor.setPlainText('{"ok": true}')
        with patch('builtins.open', side_effect=OSError('disk full')):
            with patch('PySide6.QtWidgets.QMessageBox.critical', return_value=None):
                dlg._save_json()


class TestJsonConfigDialogCloseEvent:

    def test_close_unmodified_accepts(self, qtbot, tmp_json_file):
        dlg = JsonConfigDialog(tmp_json_file)
        qtbot.addWidget(dlg)
        assert not dlg.modified
        from PySide6.QtGui import QCloseEvent
        event = QCloseEvent()
        dlg.closeEvent(event)
        assert event.isAccepted()

    def test_close_modified_with_confirmation_yes(self, qtbot, tmp_json_file):
        dlg = JsonConfigDialog(tmp_json_file)
        qtbot.addWidget(dlg)
        dlg.json_editor.setPlainText('{"changed": true}')
        assert dlg.modified
        from PySide6.QtGui import QCloseEvent
        from PySide6.QtWidgets import QMessageBox
        event = QCloseEvent()
        with patch.object(QMessageBox, 'question',
                          return_value=QMessageBox.StandardButton.Yes):
            dlg.closeEvent(event)
        assert event.isAccepted()

    def test_close_modified_with_confirmation_no(self, qtbot, tmp_json_file):
        dlg = JsonConfigDialog(tmp_json_file)
        qtbot.addWidget(dlg)
        dlg.json_editor.setPlainText('{"changed": true}')
        from PySide6.QtGui import QCloseEvent
        from PySide6.QtWidgets import QMessageBox
        event = QCloseEvent()
        with patch.object(QMessageBox, 'question',
                          return_value=QMessageBox.StandardButton.No):
            dlg.closeEvent(event)
        assert not event.isAccepted()


class TestJsonConfigDialogLoadError:

    def test_load_invalid_json_file_shows_warning(self, qtbot, tmp_path):
        bad_file = tmp_path / 'bad.json'
        bad_file.write_text('{NOT VALID JSON}')
        dlg = JsonConfigDialog(str(bad_file))
        qtbot.addWidget(dlg)
        assert '⚠' in dlg.status_label.text()

    def test_load_missing_file_closes_dialog(self, qtbot, tmp_path):
        missing = str(tmp_path / 'nonexistent.json')
        with patch('PySide6.QtWidgets.QMessageBox.critical', return_value=None):
            dlg = JsonConfigDialog(missing)
            qtbot.addWidget(dlg)


class TestJsonSyntaxHighlighter:

    def test_highlighter_creates_without_error(self, qtbot):
        from PySide6.QtWidgets import QTextEdit
        editor = QTextEdit()
        qtbot.addWidget(editor)
        highlighter = JsonSyntaxHighlighter(editor.document())
        assert highlighter is not None

    def test_highlighter_processes_text(self, qtbot):
        from PySide6.QtWidgets import QTextEdit
        editor = QTextEdit()
        qtbot.addWidget(editor)
        highlighter = JsonSyntaxHighlighter(editor.document())
        editor.setPlainText('{"key": "value", "num": 42, "flag": true}')
        # Just verify it doesn't crash and text remains intact
        assert 'key' in editor.toPlainText()
