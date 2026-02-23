"""
Unit tests for DXComExecutor helper methods and DXComWrapper.
Tests non-Qt logic without starting threads or subprocesses.
"""
import sys
import os
import subprocess
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Qt requires an application instance before creating QThread subclasses.
# Use QApplication (not QCoreApplication) so pytest-qt can reuse the instance.
from PySide6.QtWidgets import QApplication
_app = QApplication.instance() or QApplication(sys.argv)

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


# ---------------------------------------------------------------------------
# DXComExecutor.run() – full subprocess path
# ---------------------------------------------------------------------------


class TestDXComExecutorRun(unittest.TestCase):
    """Tests for DXComExecutor.run() – calls run() directly (no QThread.start())."""

    def _make_mock_popen(self, stdout_lines, returncode=0):
        mock_process = MagicMock()
        mock_process.stdout = iter(stdout_lines)
        mock_process.wait.return_value = returncode
        mock_process.poll.return_value = returncode  # process already finished
        return mock_process

    def test_run_timeout_during_execution(self):
        """Timeout exceeds during stdout reading → calls _handle_timeout."""
        import time
        executor = make_executor(timeout=1)  # 1 second timeout
        results = []
        executor.compilation_finished.connect(lambda ok, msg: results.append((ok, msg)))

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None

        # Make the generator "run" after the start time has already passed
        def gen():
            yield 'Line 1\n'

        mock_proc.stdout = gen()

        def popen_with_past_start(cmd, **kwargs):
            # Override start time to be 100 seconds ago so timeout is exceeded
            executor._start_time = time.time() - 100
            return mock_proc

        with patch('subprocess.Popen', side_effect=popen_with_past_start):
            with patch('src.dxcom_detector.get_dxcom_executable', return_value='dxcom'):
                executor.run()

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0][0])

    def test_run_success_emits_finished_true(self):
        executor = make_executor()
        results = []
        executor.compilation_finished.connect(lambda ok, msg: results.append((ok, msg)))

        with patch('subprocess.Popen', return_value=self._make_mock_popen(
                ['Compiling...\n', 'Step 1/3\n'], returncode=0)):
            with patch('src.dxcom_detector.get_dxcom_executable', return_value='dxcom'):
                executor.run()

        self.assertEqual(len(results), 1)
        self.assertTrue(results[0][0])

    def test_run_failure_emits_finished_false(self):
        executor = make_executor()
        results = []
        executor.compilation_finished.connect(lambda ok, msg: results.append((ok, msg)))

        with patch('subprocess.Popen', return_value=self._make_mock_popen(
                ['Error: something failed\n'], returncode=1)):
            with patch('src.dxcom_detector.get_dxcom_executable', return_value='dxcom'):
                executor.run()

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0][0])

    def test_run_cancelled_emits_finished_false(self):
        """_should_stop=True during stdout reading → cancellation."""
        executor = make_executor()
        results = []
        executor.compilation_finished.connect(lambda ok, msg: results.append((ok, msg)))

        def stop_after_first_line(cmd, **kwargs):
            mock_process = MagicMock()

            def gen():
                executor._should_stop = True
                yield 'Line 1\n'

            mock_process.stdout = gen()
            mock_process.poll.return_value = None
            return mock_process

        with patch('subprocess.Popen', side_effect=stop_after_first_line):
            with patch('src.dxcom_detector.get_dxcom_executable', return_value='dxcom'):
                executor.run()

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0][0])
        self.assertIn('cancel', results[0][1].lower())

    def test_run_file_not_found_emits_finished_false(self):
        executor = make_executor()
        results = []
        executor.compilation_finished.connect(lambda ok, msg: results.append((ok, msg)))

        with patch('subprocess.Popen', side_effect=FileNotFoundError('dxcom not found')):
            with patch('src.dxcom_detector.get_dxcom_executable', return_value='dxcom'):
                executor.run()

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0][0])

    def test_run_generic_exception_emits_finished_false(self):
        executor = make_executor()
        results = []
        executor.compilation_finished.connect(lambda ok, msg: results.append((ok, msg)))

        with patch('subprocess.Popen', side_effect=RuntimeError('unexpected')):
            with patch('src.dxcom_detector.get_dxcom_executable', return_value='dxcom'):
                executor.run()

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0][0])

    def test_run_python_mode_success(self):
        """Python script mode: executor.python_script_path is set."""
        executor = make_executor(python_script_path='/tmp/script.py')
        results = []
        executor.compilation_finished.connect(lambda ok, msg: results.append((ok, msg)))

        with patch('subprocess.Popen', return_value=self._make_mock_popen(
                ['Script output\n'], returncode=0)):
            executor.run()

        self.assertEqual(len(results), 1)
        self.assertTrue(results[0][0])


# ---------------------------------------------------------------------------
# _handle_timeout / _handle_process_failure / _handle_exception (direct)
# ---------------------------------------------------------------------------


class TestDXComExecutorHandlers(unittest.TestCase):

    def test_handle_timeout_emits_finished_false(self):
        executor = make_executor(timeout=10)
        executor._start_time = 0.0
        results = []
        executor.compilation_finished.connect(lambda ok, msg: results.append((ok, msg)))

        executor._handle_timeout()

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0][0])

    def test_handle_timeout_emits_error_occurred(self):
        executor = make_executor(timeout=5)
        executor._start_time = 0.0
        errors = []
        executor.error_occurred.connect(lambda msg: errors.append(msg))

        executor._handle_timeout()

        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], str)

    def test_handle_process_failure_emits_finished_false(self):
        executor = make_executor()
        results = []
        executor.compilation_finished.connect(lambda ok, msg: results.append((ok, msg)))

        executor._handle_process_failure(exit_code=2)

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0][0])

    def test_handle_process_failure_emits_error_occurred(self):
        executor = make_executor()
        errors = []
        executor.error_occurred.connect(lambda msg: errors.append(msg))

        executor._handle_process_failure(exit_code=1)

        self.assertEqual(len(errors), 1)

    def test_handle_exception_emits_finished_false(self):
        executor = make_executor()
        results = []
        executor.compilation_finished.connect(lambda ok, msg: results.append((ok, msg)))

        executor._handle_exception(ValueError("something broke"), "test context")

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0][0])

    def test_handle_exception_emits_error_occurred(self):
        executor = make_executor()
        errors = []
        executor.error_occurred.connect(lambda msg: errors.append(msg))

        executor._handle_exception(RuntimeError("oops"), "context")

        self.assertEqual(len(errors), 1)


# ---------------------------------------------------------------------------
# _terminate_process
# ---------------------------------------------------------------------------


class TestDXComExecutorTerminate(unittest.TestCase):

    def test_terminate_running_process(self):
        executor = make_executor()
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # still running
        executor._process = mock_proc

        executor._terminate_process()

        mock_proc.terminate.assert_called_once()

    def test_terminate_already_finished_process(self):
        executor = make_executor()
        mock_proc = MagicMock()
        mock_proc.poll.return_value = 0  # already done
        executor._process = mock_proc

        executor._terminate_process()

        mock_proc.terminate.assert_not_called()

    def test_terminate_timeout_falls_back_to_kill(self):
        executor = make_executor()
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # still running
        mock_proc.wait.side_effect = [subprocess.TimeoutExpired(cmd='dxcom', timeout=5), None]
        executor._process = mock_proc

        executor._terminate_process()

        mock_proc.kill.assert_called_once()


# ---------------------------------------------------------------------------
# DXComWrapper – stop previous running executor in compile/compile_with_python
# ---------------------------------------------------------------------------


class TestDXComWrapperStopsPrevious(unittest.TestCase):

    def test_compile_stops_running_executor(self):
        wrapper = DXComWrapper()
        mock_exec = MagicMock()
        mock_exec.isRunning.return_value = True
        wrapper._current_executor = mock_exec

        wrapper.compile(
            input_path='/in/model.onnx',
            output_path='/out/model.dxnn',
            compiler_options={},
        )

        mock_exec.stop.assert_called_once()
        mock_exec.wait.assert_called_once()

    def test_compile_with_python_stops_running_executor(self):
        wrapper = DXComWrapper()
        mock_exec = MagicMock()
        mock_exec.isRunning.return_value = True
        wrapper._current_executor = mock_exec

        wrapper.compile_with_python(
            script_path='/tmp/script.py',
            input_path='/in/model.onnx',
            output_path='/out/model.dxnn',
        )

        mock_exec.stop.assert_called_once()
        mock_exec.wait.assert_called_once()

    def test_compile_with_python_timeout_zero_means_no_timeout(self):
        """compile_with_python with timeout=0 sets executor.timeout to None."""
        wrapper = DXComWrapper()
        executor = wrapper.compile_with_python(
            script_path='/tmp/script.py',
            input_path='/in/model.onnx',
            output_path='/out/model.dxnn',
            timeout=0,
        )
        self.assertIsNone(executor.timeout)

    def test_wait_for_completion_with_non_running_executor(self):
        """wait_for_completion delegates to executor.wait() when set."""
        wrapper = DXComWrapper()
        executor = wrapper.compile(
            input_path='/in/model.onnx',
            output_path='/out/model.dxnn',
            compiler_options={},
        )
        # executor is not started, so wait() should return immediately (True)
        result = wrapper.wait_for_completion(timeout_ms=100)
        self.assertIsInstance(result, bool)


if __name__ == '__main__':
    unittest.main()
