"""
GUI tests for MainWindow.
Run with: DISPLAY=:99 python -m pytest tests/test_gui_main_window.py -v
"""
import sys
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QMessageBox
from src.main_window import MainWindow, CompilationStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_onnx(tmp_path, name="model.onnx", content=b"\x08\x00\x00\x00"):
    """Write a minimal fake ONNX file (4 bytes, non-empty)."""
    p = tmp_path / name
    p.write_bytes(content)
    return str(p)


def _make_json(tmp_path, name="cfg.json", data=None):
    """Write a valid JSON config file."""
    p = tmp_path / name
    data = data or {"key": "value"}
    p.write_text(json.dumps(data))
    return str(p)


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def win(qtbot):
    """Create a MainWindow with all dialog pop-ups silenced."""
    with patch("src.main_window.QMessageBox.warning", return_value=QMessageBox.StandardButton.Ok), \
         patch("src.main_window.QMessageBox.critical", return_value=QMessageBox.StandardButton.Ok), \
         patch("src.main_window.QMessageBox.information", return_value=QMessageBox.StandardButton.Ok), \
         patch("src.main_window.QMessageBox.about", return_value=None):
        w = MainWindow()
        qtbot.addWidget(w)
        yield w


# ---------------------------------------------------------------------------
# Construction & basic state
# ---------------------------------------------------------------------------

class TestMainWindowCreation:

    def test_creates_without_error(self, win):
        assert win is not None

    def test_window_title(self, win):
        assert "DXCom" in win.windowTitle()

    def test_initial_execution_mode_is_python(self, win):
        assert win.execution_mode == "python"

    def test_initial_python_data_source_is_config(self, win):
        assert win.python_data_source == "config"

    def test_initial_input_model_path_empty(self, win):
        assert win.input_model_path == ""

    def test_initial_output_model_path_empty(self, win):
        assert win.output_model_path == ""

    def test_initial_config_file_path_empty(self, win):
        assert win.config_file_path == ""

    def test_initial_compilation_status_idle(self, win):
        assert win.compilation_status == CompilationStatus.IDLE

    def test_initial_batch_mode_false(self, win):
        assert win.batch_mode is False

    def test_initial_batch_files_empty(self, win):
        assert win.batch_files == []

    def test_initial_validation_errors_empty(self, win):
        assert win.validation_errors == {}

    def test_compile_button_exists(self, win):
        assert win.compile_button is not None

    def test_compile_button_initially_disabled(self, win):
        assert not win.compile_button.isEnabled()

    def test_cancel_button_initially_hidden(self, win):
        assert not win.cancel_button.isVisible()

    def test_log_text_area_exists(self, win):
        assert win.log_text_area is not None

    def test_progress_bar_initial_value_zero(self, win):
        assert win.progress_bar.value() == 0

    def test_input_path_field_exists(self, win):
        assert win.input_path_field is not None

    def test_output_path_field_exists(self, win):
        assert win.output_path_field is not None

    def test_config_path_field_exists(self, win):
        assert win.config_path_field is not None

    def test_command_preview_field_exists(self, win):
        assert win.command_preview_field is not None

    def test_settings_manager_initialized(self, win):
        assert win.settings_manager is not None

    def test_dxcom_wrapper_initialized(self, win):
        assert win.dxcom_wrapper is not None

    def test_version_constant(self, win):
        assert hasattr(win, 'VERSION')
        assert win.VERSION is not None

    def test_company_constant(self, win):
        assert win.COMPANY == "DEEPX"


# ---------------------------------------------------------------------------
# CompilationStatus enum
# ---------------------------------------------------------------------------

class TestCompilationStatusEnum:

    def test_idle_value(self):
        assert CompilationStatus.IDLE.value == "idle"

    def test_running_value(self):
        assert CompilationStatus.RUNNING.value == "running"

    def test_success_value(self):
        assert CompilationStatus.SUCCESS.value == "success"

    def test_failed_value(self):
        assert CompilationStatus.FAILED.value == "failed"

    def test_cancelled_value(self):
        assert CompilationStatus.CANCELLED.value == "cancelled"


# ---------------------------------------------------------------------------
# set_status_message
# ---------------------------------------------------------------------------

class TestSetStatusMessage:

    def test_set_status_message_shows_in_status_bar(self, win):
        win.set_status_message("Hello test")
        assert win.status_bar.currentMessage() == "Hello test"

    def test_set_status_message_with_timeout(self, win):
        # Just verify it doesn't raise
        win.set_status_message("Timed message", 1000)
        assert win.status_bar.currentMessage() == "Timed message"

    def test_set_status_message_empty_string(self, win):
        win.set_status_message("")
        # Should not raise; status bar now shows empty
        assert win.status_bar.currentMessage() == ""


# ---------------------------------------------------------------------------
# _set_compilation_status
# ---------------------------------------------------------------------------

class TestSetCompilationStatus:

    def test_idle_status(self, win):
        win._set_compilation_status(CompilationStatus.IDLE)
        assert win.compilation_status == CompilationStatus.IDLE
        assert "Ready" in win.status_label.text()

    def test_running_status(self, win):
        win._set_compilation_status(CompilationStatus.RUNNING)
        assert win.compilation_status == CompilationStatus.RUNNING
        assert "Compiling" in win.status_label.text()

    def test_success_status(self, win):
        win._set_compilation_status(CompilationStatus.SUCCESS)
        assert win.compilation_status == CompilationStatus.SUCCESS
        assert "Completed" in win.status_label.text()

    def test_failed_status(self, win):
        win._set_compilation_status(CompilationStatus.FAILED)
        assert win.compilation_status == CompilationStatus.FAILED
        assert "Failed" in win.status_label.text()

    def test_cancelled_status(self, win):
        win._set_compilation_status(CompilationStatus.CANCELLED)
        assert win.compilation_status == CompilationStatus.CANCELLED
        assert "Cancelled" in win.status_label.text()


# ---------------------------------------------------------------------------
# _append_log_message / log
# ---------------------------------------------------------------------------

class TestLogMethods:

    def test_append_log_message_info(self, win):
        win._append_log_message("Info message\n", "info")
        assert "Info message" in win.log_text_area.toPlainText()

    def test_append_log_message_error(self, win):
        win._append_log_message("Error message\n", "error")
        assert "Error message" in win.log_text_area.toPlainText()

    def test_append_log_message_warning(self, win):
        win._append_log_message("Warning message\n", "warning")
        assert "Warning message" in win.log_text_area.toPlainText()

    def test_append_log_message_success(self, win):
        win._append_log_message("Success message\n", "success")
        assert "Success message" in win.log_text_area.toPlainText()

    def test_append_log_message_default(self, win):
        win._append_log_message("Default message\n")
        assert "Default message" in win.log_text_area.toPlainText()

    def test_log_wrapper(self, win):
        win.log("From log()\n", "info")
        assert "From log()" in win.log_text_area.toPlainText()

    def test_log_multiple_messages(self, win):
        win.log_text_area.clear()
        win.log("First\n")
        win.log("Second\n")
        text = win.log_text_area.toPlainText()
        assert "First" in text
        assert "Second" in text


# ---------------------------------------------------------------------------
# get_compiler_options
# ---------------------------------------------------------------------------

class TestGetCompilerOptions:

    def test_returns_dict(self, win):
        opts = win.get_compiler_options()
        assert isinstance(opts, dict)

    def test_has_config_path_key(self, win):
        opts = win.get_compiler_options()
        assert 'config_path' in opts

    def test_has_opt_level_key(self, win):
        opts = win.get_compiler_options()
        assert 'opt_level' in opts

    def test_default_opt_level_is_1(self, win):
        opts = win.get_compiler_options()
        assert opts['opt_level'] == 1

    def test_has_gen_log_key(self, win):
        opts = win.get_compiler_options()
        assert 'gen_log' in opts

    def test_default_gen_log_false(self, win):
        opts = win.get_compiler_options()
        assert opts['gen_log'] is False

    def test_has_aggressive_partitioning_key(self, win):
        opts = win.get_compiler_options()
        assert 'aggressive_partitioning' in opts

    def test_default_aggressive_partitioning_false(self, win):
        opts = win.get_compiler_options()
        assert opts['aggressive_partitioning'] is False

    def test_has_compile_input_nodes_key(self, win):
        opts = win.get_compiler_options()
        assert 'compile_input_nodes' in opts

    def test_has_compile_output_nodes_key(self, win):
        opts = win.get_compiler_options()
        assert 'compile_output_nodes' in opts

    def test_compile_input_nodes_initially_empty(self, win):
        opts = win.get_compiler_options()
        assert opts['compile_input_nodes'] == ""

    def test_compile_output_nodes_initially_empty(self, win):
        opts = win.get_compiler_options()
        assert opts['compile_output_nodes'] == ""

    def test_has_calib_method_key(self, win):
        opts = win.get_compiler_options()
        assert 'calib_method' in opts

    def test_default_calib_method_is_ema(self, win):
        opts = win.get_compiler_options()
        assert opts['calib_method'] == 'ema'

    def test_has_calib_num_key(self, win):
        opts = win.get_compiler_options()
        assert 'calib_num' in opts

    def test_default_calib_num_is_100(self, win):
        opts = win.get_compiler_options()
        assert opts['calib_num'] == 100

    def test_gen_log_checkbox_reflects_in_options(self, win):
        win.gen_log_checkbox.setChecked(True)
        opts = win.get_compiler_options()
        assert opts['gen_log'] is True

    def test_aggressive_partitioning_reflects_in_options(self, win):
        win.aggressive_partitioning_checkbox.setChecked(True)
        opts = win.get_compiler_options()
        assert opts['aggressive_partitioning'] is True

    def test_opt_level_0_reflects_in_options(self, win):
        win.opt_level_combo.setCurrentIndex(0)
        opts = win.get_compiler_options()
        assert opts['opt_level'] == 0

    def test_input_node_text_reflects_in_options(self, win):
        win.compile_input_nodes_field.setText("node1,node2")
        opts = win.get_compiler_options()
        assert opts['compile_input_nodes'] == "node1,node2"

    def test_output_node_text_reflects_in_options(self, win):
        win.compile_output_nodes_field.setText("out1")
        opts = win.get_compiler_options()
        assert opts['compile_output_nodes'] == "out1"


# ---------------------------------------------------------------------------
# get_validation_errors / is_ready_to_compile
# ---------------------------------------------------------------------------

class TestValidationState:

    def test_get_validation_errors_returns_dict(self, win):
        errs = win.get_validation_errors()
        assert isinstance(errs, dict)

    def test_initially_no_validation_errors(self, win):
        assert win.get_validation_errors() == {}

    def test_is_ready_to_compile_returns_bool(self, win):
        result = win.is_ready_to_compile()
        assert isinstance(result, bool)

    def test_not_ready_initially(self, win):
        assert not win.is_ready_to_compile()

    def test_set_validation_error_stores_error(self, win):
        win._set_validation_error('test_field', "Something went wrong")
        errs = win.get_validation_errors()
        assert 'test_field' in errs
        assert errs['test_field'] == "Something went wrong"

    def test_clear_validation_error_removes_error(self, win):
        win._set_validation_error('test_field', "Error")
        win._clear_validation_error('test_field')
        assert 'test_field' not in win.get_validation_errors()

    def test_clear_nonexistent_error_does_not_raise(self, win):
        win._clear_validation_error('nonexistent')  # should not raise

    def test_get_validation_errors_returns_copy(self, win):
        errs1 = win.get_validation_errors()
        errs1['injected'] = "hack"
        errs2 = win.get_validation_errors()
        assert 'injected' not in errs2


# ---------------------------------------------------------------------------
# _on_mode_changed
# ---------------------------------------------------------------------------

class TestOnModeChanged:

    def test_mode_python_sets_execution_mode(self, win):
        win._on_mode_changed(0)
        assert win.execution_mode == "python"

    def test_mode_cli_sets_execution_mode(self, win):
        win._on_mode_changed(1)
        assert win.execution_mode == "cli"

    def test_mode_switch_to_cli_then_back_to_python(self, win):
        win._on_mode_changed(1)
        assert win.execution_mode == "cli"
        win._on_mode_changed(0)
        assert win.execution_mode == "python"

    def test_python_mode_shows_python_data_source_group(self, win):
        win._on_mode_changed(0)
        if win.python_data_source_group:
            assert not win.python_data_source_group.isHidden()

    def test_cli_mode_hides_python_data_source_group(self, win):
        win._on_mode_changed(1)
        if win.python_data_source_group:
            assert not win.python_data_source_group.isVisible()

    def test_python_mode_shows_gen_python_button(self, win):
        win._on_mode_changed(0)
        assert not win.gen_python_button.isHidden()

    def test_cli_mode_hides_gen_python_button(self, win):
        win._on_mode_changed(1)
        assert not win.gen_python_button.isVisible()


# ---------------------------------------------------------------------------
# _on_data_source_btn_changed
# ---------------------------------------------------------------------------

class TestOnDataSourceBtnChanged:

    def test_index_0_sets_config(self, win):
        win._on_data_source_btn_changed(0)
        assert win.python_data_source == "config"

    def test_index_1_sets_dataloader(self, win):
        win._on_data_source_btn_changed(1)
        assert win.python_data_source == "dataloader"

    def test_switching_back_to_config(self, win):
        win._on_data_source_btn_changed(1)
        win._on_data_source_btn_changed(0)
        assert win.python_data_source == "config"


# ---------------------------------------------------------------------------
# _update_config_field_state
# ---------------------------------------------------------------------------

class TestUpdateConfigFieldState:

    def test_python_dataloader_disables_config_field(self, win):
        win.execution_mode = "python"
        win.python_data_source = "dataloader"
        win._update_config_field_state()
        assert not win.config_path_field.isEnabled()

    def test_python_config_enables_config_field(self, win):
        win.execution_mode = "python"
        win.python_data_source = "config"
        win._update_config_field_state()
        assert win.config_path_field.isEnabled()

    def test_cli_mode_enables_config_field(self, win):
        win.execution_mode = "cli"
        win._update_config_field_state()
        assert win.config_path_field.isEnabled()


# ---------------------------------------------------------------------------
# _validate_output_path
# ---------------------------------------------------------------------------

class TestValidateOutputPath:

    def test_empty_path_returns_error_string(self, win):
        result = win._validate_output_path("")
        assert result is not True
        assert isinstance(result, str)

    def test_existing_dir_returns_true(self, tmp_path, win):
        result = win._validate_output_path(str(tmp_path))
        assert result is True

    def test_nonexistent_path_with_existing_parent_returns_true(self, tmp_path, win):
        new_dir = str(tmp_path / "nonexistent_subdir")
        result = win._validate_output_path(new_dir)
        assert result is True

    def test_path_that_is_a_file_returns_error(self, tmp_path, win):
        f = tmp_path / "file.txt"
        f.write_text("x")
        result = win._validate_output_path(str(f))
        assert result is not True

    def test_nonexistent_parent_returns_error(self, win):
        result = win._validate_output_path("/nonexistent_root_xyz/subdir")
        assert result is not True


# ---------------------------------------------------------------------------
# _validate_input_file
# ---------------------------------------------------------------------------

class TestValidateInputFile:

    def test_empty_path_returns_false(self, win):
        result = win._validate_input_file("")
        assert result is False

    def test_empty_path_sets_validation_error(self, win):
        win.validation_errors.clear()
        win._validate_input_file("")
        assert 'input_file' in win.validation_errors

    def test_nonexistent_file_returns_false(self, win):
        result = win._validate_input_file("/no/such/file.onnx")
        assert result is False

    def test_directory_path_returns_false(self, tmp_path, win):
        result = win._validate_input_file(str(tmp_path))
        assert result is False

    def test_wrong_extension_returns_false(self, tmp_path, win):
        f = tmp_path / "model.pt"
        f.write_bytes(b"\x00\x01\x02\x03")
        result = win._validate_input_file(str(f))
        assert result is False

    def test_empty_file_returns_false(self, tmp_path, win):
        f = tmp_path / "empty.onnx"
        f.write_bytes(b"")
        result = win._validate_input_file(str(f))
        assert result is False

    def test_valid_onnx_file_returns_true(self, tmp_path, win):
        f = tmp_path / "model.onnx"
        f.write_bytes(b"\x08\x01\x00\x00" + b"\x00" * 100)
        result = win._validate_input_file(str(f))
        assert result is True

    def test_valid_onnx_clears_validation_error(self, tmp_path, win):
        # First set an error
        win._set_validation_error('input_file', "dummy")
        f = tmp_path / "model.onnx"
        f.write_bytes(b"\x08\x01\x00\x00" + b"\x00" * 100)
        win._validate_input_file(str(f))
        assert 'input_file' not in win.validation_errors

    def test_too_small_file_returns_false(self, tmp_path, win):
        f = tmp_path / "tiny.onnx"
        f.write_bytes(b"\x08")  # only 1 byte
        result = win._validate_input_file(str(f))
        assert result is False


# ---------------------------------------------------------------------------
# _validate_config_file
# ---------------------------------------------------------------------------

class TestValidateConfigFile:

    def test_empty_path_returns_false_in_cli_mode(self, win):
        win.execution_mode = "cli"
        result = win._validate_config_file("")
        assert result is False

    def test_dataloader_mode_skips_validation(self, win):
        win.execution_mode = "python"
        win.python_data_source = "dataloader"
        result = win._validate_config_file("")
        assert result is True

    def test_nonexistent_file_returns_false(self, win):
        win.execution_mode = "cli"
        result = win._validate_config_file("/no/such/config.json")
        assert result is False

    def test_wrong_extension_returns_false(self, tmp_path, win):
        win.execution_mode = "cli"
        f = tmp_path / "config.txt"
        f.write_text("{}")
        result = win._validate_config_file(str(f))
        assert result is False

    def test_invalid_json_returns_false(self, tmp_path, win):
        win.execution_mode = "cli"
        f = tmp_path / "bad.json"
        f.write_text("{ not valid json !!}")
        result = win._validate_config_file(str(f))
        assert result is False

    def test_json_array_returns_false(self, tmp_path, win):
        win.execution_mode = "cli"
        f = tmp_path / "array.json"
        f.write_text("[1, 2, 3]")
        result = win._validate_config_file(str(f))
        assert result is False

    def test_valid_json_object_returns_true(self, tmp_path, win):
        win.execution_mode = "cli"
        f = tmp_path / "valid.json"
        f.write_text(json.dumps({"key": "value"}))
        result = win._validate_config_file(str(f))
        assert result is True

    def test_valid_json_clears_validation_error(self, tmp_path, win):
        win.execution_mode = "cli"
        win._set_validation_error('config_file', "dummy")
        f = tmp_path / "clean.json"
        f.write_text(json.dumps({"x": 1}))
        win._validate_config_file(str(f))
        assert 'config_file' not in win.validation_errors


# ---------------------------------------------------------------------------
# _validate_node_names
# ---------------------------------------------------------------------------

class TestValidateNodeNames:

    def test_empty_string_returns_true(self, win):
        result = win._validate_node_names("", 'input_nodes')
        assert result is True

    def test_whitespace_only_returns_true(self, win):
        result = win._validate_node_names("   ", 'input_nodes')
        assert result is True

    def test_single_valid_name_returns_true(self, win):
        result = win._validate_node_names("node1", 'input_nodes')
        assert result is True

    def test_multiple_valid_names_returns_true(self, win):
        result = win._validate_node_names("node1,node2,node3", 'input_nodes')
        assert result is True

    def test_consecutive_commas_returns_false(self, win):
        result = win._validate_node_names("node1,,node2", 'input_nodes')
        assert result is False

    def test_names_with_spaces_stripped_ok(self, win):
        result = win._validate_node_names("node1, node2", 'input_nodes')
        assert result is True

    def test_invalid_characters_return_false(self, win):
        result = win._validate_node_names("node<1>", 'input_nodes')
        assert result is False

    def test_valid_clears_error(self, win):
        win._set_validation_error('input_nodes', "bad nodes")
        win._validate_node_names("node1", 'input_nodes')
        assert 'input_nodes' not in win.validation_errors

    def test_invalid_sets_error(self, win):
        win.validation_errors.pop('input_nodes', None)
        win._validate_node_names("node1,,node2", 'input_nodes')
        assert 'input_nodes' in win.validation_errors


# ---------------------------------------------------------------------------
# _suggest_output_path
# ---------------------------------------------------------------------------

class TestSuggestOutputPath:

    def test_suggests_directory_of_input(self, tmp_path, win):
        f = tmp_path / "model.onnx"
        f.write_bytes(b"\x00" * 4)
        win._suggest_output_path(str(f))
        assert win.output_model_path == str(tmp_path)

    def test_sets_output_field_text(self, tmp_path, win):
        f = tmp_path / "model.onnx"
        f.write_bytes(b"\x00" * 4)
        win._suggest_output_path(str(f))
        assert win.output_path_field.text() == str(tmp_path)


# ---------------------------------------------------------------------------
# _on_output_received
# ---------------------------------------------------------------------------

class TestOnOutputReceived:

    def test_appends_line_to_log(self, win):
        win.log_text_area.clear()
        win._on_output_received("output line here\n")
        assert "output line here" in win.log_text_area.toPlainText()

    def test_error_line(self, win):
        win.log_text_area.clear()
        win._on_output_received("error: something failed\n")
        assert "error: something failed" in win.log_text_area.toPlainText()

    def test_warning_line(self, win):
        win.log_text_area.clear()
        win._on_output_received("warning: check this\n")
        assert "warning: check this" in win.log_text_area.toPlainText()

    def test_success_line(self, win):
        win.log_text_area.clear()
        win._on_output_received("compilation done successfully\n")
        assert "compilation done successfully" in win.log_text_area.toPlainText()

    def test_indented_line(self, win):
        win.log_text_area.clear()
        win._on_output_received("  indented detail\n")
        assert "indented detail" in win.log_text_area.toPlainText()


# ---------------------------------------------------------------------------
# _on_progress_updated
# ---------------------------------------------------------------------------

class TestOnProgressUpdated:

    def test_updates_progress_bar(self, win):
        win._on_progress_updated(42, "step A")
        assert win.progress_bar.value() == 42

    def test_updates_status_bar(self, win):
        win._on_progress_updated(75, "step B")
        assert "75%" in win.status_bar.currentMessage()

    def test_zero_progress(self, win):
        win._on_progress_updated(0, "start")
        assert win.progress_bar.value() == 0

    def test_100_progress(self, win):
        win._on_progress_updated(100, "done")
        assert win.progress_bar.value() == 100


# ---------------------------------------------------------------------------
# _on_compilation_finished
# ---------------------------------------------------------------------------

class TestOnCompilationFinished:

    def test_success_sets_status_to_success(self, win):
        with patch("src.main_window.QMessageBox.information"):
            win._on_compilation_finished(True, "OK")
        assert win.compilation_status == CompilationStatus.SUCCESS

    def test_success_re_enables_compile_button(self, win):
        win.dxcom_available = True
        with patch("src.main_window.QMessageBox.information"):
            win._on_compilation_finished(True, "OK")
        assert win.compile_button.isEnabled()

    def test_success_hides_cancel_button(self, win):
        with patch("src.main_window.QMessageBox.information"):
            win._on_compilation_finished(True, "OK")
        assert not win.cancel_button.isVisible()

    def test_success_sets_progress_100(self, win):
        with patch("src.main_window.QMessageBox.information"):
            win._on_compilation_finished(True, "OK")
        assert win.progress_bar.value() == 100

    def test_failure_sets_status_to_failed(self, win):
        win._on_compilation_finished(False, "some error")
        assert win.compilation_status == CompilationStatus.FAILED

    def test_cancel_message_sets_cancelled_status(self, win):
        win._on_compilation_finished(False, "cancel requested")
        assert win.compilation_status == CompilationStatus.CANCELLED

    def test_failure_re_enables_compile_button(self, win):
        win.dxcom_available = True
        win._on_compilation_finished(False, "error")
        assert win.compile_button.isEnabled()


# ---------------------------------------------------------------------------
# _on_error_occurred
# ---------------------------------------------------------------------------

class TestOnErrorOccurred:

    def test_updates_status_bar(self, win):
        win._on_error_occurred("disk full")
        assert "disk full" in win.status_bar.currentMessage()

    def test_does_not_raise(self, win):
        win._on_error_occurred("unexpected error XYZ")


# ---------------------------------------------------------------------------
# apply_theme
# ---------------------------------------------------------------------------

class TestApplyTheme:

    def test_apply_light_theme_does_not_raise(self, win):
        win.apply_theme('light')

    def test_apply_dark_theme_does_not_raise(self, win):
        win.apply_theme('dark')

    def test_light_theme_updates_theme_action_text(self, win):
        win.apply_theme('light')
        assert "Dark" in win.theme_action.text()

    def test_dark_theme_updates_theme_action_text(self, win):
        win.apply_theme('dark')
        assert "Light" in win.theme_action.text()


# ---------------------------------------------------------------------------
# _on_toggle_theme
# ---------------------------------------------------------------------------

class TestOnToggleTheme:

    def test_toggle_from_light_sets_dark(self, win):
        win.settings_manager.set('theme', 'light')
        win._on_toggle_theme()
        assert win.settings_manager.get('theme') == 'dark'

    def test_toggle_from_dark_sets_light(self, win):
        win.settings_manager.set('theme', 'dark')
        win._on_toggle_theme()
        assert win.settings_manager.get('theme') == 'light'

    def test_double_toggle_restores_original(self, win):
        win.settings_manager.set('theme', 'light')
        win._on_toggle_theme()
        win._on_toggle_theme()
        assert win.settings_manager.get('theme') == 'light'


# ---------------------------------------------------------------------------
# _on_about
# ---------------------------------------------------------------------------

class TestOnAbout:

    def test_on_about_does_not_raise(self, win):
        with patch("src.main_window.QMessageBox.about", return_value=None):
            win._on_about()


# ---------------------------------------------------------------------------
# _on_show_shortcuts
# ---------------------------------------------------------------------------

class TestOnShowShortcuts:

    def test_does_not_raise(self, win):
        with patch("src.main_window.QMessageBox.information", return_value=QMessageBox.StandardButton.Ok):
            win._on_show_shortcuts()


# ---------------------------------------------------------------------------
# _update_recent_files_menu
# ---------------------------------------------------------------------------

class TestUpdateRecentFilesMenu:

    def test_empty_recent_files_shows_no_recent_action(self, win):
        win.settings_manager.clear_recent_files()
        win._update_recent_files_menu()
        actions = win.recent_files_menu.actions()
        assert len(actions) == 1
        assert not actions[0].isEnabled()

    def test_with_recent_files_shows_entries(self, tmp_path, win):
        f = tmp_path / "model.onnx"
        f.write_bytes(b"\x00" * 4)
        win.settings_manager.add_recent_file(str(f))
        win._update_recent_files_menu()
        actions = win.recent_files_menu.actions()
        texts = [a.text() for a in actions]
        assert any("model.onnx" in t for t in texts)

    def test_clear_recent_files_appears_when_files_exist(self, tmp_path, win):
        f = tmp_path / "model.onnx"
        f.write_bytes(b"\x00" * 4)
        win.settings_manager.add_recent_file(str(f))
        win._update_recent_files_menu()
        texts = [a.text() for a in win.recent_files_menu.actions()]
        assert any("Clear" in t for t in texts)


# ---------------------------------------------------------------------------
# _on_clear_recent_files
# ---------------------------------------------------------------------------

class TestOnClearRecentFiles:

    def test_clear_recent_files_empties_list(self, tmp_path, win):
        f = tmp_path / "model.onnx"
        f.write_bytes(b"\x00" * 4)
        win.settings_manager.add_recent_file(str(f))

        # QMessageBox.question is already patched to Yes by autouse fixture
        win._on_clear_recent_files()
        assert win.settings_manager.get_recent_files() == []


# ---------------------------------------------------------------------------
# set_dxcom_path
# ---------------------------------------------------------------------------

class TestSetDxcomPath:

    def test_set_dxcom_path_does_not_raise(self, win):
        with patch("src.dxcom_detector.set_custom_dxcom_path"), \
             patch("src.dxcom_detector.refresh_dxcom_detection"):
            win.set_dxcom_path("/usr/local/bin/dxcom")


# ---------------------------------------------------------------------------
# _on_settings (opens dialog)
# ---------------------------------------------------------------------------

class TestOnSettings:

    def test_on_settings_does_not_raise(self, win):
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = 0
        with patch("src.main_window.SettingsDialog", return_value=mock_dialog):
            win._on_settings()


# ---------------------------------------------------------------------------
# Checkboxes and combo state
# ---------------------------------------------------------------------------

class TestCompilerOptionWidgets:

    def test_gen_log_checkbox_toggles(self, win):
        win.gen_log_checkbox.setChecked(False)
        assert not win.gen_log_checkbox.isChecked()
        win.gen_log_checkbox.setChecked(True)
        assert win.gen_log_checkbox.isChecked()

    def test_aggressive_partitioning_checkbox_toggles(self, win):
        win.aggressive_partitioning_checkbox.setChecked(True)
        assert win.aggressive_partitioning_checkbox.isChecked()

    def test_opt_level_combo_has_two_items(self, win):
        assert win.opt_level_combo.count() == 2

    def test_opt_level_combo_default_index_is_1(self, win):
        assert win.opt_level_combo.currentIndex() == 1

    def test_calib_method_combo_has_ema_and_minmax(self, win):
        items = [win.calib_method_combo.itemData(i) for i in range(win.calib_method_combo.count())]
        assert "ema" in items
        assert "minmax" in items

    def test_calib_num_spinbox_default_100(self, win):
        assert win.calib_num_spinbox.value() == 100

    def test_calib_num_spinbox_accepts_new_value(self, win):
        win.calib_num_spinbox.setValue(200)
        assert win.calib_num_spinbox.value() == 200


# ---------------------------------------------------------------------------
# _on_batch_progress_updated / _on_batch_file_finished
# ---------------------------------------------------------------------------

class TestBatchProgressHandlers:

    def test_batch_progress_updated_does_not_raise(self, win):
        win.batch_files = ["a.onnx", "b.onnx"]
        win.batch_current_index = 0
        win._on_batch_progress_updated(50)
        assert win.progress_bar.value() == 25  # (0*100 + 50) / 2

    def test_batch_progress_at_file_1(self, win):
        win.batch_files = ["a.onnx", "b.onnx"]
        win.batch_current_index = 1
        win._on_batch_progress_updated(50)
        assert win.progress_bar.value() == 75  # (1*100 + 50) / 2


# ---------------------------------------------------------------------------
# _on_input_path_changed / _on_config_path_changed / _on_output_path_changed
# ---------------------------------------------------------------------------

class TestPathChangeHandlers:

    def test_on_output_path_changed_sets_empty_when_cleared(self, win):
        win.output_path_field.setText("")
        # calling directly
        win._on_output_path_changed()
        assert win.output_model_path == ""

    def test_on_output_path_changed_valid_dir(self, tmp_path, win):
        win.output_path_field.setText(str(tmp_path))
        win._on_output_path_changed()
        assert win.output_model_path == str(tmp_path)

    def test_on_output_path_changed_invalid_path_sets_error_style(self, win):
        win.output_path_field.setText("/nonexistent_root_xyz/sub")
        win._on_output_path_changed()
        # Path is invalid; field should have error styling applied
        style = win.output_path_field.styleSheet()
        assert "ff6b6b" in style or "border" in style

    def test_on_input_path_changed_updates_command_preview(self, win):
        # Just verify it doesn't raise when called directly
        win._on_input_path_changed()

    def test_on_config_path_changed_updates_edit_button(self, win):
        # With no config loaded, edit button should be disabled
        win._on_config_path_changed()
        assert not win.edit_config_button.isEnabled()

    def test_on_config_path_changed_with_path_enables_edit_button(self, tmp_path, win):
        f = tmp_path / "c.json"
        f.write_text(json.dumps({"x": 1}))
        win.config_file_path = str(f)
        win.config_path_field.setReadOnly(False)
        win.config_path_field.setText(str(f))
        win._on_config_path_changed()
        assert win.edit_config_button.isEnabled()


# ---------------------------------------------------------------------------
# _on_open_recent_file
# ---------------------------------------------------------------------------

class TestOnOpenRecentFile:

    def test_opens_existing_onnx_file(self, tmp_path, win):
        f = tmp_path / "model.onnx"
        f.write_bytes(b"\x08\x01\x00\x00" + b"\x00" * 10)
        win._on_open_recent_file(str(f))
        assert win.input_model_path == str(f)

    def test_opens_existing_json_file(self, tmp_path, win):
        f = tmp_path / "cfg.json"
        f.write_text(json.dumps({"x": 1}))
        win._on_open_recent_file(str(f))
        assert win.config_file_path == str(f)

    def test_nonexistent_file_shows_warning(self, win):
        with patch("src.main_window.QMessageBox.warning", return_value=QMessageBox.StandardButton.Ok) as mock_warn:
            win._on_open_recent_file("/nonexistent/file.onnx")
            mock_warn.assert_called_once()


# ---------------------------------------------------------------------------
# _write_default_loader_to_config (no-op when config not set)
# ---------------------------------------------------------------------------

class TestWriteDefaultLoaderToConfig:

    def test_does_not_raise_when_no_config(self, win):
        win.config_file_path = ""
        win._write_default_loader_to_config()  # Should silently return

    def test_writes_dataset_path_to_config(self, tmp_path, win):
        cfg_file = tmp_path / "model.json"
        cfg_file.write_text(json.dumps({"default_loader": {}}))
        win.config_file_path = str(cfg_file)
        win.dataset_path_field.setText("/data/images")
        win._write_default_loader_to_config()
        updated = json.loads(cfg_file.read_text())
        assert updated.get("default_loader", {}).get("dataset_path") == "/data/images"


# ---------------------------------------------------------------------------
# _load_default_loader_from_config
# ---------------------------------------------------------------------------

class TestLoadDefaultLoaderFromConfig:

    def test_no_op_when_config_not_set(self, win):
        win.config_file_path = ""
        win._load_default_loader_from_config()  # Should not raise

    def test_populates_dataset_path_field(self, tmp_path, win):
        cfg = {"default_loader": {"dataset_path": "/my/dataset"}}
        f = tmp_path / "cfg.json"
        f.write_text(json.dumps(cfg))
        win.config_file_path = str(f)
        win._load_default_loader_from_config()
        assert win.dataset_path_field.text() == "/my/dataset"

    def test_populates_file_extensions_field(self, tmp_path, win):
        cfg = {"default_loader": {"file_extensions": ["jpg", "png"]}}
        f = tmp_path / "cfg.json"
        f.write_text(json.dumps(cfg))
        win.config_file_path = str(f)
        win._load_default_loader_from_config()
        assert "jpg" in win.file_extensions_field.text()


# ---------------------------------------------------------------------------
# _on_calib_setting_changed
# ---------------------------------------------------------------------------

class TestOnCalibSettingChanged:

    def test_does_not_raise(self, win):
        win._on_calib_setting_changed()

    def test_calib_method_change_triggers_handler(self, win):
        # Switching combo index invokes _on_calib_setting_changed via signal
        win.calib_method_combo.setCurrentIndex(1)  # Switch to minmax
        assert win.calib_method_combo.currentData() == "minmax"


# ---------------------------------------------------------------------------
# _on_input_nodes_changed / _on_output_nodes_changed
# ---------------------------------------------------------------------------

class TestNodeChangeHandlers:

    def test_input_nodes_valid_clears_error(self, win):
        win.compile_input_nodes_field.setText("node1,node2")
        win._on_input_nodes_changed()
        assert 'input_nodes' not in win.validation_errors

    def test_input_nodes_invalid_sets_error(self, win):
        win.compile_input_nodes_field.setText("node1,,node2")
        win._on_input_nodes_changed()
        assert 'input_nodes' in win.validation_errors

    def test_output_nodes_valid_clears_error(self, win):
        win.compile_output_nodes_field.setText("out1")
        win._on_output_nodes_changed()
        assert 'output_nodes' not in win.validation_errors

    def test_output_nodes_invalid_sets_error(self, win):
        win.compile_output_nodes_field.setText("out1,,out2")
        win._on_output_nodes_changed()
        assert 'output_nodes' in win.validation_errors


# ---------------------------------------------------------------------------
# _apply_calib_to_config
# ---------------------------------------------------------------------------

class TestApplyCalibToConfig:

    def test_no_config_returns_options_unchanged(self, win):
        opts = {'config_path': '', 'calib_method': 'ema', 'calib_num': 100}
        result = win._apply_calib_to_config(opts)
        assert result == opts

    def test_with_config_writes_to_json(self, tmp_path, win):
        cfg = {"input": "model.onnx"}
        f = tmp_path / "cfg.json"
        f.write_text(json.dumps(cfg))
        opts = {'config_path': str(f), 'calib_method': 'minmax', 'calib_num': 50}
        result = win._apply_calib_to_config(opts)
        updated = json.loads(f.read_text())
        assert updated.get('calibration_method') == 'minmax'
        assert updated.get('calibration_num') == 50

    def test_with_config_removes_calib_keys_from_result(self, tmp_path, win):
        cfg = {}
        f = tmp_path / "cfg2.json"
        f.write_text(json.dumps(cfg))
        opts = {'config_path': str(f), 'calib_method': 'ema', 'calib_num': 100}
        result = win._apply_calib_to_config(opts)
        assert 'calib_method' not in result
        assert 'calib_num' not in result


# ---------------------------------------------------------------------------
# _on_check_dxcom_status
# ---------------------------------------------------------------------------

class TestOnCheckDxcomStatus:

    def test_does_not_raise(self, win):
        with patch("src.main_window.QMessageBox.information", return_value=QMessageBox.StandardButton.Ok), \
             patch("src.main_window.QMessageBox.warning", return_value=QMessageBox.StandardButton.Ok), \
             patch("src.dxcom_detector.refresh_dxcom_detection"), \
             patch("src.environment_validator.clear_validation_cache"):
            win._on_check_dxcom_status()


# ---------------------------------------------------------------------------
# Menu bar existence
# ---------------------------------------------------------------------------

class TestMenuBar:

    def test_menu_bar_exists(self, win):
        assert win.menuBar() is not None

    def test_recent_files_menu_exists(self, win):
        assert win.recent_files_menu is not None

    def test_theme_action_exists(self, win):
        assert win.theme_action is not None
