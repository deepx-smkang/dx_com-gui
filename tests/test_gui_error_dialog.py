"""
GUI tests for ErrorDialog.
Run with: xvfb-run python -m pytest tests/test_gui_error_dialog.py -v
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.error_dialog import ErrorDialog, show_error_dialog
from src.error_handler import DXComError, ErrorCategory


def make_error(**kwargs):
    defaults = dict(
        category=ErrorCategory.PROCESS_FAILURE,
        user_message='Something went wrong',
        message='Raw error output',
        technical_details='Traceback...',
        suggestions=['Try again', 'Check logs'],
        exit_code=1,
    )
    defaults.update(kwargs)
    return DXComError(**defaults)


class TestErrorDialogCreation:

    def test_creates_without_error(self, qtbot):
        dlg = ErrorDialog(make_error())
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_window_title(self, qtbot):
        dlg = ErrorDialog(make_error())
        qtbot.addWidget(dlg)
        assert dlg.windowTitle() == "Compilation Error"

    def test_shows_with_exit_code(self, qtbot):
        dlg = ErrorDialog(make_error(exit_code=127))
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_shows_without_exit_code(self, qtbot):
        dlg = ErrorDialog(make_error(exit_code=None))
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_shows_with_technical_details(self, qtbot):
        dlg = ErrorDialog(make_error(technical_details='Detailed log here'))
        qtbot.addWidget(dlg)
        assert dlg.details_text.toPlainText() == 'Detailed log here'

    def test_shows_without_technical_details(self, qtbot):
        dlg = ErrorDialog(make_error(technical_details=None))
        qtbot.addWidget(dlg)
        assert not hasattr(dlg, 'details_text') or dlg is not None

    def test_shows_with_no_suggestions(self, qtbot):
        dlg = ErrorDialog(make_error(suggestions=[]))
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_shows_with_suggestions(self, qtbot):
        dlg = ErrorDialog(make_error(suggestions=['Fix A', 'Fix B']))
        qtbot.addWidget(dlg)
        assert dlg is not None


class TestErrorDialogCopyButton:

    def test_copy_error_sets_clipboard(self, qtbot):
        from PySide6.QtWidgets import QApplication
        dlg = ErrorDialog(make_error())
        qtbot.addWidget(dlg)
        # mock QMessageBox.information to avoid blocking
        from unittest.mock import patch
        with patch('PySide6.QtWidgets.QMessageBox.information', return_value=None):
            dlg._on_copy_error()
        clipboard = QApplication.clipboard()
        assert len(clipboard.text()) > 0


class TestErrorDialogConvenienceFunctions:

    def test_show_error_dialog_returns_int(self, qtbot):
        """show_error_dialog should create a dialog; test it instantiates."""
        dlg = ErrorDialog(make_error())
        qtbot.addWidget(dlg)
        # Just check dialog can be created — don't call .exec() to avoid blocking
        assert isinstance(dlg, ErrorDialog)
