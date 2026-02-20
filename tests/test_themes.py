"""
Unit tests for themes module.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.themes import get_theme_stylesheet, LIGHT_THEME, DARK_THEME


class TestThemes(unittest.TestCase):
    """Test cases for theme support."""

    def test_get_light_theme(self):
        """Test that 'light' returns the LIGHT_THEME stylesheet."""
        stylesheet = get_theme_stylesheet('light')
        self.assertEqual(stylesheet, LIGHT_THEME)
        self.assertIsInstance(stylesheet, str)
        self.assertGreater(len(stylesheet), 0)

    def test_get_dark_theme(self):
        """Test that 'dark' returns the DARK_THEME stylesheet."""
        stylesheet = get_theme_stylesheet('dark')
        self.assertEqual(stylesheet, DARK_THEME)
        self.assertIsInstance(stylesheet, str)
        self.assertGreater(len(stylesheet), 0)

    def test_dark_theme_case_insensitive(self):
        """Test that theme name is case-insensitive for dark."""
        self.assertEqual(get_theme_stylesheet('DARK'), DARK_THEME)
        self.assertEqual(get_theme_stylesheet('Dark'), DARK_THEME)
        self.assertEqual(get_theme_stylesheet('DaRk'), DARK_THEME)

    def test_unknown_theme_falls_back_to_light(self):
        """Test that unknown theme names fall back to light theme."""
        self.assertEqual(get_theme_stylesheet('unknown'), LIGHT_THEME)
        self.assertEqual(get_theme_stylesheet(''), LIGHT_THEME)
        self.assertEqual(get_theme_stylesheet('solarized'), LIGHT_THEME)

    def test_light_and_dark_are_different(self):
        """Test that light and dark themes are distinct stylesheets."""
        self.assertNotEqual(LIGHT_THEME, DARK_THEME)

    def test_light_theme_contains_expected_colors(self):
        """Test that light theme uses light color values."""
        self.assertIn('#ffffff', LIGHT_THEME.lower())

    def test_dark_theme_contains_expected_colors(self):
        """Test that dark theme has CSS color definitions."""
        self.assertIn('#', DARK_THEME)
        self.assertGreater(len(DARK_THEME), 0)


if __name__ == '__main__':
    unittest.main()
