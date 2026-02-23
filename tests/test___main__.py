"""
Tests for __main__.py entry point.
Covers the main() function body (lines 52-96).
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import patch, MagicMock


class TestMainFunction:
    """Tests for the main() entry point."""

    def _make_mock_app(self):
        mock_app = MagicMock()
        mock_app.exec.return_value = 0
        return mock_app

    def test_main_returns_zero_on_success(self):
        mock_app = self._make_mock_app()
        mock_window = MagicMock()
        with patch('sys.argv', ['dxcom-gui']), \
             patch('src.__main__.QApplication', return_value=mock_app), \
             patch('src.__main__.MainWindow', return_value=mock_window):
            from src.__main__ import main
            result = main()
        assert result == 0

    def test_main_creates_main_window(self):
        mock_app = self._make_mock_app()
        mock_window = MagicMock()
        with patch('sys.argv', ['dxcom-gui']), \
             patch('src.__main__.QApplication', return_value=mock_app), \
             patch('src.__main__.MainWindow', return_value=mock_window) as mock_mw:
            from src.__main__ import main
            main()
        mock_mw.assert_called_once()

    def test_main_shows_window(self):
        mock_app = self._make_mock_app()
        mock_window = MagicMock()
        with patch('sys.argv', ['dxcom-gui']), \
             patch('src.__main__.QApplication', return_value=mock_app), \
             patch('src.__main__.MainWindow', return_value=mock_window):
            from src.__main__ import main
            main()
        mock_window.show.assert_called_once()

    def test_main_applies_dark_theme(self):
        mock_app = self._make_mock_app()
        mock_window = MagicMock()
        with patch('sys.argv', ['dxcom-gui', '--theme', 'dark']), \
             patch('src.__main__.QApplication', return_value=mock_app), \
             patch('src.__main__.MainWindow', return_value=mock_window):
            from src.__main__ import main
            main()
        mock_window.apply_theme.assert_called_once_with('dark')

    def test_main_applies_light_theme(self):
        mock_app = self._make_mock_app()
        mock_window = MagicMock()
        with patch('sys.argv', ['dxcom-gui', '--theme', 'light']), \
             patch('src.__main__.QApplication', return_value=mock_app), \
             patch('src.__main__.MainWindow', return_value=mock_window):
            from src.__main__ import main
            main()
        mock_window.apply_theme.assert_called_once_with('light')

    def test_main_no_theme_does_not_apply_theme(self):
        mock_app = self._make_mock_app()
        mock_window = MagicMock()
        with patch('sys.argv', ['dxcom-gui']), \
             patch('src.__main__.QApplication', return_value=mock_app), \
             patch('src.__main__.MainWindow', return_value=mock_window):
            from src.__main__ import main
            main()
        mock_window.apply_theme.assert_not_called()

    def test_main_sets_dxcom_path(self):
        mock_app = self._make_mock_app()
        mock_window = MagicMock()
        with patch('sys.argv', ['dxcom-gui', '--dxcom-path', '/usr/local/bin/dxcom']), \
             patch('src.__main__.QApplication', return_value=mock_app), \
             patch('src.__main__.MainWindow', return_value=mock_window):
            from src.__main__ import main
            main()
        mock_window.set_dxcom_path.assert_called_once_with('/usr/local/bin/dxcom')

    def test_main_no_dxcom_path_does_not_set_path(self):
        mock_app = self._make_mock_app()
        mock_window = MagicMock()
        with patch('sys.argv', ['dxcom-gui']), \
             patch('src.__main__.QApplication', return_value=mock_app), \
             patch('src.__main__.MainWindow', return_value=mock_window):
            from src.__main__ import main
            main()
        mock_window.set_dxcom_path.assert_not_called()

    def test_main_sets_application_name(self):
        mock_app = self._make_mock_app()
        mock_window = MagicMock()
        with patch('sys.argv', ['dxcom-gui']), \
             patch('src.__main__.QApplication', return_value=mock_app), \
             patch('src.__main__.MainWindow', return_value=mock_window):
            from src.__main__ import main
            main()
        mock_app.setApplicationName.assert_called_once_with("DXCom GUI")

    def test_main_calls_app_exec(self):
        mock_app = self._make_mock_app()
        mock_window = MagicMock()
        with patch('sys.argv', ['dxcom-gui']), \
             patch('src.__main__.QApplication', return_value=mock_app), \
             patch('src.__main__.MainWindow', return_value=mock_window):
            from src.__main__ import main
            main()
        mock_app.exec.assert_called_once()
