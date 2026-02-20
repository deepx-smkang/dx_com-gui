"""
Unit tests for __main__.py argument parsing.
Tests parse_arguments() without launching a Qt application.
"""
import sys
import os
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.__main__ import parse_arguments


class TestParseArguments(unittest.TestCase):
    """Test argparse configuration in __main__."""

    def _parse(self, args):
        """Helper: parse with given argv (excluding program name)."""
        with patch('sys.argv', ['dxcom-gui'] + args):
            return parse_arguments()

    def test_no_args_returns_defaults(self):
        """All arguments are optional; defaults should be None."""
        args = self._parse([])
        self.assertIsNone(args.input)
        self.assertIsNone(args.output)
        self.assertIsNone(args.theme)
        self.assertIsNone(args.dxcom_path)

    def test_input_flag(self):
        """--input sets args.input."""
        args = self._parse(['--input', 'model.onnx'])
        self.assertEqual(args.input, 'model.onnx')

    def test_output_flag(self):
        """--output sets args.output."""
        args = self._parse(['--output', '/tmp/out.dxnn'])
        self.assertEqual(args.output, '/tmp/out.dxnn')

    def test_theme_light(self):
        """--theme light is accepted."""
        args = self._parse(['--theme', 'light'])
        self.assertEqual(args.theme, 'light')

    def test_theme_dark(self):
        """--theme dark is accepted."""
        args = self._parse(['--theme', 'dark'])
        self.assertEqual(args.theme, 'dark')

    def test_theme_invalid_rejected(self):
        """--theme with an invalid value should raise SystemExit."""
        with self.assertRaises(SystemExit):
            self._parse(['--theme', 'solarized'])

    def test_dxcom_path_flag(self):
        """--dxcom-path sets args.dxcom_path (hyphen becomes underscore)."""
        args = self._parse(['--dxcom-path', '/usr/local/bin/dxcom'])
        self.assertEqual(args.dxcom_path, '/usr/local/bin/dxcom')

    def test_all_flags_together(self):
        """All flags can be combined."""
        args = self._parse([
            '--input', 'a.onnx',
            '--output', 'b.dxnn',
            '--theme', 'dark',
            '--dxcom-path', '/opt/dxcom',
        ])
        self.assertEqual(args.input, 'a.onnx')
        self.assertEqual(args.output, 'b.dxnn')
        self.assertEqual(args.theme, 'dark')
        self.assertEqual(args.dxcom_path, '/opt/dxcom')

    def test_help_flag_exits(self):
        """--help prints usage and exits with code 0."""
        with self.assertRaises(SystemExit) as cm:
            self._parse(['--help'])
        self.assertEqual(cm.exception.code, 0)


if __name__ == '__main__':
    unittest.main()
