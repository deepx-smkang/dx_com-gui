"""
Unit tests for DXComExecutor helper methods and DXComWrapper.
Tests non-Qt logic without starting threads or subprocesses.
"""
import sys
import os
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Qt requires an application instance before creating QThread subclasses
from PySide6.QtCore import QCoreApplication
_app = QCoreApplication.instance() or QCoreApplication(sys.argv)

from src.dxcom_wrapper import (
    DXComExecutor,
    DXComWrapper,
    strip_ansi_codes,
)


def make_executor(**kwargs):
    """Create a minimal DXComExecutor without starting it."""
    defaults = dict(
        input_path='/in/model.onnx',
        output_path='/out/model.dxnn',
        compiler_options={},
    )
    defaults.update(kwargs)
    return DXComExecutor(**defaults)


# ---------------------------------------------------------------------------
# strip_ansi_codes
# ---------------------------------------------------------------------------

class TestStripAnsiCodes(unittest.TestCase):

    def test_plain_text_unchanged(self):
        self.assertEqual(strip_ansi_codes('hello world'), 'hello world')

    def test_removes_color_code(self):
        text = '\x1b[31mred text\x1b[0m'
        self.assertEqual(strip_ansi_codes(text), 'red text')

    def test_removes_cursor_movement(self):
        text = '\x1b[2J\x1b[H'
        self.assertEqual(strip_ansi_codes(text), '')

    def test_empty_string(self):
        self.assertEqual(strip_ansi_codes(''), '')

    def test_mixed_ansi_and_text(self):
        text = '\x1b[1mBold\x1b[0m and normal'
        self.assertEqual(strip_ansi_codes(text), 'Bold and normal')


# ---------------------------------------------------------------------------
# _estimate_progress
# ---------------------------------------------------------------------------

class TestEstimateProgress(unittest.TestCase):

    def setUp(self):
        self.executor = make_executor()

    def test_loading_returns_10(self):
        self.assertEqual(self.executor._estimate_progress('Loading model...', 1), 10)

    def test_parsing_returns_10(self):
        self.assertEqual(self.executor._estimate_progress('Parsing ONNX graph', 1), 10)

    def test_optimizing_returns_40(self):
        self.assertEqual(self.executor._estimate_progress('Optimizing layers', 2), 40)

    def test_optimization_returns_40(self):
        self.assertEqual(self.executor._estimate_progress('Running optimization pass', 5), 40)

    def test_compiling_returns_60(self):
        self.assertEqual(self.executor._estimate_progress('Compiling ops', 10), 60)

    def test_writing_returns_90(self):
        self.assertEqual(self.executor._estimate_progress('Writing output file', 15), 90)

    def test_saving_returns_90(self):
        self.assertEqual(self.executor._estimate_progress('Saving dxnn model', 15), 90)

    def test_complete_returns_100(self):
        self.assertEqual(self.executor._estimate_progress('Compilation complete', 20), 100)

    def test_success_returns_100(self):
        self.assertEqual(self.executor._estimate_progress('Success!', 30), 100)

    def test_fallback_early_lines(self):
        result = self.executor._estimate_progress('unrelated line', 3)
        self.assertEqual(result, 15)

    def test_fallback_mid_lines(self):
        self.assertEqual(self.executor._estimate_progress('unrelated', 7), 30)
        self.assertEqual(self.executor._estimate_progress('unrelated', 15), 50)
        self.assertEqual(self.executor._estimate_progress('unrelated', 30), 70)
        self.assertEqual(self.executor._estimate_progress('unrelated', 50), 85)

    def test_case_insensitive(self):
        self.assertEqual(self.executor._estimate_progress('LOADING model', 1), 10)
        self.assertEqual(self.executor._estimate_progress('COMPILING', 1), 60)


# ---------------------------------------------------------------------------
# _extract_progress_message
# ---------------------------------------------------------------------------

class TestExtractProgressMessage(unittest.TestCase):

    def setUp(self):
        self.executor = make_executor()

    def test_normal_line_returned(self):
        self.assertEqual(self.executor._extract_progress_message('  hello  '), 'hello')

    def test_empty_line_returns_processing(self):
        self.assertEqual(self.executor._extract_progress_message(''), 'Processing...')

    def test_whitespace_only_returns_processing(self):
        self.assertEqual(self.executor._extract_progress_message('   '), 'Processing...')

    def test_long_line_truncated(self):
        long_line = 'x' * 200
        msg = self.executor._extract_progress_message(long_line)
        self.assertEqual(len(msg), 100)
        self.assertTrue(msg.endswith('...'))

    def test_exactly_100_chars_not_truncated(self):
        line = 'a' * 100
        msg = self.executor._extract_progress_message(line)
        self.assertEqual(len(msg), 100)
        self.assertFalse(msg.endswith('...'))


# ---------------------------------------------------------------------------
# stop()
# ---------------------------------------------------------------------------

class TestExecutorStop(unittest.TestCase):

    def test_stop_sets_flag(self):
        executor = make_executor()
        self.assertFalse(executor._should_stop)
        executor.stop()
        self.assertTrue(executor._should_stop)


# ---------------------------------------------------------------------------
# _build_command with calibration options
# ---------------------------------------------------------------------------

class TestBuildCommandCalibration(unittest.TestCase):

    def _build(self, options):
        with patch('src.dxcom_detector.get_dxcom_executable', return_value='dxcom'):
            executor = make_executor(compiler_options=options)
            return executor._build_command()

    def test_calib_method_included(self):
        cmd = self._build({'calib_method': 'entropy', 'opt_level': 1})
        self.assertIn('--calib_method', cmd)
        self.assertIn('entropy', cmd)

    def test_calib_num_included(self):
        cmd = self._build({'calib_num': 100, 'opt_level': 1})
        self.assertIn('--calib_num', cmd)
        self.assertIn('100', cmd)

    def test_calib_num_zero_included(self):
        """calib_num=0 is a valid value and should be included."""
        cmd = self._build({'calib_num': 0, 'opt_level': 0})
        self.assertIn('--calib_num', cmd)
        self.assertIn('0', cmd)

    def test_no_calib_when_absent(self):
        cmd = self._build({'opt_level': 0})
        self.assertNotIn('--calib_method', cmd)
        self.assertNotIn('--calib_num', cmd)


# ---------------------------------------------------------------------------
# DXComWrapper
# ---------------------------------------------------------------------------

class TestDXComWrapper(unittest.TestCase):

    def setUp(self):
        self.wrapper = DXComWrapper()

    def test_initial_state_not_running(self):
        self.assertFalse(self.wrapper.is_running())

    def test_default_timeout_is_set(self):
        self.assertIsNotNone(self.wrapper.default_timeout)
        self.assertGreater(self.wrapper.default_timeout, 0)

    def test_compile_returns_executor(self):
        executor = self.wrapper.compile(
            input_path='/in/model.onnx',
            output_path='/out/model.dxnn',
            compiler_options={'opt_level': 0},
        )
        self.assertIsInstance(executor, DXComExecutor)

    def test_compile_with_python_returns_executor(self):
        executor = self.wrapper.compile_with_python(
            script_path='/tmp/script.py',
            input_path='/in/model.onnx',
            output_path='/out/model.dxnn',
        )
        self.assertIsInstance(executor, DXComExecutor)
        self.assertEqual(executor.python_script_path, '/tmp/script.py')

    def test_compile_timeout_zero_means_none(self):
        executor = self.wrapper.compile(
            input_path='/in/model.onnx',
            output_path='/out/model.dxnn',
            compiler_options={},
            timeout=0,
        )
        self.assertIsNone(executor.timeout)

    def test_compile_explicit_timeout(self):
        executor = self.wrapper.compile(
            input_path='/in/model.onnx',
            output_path='/out/model.dxnn',
            compiler_options={},
            timeout=60,
        )
        self.assertEqual(executor.timeout, 60)

    def test_wait_for_completion_no_executor(self):
        """wait_for_completion() returns True when nothing is running."""
        self.assertTrue(self.wrapper.wait_for_completion())

    def test_stop_current_no_executor(self):
        """stop_current() does nothing (no crash) when no executor set."""
        self.wrapper.stop_current()  # Should not raise

    def test_stop_current_with_executor(self):
        executor = self.wrapper.compile(
            input_path='/in/model.onnx',
            output_path='/out/model.dxnn',
            compiler_options={},
        )
        self.wrapper.stop_current()
        self.assertTrue(executor._should_stop)


if __name__ == '__main__':
    unittest.main()
