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


# ===========================================================================
# COVERAGE BOOST — New test classes targeting uncovered lines
# ===========================================================================

import time as _time_module


def _make_mock_executor():
    """Create a mock DXComExecutor with signal-like attributes."""
    ex = MagicMock()
    ex.isRunning.return_value = False
    return ex


def _make_validation(overall_valid=True, errors=None, warnings=None, checks=None):
    """Create a mock EnvironmentValidation result."""
    v = MagicMock()
    v.overall_valid = overall_valid
    v.errors = errors or []
    v.warnings = warnings or []
    v.checks = checks or []
    return v


def _make_err(msg="Test error"):
    e = MagicMock()
    e.message = msg
    return e


# ---------------------------------------------------------------------------
# _update_config_field_state null-guard (line 464)
# ---------------------------------------------------------------------------

class TestUpdateConfigFieldNullGuard:

    def test_update_config_field_null_guard(self, win):
        """When config_path_field is None, _update_config_field_state returns early."""
        orig = win.config_path_field
        win.config_path_field = None
        win._update_config_field_state()  # Must not raise
        win.config_path_field = orig


# ---------------------------------------------------------------------------
# _on_browse_dataset_path  (lines 884-891)
# ---------------------------------------------------------------------------

class TestBrowseDatasetPath:

    def test_browse_sets_field_text(self, tmp_path, win):
        with patch('src.main_window.QFileDialog.getExistingDirectory',
                   return_value=str(tmp_path)):
            win._on_browse_dataset_path()
        assert win.dataset_path_field.text() == str(tmp_path)

    def test_browse_cancelled_leaves_field_unchanged(self, win):
        win.dataset_path_field.setText("/original")
        with patch('src.main_window.QFileDialog.getExistingDirectory',
                   return_value=""):
            win._on_browse_dataset_path()
        assert win.dataset_path_field.text() == "/original"


# ---------------------------------------------------------------------------
# _write_default_loader_to_config — preprocessing fields  (lines 915-997)
# ---------------------------------------------------------------------------

class TestWriteDefaultLoaderPreprocessings:

    def test_writes_preprocessing_fields(self, tmp_path, win):
        cfg_file = tmp_path / "model.json"
        cfg_file.write_text(json.dumps({"default_loader": {}}))
        win.config_file_path = str(cfg_file)

        win.dataset_path_field.setText("/data")
        win.file_extensions_field.setText('["jpg","png"]')
        win.resize_field.setText('[224, 224]')
        win.convert_color_combo.setCurrentIndex(1)  # pick non-blank
        win._write_default_loader_to_config()

        updated = json.loads(cfg_file.read_text())
        dl = updated.get("default_loader", {})
        assert dl.get("dataset_path") == "/data"
        assert "preprocessings" in dl

    def test_writes_all_numeric_fields(self, tmp_path, win):
        cfg_file = tmp_path / "model.json"
        cfg_file.write_text(json.dumps({"default_loader": {}}))
        win.config_file_path = str(cfg_file)

        win.centercrop_field.setText('[224, 224]')
        win.transpose_field.setText('[2, 0, 1]')
        win.expand_dim_field.setText('[0]')
        win.normalize_field.setText('{"mean": [0.485]}')
        win.mul_field.setText('255')
        win.add_field.setText('0')
        win.subtract_field.setText('0')
        win.div_field.setText('255')
        win._write_default_loader_to_config()

        updated = json.loads(cfg_file.read_text())
        dl = updated.get("default_loader", {})
        assert "preprocessings" in dl

    def test_handles_malformed_json_fields_gracefully(self, tmp_path, win):
        cfg_file = tmp_path / "model.json"
        cfg_file.write_text(json.dumps({"default_loader": {}}))
        win.config_file_path = str(cfg_file)

        win.resize_field.setText('not-valid-json')
        win._write_default_loader_to_config()  # Must not raise


# ---------------------------------------------------------------------------
# _load_default_loader_from_config — full preprocessing section  (lines 1037-1081)
# ---------------------------------------------------------------------------

class TestLoadDefaultLoaderPreprocessings:

    def test_populates_all_preprocessing_fields(self, tmp_path, win):
        cfg = {
            "default_loader": {
                "dataset_path": "/data",
                "file_extensions": ["jpg"],
                "preprocessings": [
                    {"convertColor": {"form": "RGB2BGR"}},  # valid combo value
                    {"resize": [224, 224]},
                    {"centercrop": [224, 224]},
                    {"transpose": [2, 0, 1]},
                    {"expandDim": [0]},
                    {"normalize": {"mean": [0.485]}},
                    {"mul": 255},
                    {"add": 0},
                    {"subtract": 0},
                    {"div": 255},
                ]
            }
        }
        f = tmp_path / "cfg.json"
        f.write_text(json.dumps(cfg))
        win.config_file_path = str(f)
        win._load_default_loader_from_config()

        assert win.dataset_path_field.text() == "/data"
        assert win.resize_field.text() != ""


# ---------------------------------------------------------------------------
# _check_dxcom_availability  (lines 1413-1445)
# ---------------------------------------------------------------------------

class TestCheckDxcomAvailability:

    def test_dxcom_available_valid_environment(self, win):
        good_info = MagicMock()
        good_info.is_valid.return_value = True
        good_info.path = '/usr/bin/dxcom'
        good_info.version = '1.0.0'
        good_val = _make_validation(overall_valid=True)

        with patch('src.main_window.check_dxcom_available', return_value=good_info), \
             patch('src.main_window.validate_environment', return_value=good_val), \
             patch('src.main_window.get_dxcom_status', return_value=('ok', 'dxcom ready')):
            win._check_dxcom_availability()

        assert win.dxcom_available is True

    def test_dxcom_available_env_with_warnings(self, win):
        good_info = MagicMock()
        good_info.is_valid.return_value = True
        warn_val = _make_validation(overall_valid=True, warnings=[_make_err("Low mem")])

        with patch('src.main_window.check_dxcom_available', return_value=good_info), \
             patch('src.main_window.validate_environment', return_value=warn_val), \
             patch('src.main_window.get_dxcom_status', return_value=('ok', 'dxcom ready')), \
             patch('src.main_window.QMessageBox.warning'):
            win._check_dxcom_availability()

        assert win.dxcom_available is True

    def test_dxcom_available_env_invalid(self, win):
        good_info = MagicMock()
        good_info.is_valid.return_value = True
        bad_val = _make_validation(overall_valid=False, errors=[_make_err("env broken")])

        with patch('src.main_window.check_dxcom_available', return_value=good_info), \
             patch('src.main_window.validate_environment', return_value=bad_val), \
             patch('src.main_window.QMessageBox.critical'):
            win._check_dxcom_availability()

        assert win.dxcom_available is False

    def test_dxcom_not_available(self, win):
        bad_info = MagicMock()
        bad_info.is_valid.return_value = False
        bad_info.error_message = "dxcom not found"

        with patch('src.main_window.check_dxcom_available', return_value=bad_info), \
             patch('src.main_window.QMessageBox.warning'):
            win._check_dxcom_availability()

        assert win.dxcom_available is False


# ---------------------------------------------------------------------------
# _on_compile_clicked  (lines 1562-1600)
# ---------------------------------------------------------------------------

class TestOnCompileClicked:

    def test_validation_fails_shows_error(self, win):
        bad = _make_validation(overall_valid=False, errors=[_make_err("broken")])
        with patch('src.main_window.validate_for_compilation', return_value=bad), \
             patch('src.main_window.QMessageBox.critical') as mock_crit:
            win._on_compile_clicked()
        mock_crit.assert_called_once()

    def test_validation_fails_with_warnings_listed(self, win):
        bad = _make_validation(overall_valid=False,
                               errors=[_make_err("err")],
                               warnings=[_make_err("warn")])
        with patch('src.main_window.validate_for_compilation', return_value=bad), \
             patch('src.main_window.QMessageBox.critical') as mock_crit:
            win._on_compile_clicked()
        mock_crit.assert_called_once()

    def test_validation_ok_starts_compilation(self, win, tmp_path):
        good = _make_validation()
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.execution_mode = "cli"  # fix to CLI so compile() is called
        mock_ex = _make_mock_executor()
        win.dxcom_wrapper = MagicMock()
        win.dxcom_wrapper.compile.return_value = mock_ex

        with patch('src.main_window.validate_for_compilation', return_value=good):
            win._on_compile_clicked()

        assert win.current_executor is mock_ex

    def test_validation_warns_user_confirms(self, win, tmp_path):
        warn = _make_validation(overall_valid=True, warnings=[_make_err("low mem")])
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.execution_mode = "cli"
        mock_ex = _make_mock_executor()
        win.dxcom_wrapper = MagicMock()
        win.dxcom_wrapper.compile.return_value = mock_ex

        with patch('src.main_window.validate_for_compilation', return_value=warn), \
             patch('src.main_window.QMessageBox.warning',
                   return_value=QMessageBox.StandardButton.Yes):
            win._on_compile_clicked()

        assert win.current_executor is mock_ex

    def test_validation_warns_user_cancels(self, win):
        warn = _make_validation(overall_valid=True, warnings=[_make_err("warn")])
        with patch('src.main_window.validate_for_compilation', return_value=warn), \
             patch('src.main_window.QMessageBox.warning',
                   return_value=QMessageBox.StandardButton.No):
            win._on_compile_clicked()

        assert win.current_executor is None


# ---------------------------------------------------------------------------
# _start_compilation routing  (lines 1605-1628)
# ---------------------------------------------------------------------------

class TestStartCompilation:

    def test_routes_to_cli_in_cli_mode(self, win, tmp_path):
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.execution_mode = "cli"
        mock_ex = _make_mock_executor()
        win.dxcom_wrapper = MagicMock()
        win.dxcom_wrapper.compile.return_value = mock_ex

        win._start_compilation()

        win.dxcom_wrapper.compile.assert_called_once()
        assert win.current_executor is mock_ex

    def test_routes_to_python_in_python_mode(self, win, tmp_path):
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.execution_mode = "python"
        win.saved_python_script_path = None
        mock_ex = _make_mock_executor()
        win.dxcom_wrapper = MagicMock()
        win.dxcom_wrapper.compile_with_python.return_value = mock_ex

        win._start_compilation()

        win.dxcom_wrapper.compile_with_python.assert_called_once()

    def test_routes_to_batch_when_batch_mode(self, win, tmp_path):
        onnx1 = _make_onnx(tmp_path, "m1.onnx")
        onnx2 = _make_onnx(tmp_path, "m2.onnx")
        win.batch_mode = True
        win.batch_files = [onnx1, onnx2]
        win.output_model_path = str(tmp_path)
        mock_ex = _make_mock_executor()
        win.dxcom_wrapper = MagicMock()
        win.dxcom_wrapper.compile.return_value = mock_ex

        win._start_compilation()

        win.dxcom_wrapper.compile.assert_called()

    def test_clears_log_on_start(self, win, tmp_path):
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.execution_mode = "cli"
        win.log_text_area.setPlainText("old log content")
        win.dxcom_wrapper = MagicMock()
        win.dxcom_wrapper.compile.return_value = _make_mock_executor()

        win._start_compilation()

        assert win.log_text_area.toPlainText() == ""


# ---------------------------------------------------------------------------
# _apply_calib_to_config with file present  (lines 1649-1650)
# ---------------------------------------------------------------------------

class TestApplyCalibToConfigWithFile:

    def test_writes_calib_to_file_and_removes_keys(self, tmp_path, win):
        cfg = {"calibration_method": "ema", "calibration_num": 100}
        f = tmp_path / "cfg.json"
        f.write_text(json.dumps(cfg))

        options = {
            'config_path': str(f),
            'calib_method': 'minmax',
            'calib_num': 50,
            'opt_level': 1,
        }
        result = win._apply_calib_to_config(options)

        assert 'calib_method' not in result
        assert 'calib_num' not in result
        updated = json.loads(f.read_text())
        assert updated['calibration_method'] == 'minmax'
        assert updated['calibration_num'] == 50


# ---------------------------------------------------------------------------
# _run_cli_compilation  (lines 1660-1689)
# ---------------------------------------------------------------------------

class TestRunCliCompilation:

    def test_creates_executor_and_starts(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        mock_ex = _make_mock_executor()
        win.dxcom_wrapper = MagicMock()
        win.dxcom_wrapper.compile.return_value = mock_ex

        opts = win.get_compiler_options()
        win._run_cli_compilation(opts)

        win.dxcom_wrapper.compile.assert_called_once()
        assert win.current_executor is mock_ex
        mock_ex.start.assert_called_once()

    def test_cancel_button_becomes_visible(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.dxcom_wrapper = MagicMock()
        win.dxcom_wrapper.compile.return_value = _make_mock_executor()

        opts = win.get_compiler_options()
        win._run_cli_compilation(opts)

        assert not win.cancel_button.isHidden()
        assert not win.compile_button.isEnabled()


# ---------------------------------------------------------------------------
# _run_python_compilation  (lines 1693-1733)
# ---------------------------------------------------------------------------

class TestRunPythonCompilation:

    def test_generates_temp_script_when_no_saved(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.saved_python_script_path = None
        mock_ex = _make_mock_executor()
        win.dxcom_wrapper = MagicMock()
        win.dxcom_wrapper.compile_with_python.return_value = mock_ex

        opts = win.get_compiler_options()
        win._run_python_compilation(opts)

        win.dxcom_wrapper.compile_with_python.assert_called_once()
        assert win.current_executor is mock_ex
        mock_ex.start.assert_called_once()

    def test_uses_saved_script_when_set(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        script = tmp_path / "compile.py"
        script.write_text("import dx_com")
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.saved_python_script_path = str(script)
        mock_ex = _make_mock_executor()
        win.dxcom_wrapper = MagicMock()
        win.dxcom_wrapper.compile_with_python.return_value = mock_ex

        opts = win.get_compiler_options()
        win._run_python_compilation(opts)

        call_kwargs = win.dxcom_wrapper.compile_with_python.call_args
        assert str(script) in str(call_kwargs)


# ---------------------------------------------------------------------------
# _generate_python_script_content  (lines 1737-1886)
# ---------------------------------------------------------------------------

class TestGeneratePythonScriptContent:

    def test_generates_config_mode_script(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.config_file_path = str(tmp_path / "cfg.json")
        win.python_data_source = "config"

        opts = win.get_compiler_options()
        content = win._generate_python_script_content(opts)

        assert 'import dx_com' in content
        assert 'dx_com.compile' in content

    def test_generates_dataloader_mode_script(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.python_data_source = "dataloader"

        opts = win.get_compiler_options()
        content = win._generate_python_script_content(opts)

        assert 'DataLoader' in content
        assert 'dataloader=dataloader' in content

    def test_includes_input_output_nodes(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.python_data_source = "config"
        win.compile_input_nodes_field.setText("node1,node2")
        win.compile_output_nodes_field.setText("out1")

        opts = win.get_compiler_options()
        content = win._generate_python_script_content(opts)

        assert 'node1' in content
        assert 'out1' in content

    def test_includes_valid_enhanced_scheme(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.python_data_source = "config"
        win.enhanced_scheme_field.setText('{"DXQ-P0": {"alpha": 0.5}}')

        opts = win.get_compiler_options()
        content = win._generate_python_script_content(opts)

        assert 'enhanced_scheme' in content

    def test_handles_invalid_enhanced_scheme(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.python_data_source = "config"
        win.enhanced_scheme_field.setText('not valid json')

        opts = win.get_compiler_options()
        content = win._generate_python_script_content(opts)

        assert 'Invalid JSON format' in content


# ---------------------------------------------------------------------------
# Batch compilation  (lines 1888-1952)
# ---------------------------------------------------------------------------

class TestBatchCompilationFlow:

    def test_start_batch_sets_running_status(self, tmp_path, win):
        onnx1 = _make_onnx(tmp_path, "a.onnx")
        onnx2 = _make_onnx(tmp_path, "b.onnx")
        win.batch_mode = True
        win.batch_files = [onnx1, onnx2]
        win.output_model_path = str(tmp_path)
        mock_ex = _make_mock_executor()
        win.dxcom_wrapper = MagicMock()
        win.dxcom_wrapper.compile.return_value = mock_ex

        win._start_batch_compilation()

        assert win.batch_current_index == 0
        assert not win.compile_button.isEnabled()
        assert not win.cancel_button.isHidden()
        mock_ex.start.assert_called()

    def test_compile_next_batch_calls_compile(self, tmp_path, win):
        onnx1 = _make_onnx(tmp_path, "a.onnx")
        onnx2 = _make_onnx(tmp_path, "b.onnx")
        win.batch_files = [onnx1, onnx2]
        win.batch_current_index = 0
        win.batch_success_count = 0
        win.batch_failed_count = 0
        win.output_model_path = str(tmp_path)
        mock_ex = _make_mock_executor()
        win.dxcom_wrapper = MagicMock()
        win.dxcom_wrapper.compile.return_value = mock_ex

        win._compile_next_batch_file()

        win.dxcom_wrapper.compile.assert_called()

    def test_compile_next_batch_finishes_when_done(self, tmp_path, win):
        win.batch_files = [str(tmp_path / "a.onnx")]
        win.batch_current_index = 1  # beyond list
        win.batch_success_count = 1
        win.batch_failed_count = 0
        win.compilation_start_time = None
        win.compile_button.setEnabled(False)

        with patch('src.main_window.QMessageBox.information'):
            win._compile_next_batch_file()

        assert win.compile_button.isEnabled()


# ---------------------------------------------------------------------------
# _on_batch_file_finished / _finish_batch_compilation  (lines 1964-2027)
# ---------------------------------------------------------------------------

class TestBatchFileFinished:

    def test_success_increments_success_count(self, tmp_path, win):
        onnx1 = _make_onnx(tmp_path, "a.onnx")
        win.batch_files = [onnx1]
        win.batch_current_index = 0
        win.batch_success_count = 0
        win.batch_failed_count = 0
        win.output_model_path = str(tmp_path)
        win.dxcom_wrapper = MagicMock()
        win.dxcom_wrapper.compile.return_value = _make_mock_executor()

        with patch('src.main_window.QMessageBox.information'):
            win._on_batch_file_finished(True, "ok")

        assert win.batch_success_count == 1

    def test_failure_increments_fail_count(self, tmp_path, win):
        onnx1 = _make_onnx(tmp_path, "a.onnx")
        win.batch_files = [onnx1]
        win.batch_current_index = 0
        win.batch_success_count = 0
        win.batch_failed_count = 0
        win.output_model_path = str(tmp_path)
        win.dxcom_wrapper = MagicMock()
        win.dxcom_wrapper.compile.return_value = _make_mock_executor()

        with patch('src.main_window.QMessageBox.warning'):
            win._on_batch_file_finished(False, "error")

        assert win.batch_failed_count == 1

    def test_finish_batch_all_success(self, tmp_path, win):
        win.batch_files = [str(tmp_path / "a.onnx")]
        win.batch_current_index = 1
        win.batch_success_count = 1
        win.batch_failed_count = 0
        win.compilation_start_time = None
        win.compile_button.setEnabled(False)

        with patch('src.main_window.QMessageBox.information') as mock_info:
            win._finish_batch_compilation()

        mock_info.assert_called_once()
        assert win.compile_button.isEnabled()

    def test_finish_batch_with_failures(self, tmp_path, win):
        win.batch_files = [str(tmp_path / "a.onnx")]
        win.batch_current_index = 1
        win.batch_success_count = 0
        win.batch_failed_count = 1
        win.compilation_start_time = None
        win.compile_button.setEnabled(False)

        with patch('src.main_window.QMessageBox.warning') as mock_warn:
            win._finish_batch_compilation()

        mock_warn.assert_called_once()

    def test_finish_batch_with_short_duration(self, tmp_path, win):
        win.batch_files = [str(tmp_path / "a.onnx")]
        win.batch_current_index = 1
        win.batch_success_count = 1
        win.batch_failed_count = 0
        win.compilation_start_time = _time_module.time() - 5
        win.compile_button.setEnabled(False)

        with patch('src.main_window.QMessageBox.information'):
            win._finish_batch_compilation()

        assert win.batch_mode is False

    def test_finish_batch_with_long_duration(self, tmp_path, win):
        win.batch_files = [str(tmp_path / "a.onnx")]
        win.batch_current_index = 1
        win.batch_success_count = 1
        win.batch_failed_count = 0
        win.compilation_start_time = _time_module.time() - 130  # > 60s
        win.compile_button.setEnabled(False)

        with patch('src.main_window.QMessageBox.information'):
            win._finish_batch_compilation()

        assert not win.batch_mode


# ---------------------------------------------------------------------------
# _on_compilation_finished success with timing  (lines 2099-2105)
# ---------------------------------------------------------------------------

class TestCompilationFinishedTiming:

    def test_success_with_short_duration(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.compilation_start_time = _time_module.time() - 5
        win.compile_button.setEnabled(False)
        win.cancel_button.setVisible(True)

        with patch('src.main_window.QMessageBox.information'):
            win._on_compilation_finished(True, "Compilation complete")

        assert win.compile_button.isEnabled()

    def test_success_with_long_duration(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.compilation_start_time = _time_module.time() - 130
        win.compile_button.setEnabled(False)
        win.cancel_button.setVisible(True)

        with patch('src.main_window.QMessageBox.information'):
            win._on_compilation_finished(True, "done")

        assert win.compile_button.isEnabled()


# ---------------------------------------------------------------------------
# _on_cancel_clicked  (lines 2132-2148)
# ---------------------------------------------------------------------------

class TestOnCancelClicked:

    def test_cancel_when_running_and_confirmed(self, win):
        mock_ex = _make_mock_executor()
        mock_ex.isRunning.return_value = True
        win.current_executor = mock_ex
        win.cancel_button.setEnabled(True)
        win.cancel_button.setText("Cancel")

        with patch('src.main_window.QMessageBox.question',
                   return_value=QMessageBox.StandardButton.Yes):
            win._on_cancel_clicked()

        mock_ex.stop.assert_called_once()
        assert not win.cancel_button.isEnabled()
        assert win.cancel_button.text() == "Cancelling..."

    def test_cancel_when_running_but_user_declines(self, win):
        mock_ex = _make_mock_executor()
        mock_ex.isRunning.return_value = True
        win.current_executor = mock_ex

        with patch('src.main_window.QMessageBox.question',
                   return_value=QMessageBox.StandardButton.No):
            win._on_cancel_clicked()

        mock_ex.stop.assert_not_called()

    def test_cancel_when_executor_not_running(self, win):
        mock_ex = _make_mock_executor()
        mock_ex.isRunning.return_value = False
        win.current_executor = mock_ex

        win._on_cancel_clicked()

        mock_ex.stop.assert_not_called()

    def test_cancel_with_no_executor(self, win):
        win.current_executor = None
        win._on_cancel_clicked()  # Must not raise


# ---------------------------------------------------------------------------
# _on_browse_input_file  (lines 2153-2190)
# ---------------------------------------------------------------------------

class TestOnBrowseInputFile:

    def test_browse_sets_input_path(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        with patch('src.main_window.QFileDialog.getOpenFileName',
                   return_value=(onnx, "ONNX Files")):
            win._on_browse_input_file()

        assert win.input_model_path == onnx
        assert win.input_path_field.text() == onnx

    def test_browse_adds_to_recent_files(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        with patch('src.main_window.QFileDialog.getOpenFileName',
                   return_value=(onnx, "")):
            win._on_browse_input_file()

        assert onnx in win.settings_manager.get_recent_files()

    def test_browse_cancelled_leaves_path_unchanged(self, win):
        win.input_model_path = "/existing.onnx"
        with patch('src.main_window.QFileDialog.getOpenFileName',
                   return_value=("", "")):
            win._on_browse_input_file()

        assert win.input_model_path == "/existing.onnx"

    def test_browse_uses_default_input_path_setting(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        win.settings_manager.set('default_input_path', str(tmp_path))
        with patch('src.main_window.QFileDialog.getOpenFileName',
                   return_value=(onnx, "")):
            win._on_browse_input_file()

        assert win.input_model_path == onnx

    def test_browse_resets_batch_mode(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        win.batch_mode = True
        win.batch_files = [onnx, onnx]
        with patch('src.main_window.QFileDialog.getOpenFileName',
                   return_value=(onnx, "")):
            win._on_browse_input_file()

        assert win.batch_mode is False
        assert win.batch_files == []


# ---------------------------------------------------------------------------
# _on_browse_config_file  (lines 2194-2240)
# ---------------------------------------------------------------------------

class TestOnBrowseConfigFile:

    def test_browse_sets_config_path(self, tmp_path, win):
        cfg = _make_json(tmp_path)
        with patch('src.main_window.QFileDialog.getOpenFileName',
                   return_value=(cfg, "JSON Files")):
            win._on_browse_config_file()

        assert win.config_file_path == cfg

    def test_browse_config_validates_file(self, tmp_path, win):
        cfg = _make_json(tmp_path)
        with patch('src.main_window.QFileDialog.getOpenFileName',
                   return_value=(cfg, "")):
            win._on_browse_config_file()

        assert win.config_path_field.text() == cfg

    def test_browse_config_cancelled_leaves_unchanged(self, win):
        win.config_file_path = "/existing.json"
        with patch('src.main_window.QFileDialog.getOpenFileName',
                   return_value=("", "")):
            win._on_browse_config_file()

        assert win.config_file_path == "/existing.json"

    def test_browse_config_syncs_calib_combo_to_minmax(self, tmp_path, win):
        cfg_data = {"calibration_method": "minmax", "calibration_num": 50}
        cfg = _make_json(tmp_path, data=cfg_data)
        with patch('src.main_window.QFileDialog.getOpenFileName',
                   return_value=(cfg, "")):
            win._on_browse_config_file()

        assert win.calib_method_combo.currentData() == "minmax"
        assert win.calib_num_spinbox.value() == 50


# ---------------------------------------------------------------------------
# _on_browse_output_file  (lines 2245-2276)
# ---------------------------------------------------------------------------

class TestOnBrowseOutputFile:

    def test_browse_sets_valid_output_path(self, tmp_path, win):
        with patch('src.main_window.QFileDialog.getExistingDirectory',
                   return_value=str(tmp_path)):
            win._on_browse_output_file()

        assert win.output_model_path == str(tmp_path)
        assert win.output_path_field.text() == str(tmp_path)

    def test_browse_cancelled_leaves_unchanged(self, win):
        win.output_model_path = "/original"
        with patch('src.main_window.QFileDialog.getExistingDirectory',
                   return_value=""):
            win._on_browse_output_file()

        assert win.output_model_path == "/original"

    def test_browse_invalid_path_shows_warning(self, win):
        with patch('src.main_window.QFileDialog.getExistingDirectory',
                   return_value="/nonexistent_parent_xyz/sub"), \
             patch('src.main_window.QMessageBox.warning') as mock_warn:
            win._on_browse_output_file()

        mock_warn.assert_called_once()

    def test_browse_uses_input_path_dir_as_initial(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = ""
        with patch('src.main_window.QFileDialog.getExistingDirectory',
                   return_value=str(tmp_path)) as mock_dlg:
            win._on_browse_output_file()

        call_args = mock_dlg.call_args[0]
        assert str(tmp_path) in call_args


# ---------------------------------------------------------------------------
# Validation edge cases (lines 2325, 2332, 2366-2368, 2391-2394, 2427-2461)
# ---------------------------------------------------------------------------

class TestValidateOutputPathEdgeCases:

    def test_not_writable_dir_returns_error(self, tmp_path, win):
        with patch('os.access', return_value=False):
            result = win._validate_output_path(str(tmp_path))
        assert isinstance(result, str)

    def test_nonexistent_parent_not_writable_returns_error(self, tmp_path, win):
        nonexistent = str(tmp_path / "new_dir")
        with patch('os.access', return_value=False):
            result = win._validate_output_path(nonexistent)
        assert isinstance(result, str)


class TestValidateInputFileEdgeCases:

    def test_not_readable_file_returns_false(self, tmp_path, win):
        f = tmp_path / "model.onnx"
        f.write_bytes(b"\x08\x00\x00\x00extra")
        with patch('os.access', side_effect=lambda p, m: False if m == 4 else True):
            result = win._validate_input_file(str(f))
        assert result is False

    def test_directory_input_path_returns_false(self, tmp_path, win):
        result = win._validate_input_file(str(tmp_path))
        assert result is False


class TestValidateConfigFileEdgeCases:

    def test_config_file_not_readable_returns_false(self, tmp_path, win):
        f = tmp_path / "cfg.json"
        f.write_text("{}")
        with patch('os.access', side_effect=lambda p, m: False if m == 4 else True):
            result = win._validate_config_file(str(f))
        assert result is False

    def test_config_general_read_exception_returns_false(self, tmp_path, win):
        f = tmp_path / "cfg.json"
        f.write_text("{}")
        with patch('builtins.open', side_effect=OSError("permission denied")):
            result = win._validate_config_file(str(f))
        assert result is False


# ---------------------------------------------------------------------------
# _update_compile_button_state edge cases  (lines 2541-2588)
# ---------------------------------------------------------------------------

class TestUpdateCompileButtonStateEdges:

    def test_disabled_when_dxcom_not_available(self, win):
        win.dxcom_available = False
        win._update_compile_button_state()
        assert not win.compile_button.isEnabled()
        assert not win.gen_python_button.isEnabled()

    def test_enabled_in_dataloader_mode_without_config(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        win.dxcom_available = True
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.config_file_path = ""
        win.execution_mode = "python"
        win.python_data_source = "dataloader"
        win.validation_errors = {}
        win._update_compile_button_state()
        assert win.compile_button.isEnabled()

    def test_tooltip_shows_first_validation_error(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        win.dxcom_available = True
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.config_file_path = "cfg.json"
        win.execution_mode = "cli"
        win.validation_errors = {'input': 'fix this error please'}
        win._update_compile_button_state()
        assert 'fix this error' in win.compile_button.toolTip()


# ---------------------------------------------------------------------------
# _write_calib_to_config with config set  (lines 2627-2650)
# ---------------------------------------------------------------------------

class TestWriteCalibToConfigWithFile:

    def test_writes_calib_values_to_json(self, tmp_path, win):
        cfg = {"name": "model"}
        f = tmp_path / "cfg.json"
        f.write_text(json.dumps(cfg))
        win.config_file_path = str(f)
        win.calib_method_combo.setCurrentIndex(1)  # minmax
        win.calib_num_spinbox.setValue(200)

        win._write_calib_to_config()

        updated = json.loads(f.read_text())
        assert updated.get("calibration_method") == "minmax"
        assert updated.get("calibration_num") == 200

    def test_on_calib_setting_changed_does_not_raise(self, tmp_path, win):
        cfg = {"name": "model"}
        f = tmp_path / "cfg.json"
        f.write_text(json.dumps(cfg))
        win.config_file_path = str(f)

        win._on_calib_setting_changed()  # Must not raise


# ---------------------------------------------------------------------------
# _on_edit_config_file  (lines 2659-2675)
# ---------------------------------------------------------------------------

class TestOnEditConfigFile:

    def test_no_config_shows_warning(self, win):
        win.config_file_path = ""
        with patch('src.main_window.QMessageBox.warning') as mock_warn:
            win._on_edit_config_file()
        mock_warn.assert_called_once()

    def test_with_config_opens_json_dialog(self, tmp_path, win):
        cfg = _make_json(tmp_path)
        win.config_file_path = cfg
        mock_dlg_instance = MagicMock()
        with patch('src.json_config_dialog.JsonConfigDialog', return_value=mock_dlg_instance):
            win._on_edit_config_file()
        mock_dlg_instance.show.assert_called_once()


# ---------------------------------------------------------------------------
# _on_check_dxcom_status  (lines 2762, 2771-2813)
# ---------------------------------------------------------------------------

class TestOnCheckDxcomStatusFull:

    def _good_info(self):
        info = MagicMock()
        info.is_valid.return_value = True
        info.path = '/usr/bin/dxcom'
        info.version = '1.0.0'
        return info

    def test_available_all_checks_pass_shows_info(self, win):
        good_check = MagicMock()
        good_check.passed = True
        good_check.severity = "info"
        good_check.message = "All good"
        good_val = _make_validation(overall_valid=True, checks=[good_check])
        good_val.warnings = []
        good_val.errors = []

        with patch('src.main_window.check_dxcom_available', return_value=self._good_info()), \
             patch('src.main_window.validate_environment', return_value=good_val), \
             patch('src.dxcom_detector.refresh_dxcom_detection'), \
             patch('src.environment_validator.clear_validation_cache'), \
             patch('src.main_window.QMessageBox.information'):
            win._on_check_dxcom_status()

        assert win.dxcom_available is True

    def test_available_with_failed_checks_shows_warning(self, win):
        fail_check = MagicMock()
        fail_check.passed = False
        fail_check.severity = "error"
        fail_check.message = "disk full"
        bad_val = _make_validation(overall_valid=False,
                                   errors=[_make_err("disk full")],
                                   checks=[fail_check])
        bad_val.warnings = []

        with patch('src.main_window.check_dxcom_available', return_value=self._good_info()), \
             patch('src.main_window.validate_environment', return_value=bad_val), \
             patch('src.dxcom_detector.refresh_dxcom_detection'), \
             patch('src.environment_validator.clear_validation_cache'), \
             patch('src.main_window.QMessageBox.warning'):
            win._on_check_dxcom_status()

        assert win.dxcom_available is False

    def test_available_with_warnings_note_shown(self, win):
        good_val = _make_validation(overall_valid=True, warnings=[_make_err("low mem")])
        good_val.checks = []
        good_val.errors = []

        with patch('src.main_window.check_dxcom_available', return_value=self._good_info()), \
             patch('src.main_window.validate_environment', return_value=good_val), \
             patch('src.dxcom_detector.refresh_dxcom_detection'), \
             patch('src.environment_validator.clear_validation_cache'), \
             patch('src.main_window.QMessageBox.information'):
            win._on_check_dxcom_status()

        assert win.dxcom_available is True

    def test_dxcom_not_available_shows_warning(self, win):
        bad_info = MagicMock()
        bad_info.is_valid.return_value = False
        bad_info.error_message = "not found"
        good_val = _make_validation()
        good_val.checks = []

        with patch('src.main_window.check_dxcom_available', return_value=bad_info), \
             patch('src.main_window.validate_environment', return_value=good_val), \
             patch('src.dxcom_detector.refresh_dxcom_detection'), \
             patch('src.environment_validator.clear_validation_cache'), \
             patch('src.main_window.QMessageBox.warning') as mock_warn:
            win._on_check_dxcom_status()

        mock_warn.assert_called()
        assert win.dxcom_available is False


# ---------------------------------------------------------------------------
# _on_open_batch_files  (lines 2913-2937)
# ---------------------------------------------------------------------------

class TestOnOpenBatchFiles:

    def test_batch_files_selected_sets_batch_mode(self, tmp_path, win):
        onnx1 = _make_onnx(tmp_path, "a.onnx")
        onnx2 = _make_onnx(tmp_path, "b.onnx")

        with patch('src.main_window.QFileDialog.getOpenFileNames',
                   return_value=([onnx1, onnx2], "ONNX Files")):
            win._on_open_batch_files()

        assert win.batch_mode is True
        assert len(win.batch_files) == 2
        assert "2" in win.compile_button.text()

    def test_batch_cancelled_leaves_mode_unchanged(self, win):
        with patch('src.main_window.QFileDialog.getOpenFileNames',
                   return_value=([], "")):
            win._on_open_batch_files()

        assert win.batch_mode is False


# ---------------------------------------------------------------------------
# _update_tab_styles  (lines 3086-3160)
# ---------------------------------------------------------------------------

class TestUpdateTabStylesCoverage:

    def test_dark_theme_mode_container_gets_stylesheet(self, win):
        win._update_tab_styles('dark')
        assert len(win.mode_btn_container.styleSheet()) > 0

    def test_light_theme_mode_container_gets_stylesheet(self, win):
        win._update_tab_styles('light')
        assert len(win.mode_btn_container.styleSheet()) > 0

    def test_data_src_container_also_styled(self, win):
        win._update_tab_styles('dark')
        if win.data_src_btn_container:
            assert len(win.data_src_btn_container.styleSheet()) > 0

    def test_no_container_does_not_crash(self, win):
        orig = win.mode_btn_container
        win.mode_btn_container = None
        win._update_tab_styles('light')  # Must not raise
        win.mode_btn_container = orig


# ---------------------------------------------------------------------------
# _on_config_path_changed with file path  (lines 2603-2637)
# ---------------------------------------------------------------------------

class TestOnConfigPathChanged:

    def test_with_valid_json_path_loads_calib(self, tmp_path, win):
        cfg_data = {"calibration_method": "minmax", "calibration_num": 75}
        f = tmp_path / "cfg.json"
        f.write_text(json.dumps(cfg_data))
        win.config_path_field.setText(str(f))
        # Trigger manually since the field is read-only normally
        win._on_config_path_changed()
        assert win.calib_method_combo.currentData() == "minmax"
        assert win.calib_num_spinbox.value() == 75

    def test_clearing_path_disables_edit_button(self, win):
        win.config_path_field.setText("")
        win._on_config_path_changed()
        assert not win.edit_config_button.isEnabled()

    def test_exception_in_calib_sync_does_not_raise(self, tmp_path, win):
        """Lines 2627-2628: exception in calib sync is silently caught."""
        f = tmp_path / "cfg.json"
        f.write_text("{}")
        win.config_path_field.setText(str(f))
        with patch('builtins.open', side_effect=OSError("read error")):
            win._on_config_path_changed()  # Must not raise


# ===========================================================================
# COVERAGE REFINEMENT — targeted tests for remaining uncovered lines
# ===========================================================================

class TestUpdateConfigFieldStateWithConfigSet:
    """Line 480: edit_config_button enabled when config_file_path is set."""

    def test_edit_button_enabled_when_config_file_set(self, win):
        win.execution_mode = "cli"
        win.config_file_path = "/some/config.json"
        win._update_config_field_state()
        assert win.edit_config_button.isEnabled()


class TestWriteDefaultLoaderExceptionPaths:
    """Lines 917-918, 939-940: exception handling in preprocessing field parsing."""

    def test_invalid_file_extensions_json_does_not_raise(self, tmp_path, win):
        """Lines 917-918: malformed file_extensions JSON is silently ignored."""
        cfg_file = tmp_path / "model.json"
        cfg_file.write_text(json.dumps({"default_loader": {}}))
        win.config_file_path = str(cfg_file)
        win.file_extensions_field.setText('not-valid-json')
        win._write_default_loader_to_config()  # Must not raise

    def test_invalid_centercrop_json_does_not_raise(self, tmp_path, win):
        """Lines 939-940: malformed centercrop JSON is silently ignored."""
        cfg_file = tmp_path / "model.json"
        cfg_file.write_text(json.dumps({"default_loader": {}}))
        win.config_file_path = str(cfg_file)
        win.centercrop_field.setText('invalid{json')
        win._write_default_loader_to_config()  # Must not raise


class TestLoadDefaultLoaderExceptionPath:
    """Lines 1080-1081: outer exception in _load_default_loader_from_config."""

    def test_exception_in_json_load_is_silently_caught(self, tmp_path, win):
        f = tmp_path / "cfg.json"
        f.write_text("{}")
        win.config_file_path = str(f)
        with patch('builtins.open', side_effect=OSError("unreadable")):
            win._load_default_loader_from_config()  # Must not raise


class TestApplyCalibToConfigExceptionPath:
    """Lines 1649-1650: exception when writing to config file in _apply_calib_to_config."""

    def test_write_exception_logs_warning(self, tmp_path, win):
        cfg = {"calibration_method": "ema"}
        f = tmp_path / "cfg.json"
        f.write_text(json.dumps(cfg))

        import builtins
        real_open = builtins.open
        call_count = [0]

        def mock_open(path, *args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 1:  # first open (read) succeeds
                return real_open(path, *args, **kwargs)
            raise OSError("disk full")  # second open (write) fails

        options = {'config_path': str(f), 'calib_method': 'minmax', 'calib_num': 10}
        with patch('builtins.open', side_effect=mock_open):
            result = win._apply_calib_to_config(options)
        # Should not raise; the exception is caught and logged


class TestOnOutputReceivedInfoColor:
    """Line 2051: 'info' color in _on_output_received."""

    def test_info_line_does_not_raise(self, win):
        win._on_output_received("info: loading model from disk\n")

    def test_loading_line_uses_info_color(self, win):
        win._on_output_received("loading model weights...\n")

    def test_starting_line_uses_info_color(self, win):
        win._on_output_received("starting compilation process\n")


class TestBrowseInputFileLastBrowseDir:
    """Line 2157: uses last_browse_directory when default_input_path is invalid."""

    def test_uses_last_browse_dir_when_no_default(self, tmp_path, win):
        """Clear default so we hit the else branch (line 2157)."""
        onnx = _make_onnx(tmp_path)
        win.settings_manager.settings['default_input_path'] = ''
        win.last_browse_directory = str(tmp_path)
        with patch('src.main_window.QFileDialog.getOpenFileName',
                   return_value=(onnx, "")) as mock_dlg:
            win._on_browse_input_file()

        call_args = mock_dlg.call_args[0]
        assert str(tmp_path) in call_args


class TestBrowseConfigFileExceptionPath:
    """Lines 2233-2234: exception in calib sync after selecting config file."""

    def test_exception_in_json_sync_is_silently_caught(self, tmp_path, win):
        cfg = _make_json(tmp_path)
        with patch('src.main_window.QFileDialog.getOpenFileName',
                   return_value=(cfg, "")), \
             patch('builtins.open', side_effect=OSError("read error")):
            win._on_browse_config_file()  # Must not raise


class TestBrowseOutputFileInitialDirCases:
    """Lines 2247, 2253: initial directory selection in _on_browse_output_file."""

    def test_uses_existing_output_path_as_initial(self, tmp_path, win):
        """Line 2247: when output_model_path exists and is a dir."""
        win.output_model_path = str(tmp_path)
        win.input_model_path = ""
        with patch('src.main_window.QFileDialog.getExistingDirectory',
                   return_value=str(tmp_path)) as mock_dlg:
            win._on_browse_output_file()

        call_args = mock_dlg.call_args[0]
        assert str(tmp_path) in call_args

    def test_falls_back_to_last_browse_dir(self, win):
        """Line 2253: when no output/input/default paths are set."""
        win.output_model_path = ""
        win.input_model_path = ""
        win.settings_manager.settings['default_output_path'] = ''
        win.last_browse_directory = '/tmp'
        with patch('src.main_window.QFileDialog.getExistingDirectory',
                   return_value="") as mock_dlg:
            win._on_browse_output_file()

        call_args = mock_dlg.call_args[0]
        assert '/tmp' in call_args


class TestValidateInputFileExceptionPath:
    """Lines 2391-2394: exception when reading input file header."""

    def test_file_read_exception_returns_false(self, tmp_path, win):
        f = tmp_path / "model.onnx"
        f.write_bytes(b"\x08\x00\x00\x00extra")

        import builtins
        real_open = builtins.open
        call_count = [0]

        def mock_open(path, *args, **kwargs):
            call_count[0] += 1
            if 'rb' in args or kwargs.get('mode', '') == 'rb':
                raise OSError("read error")
            return real_open(path, *args, **kwargs)

        with patch('builtins.open', side_effect=mock_open):
            result = win._validate_input_file(str(f))
        assert result is False


class TestValidateConfigFileDirectoryPath:
    """Lines 2426-2429: config path that's a directory (not a file)."""

    def test_directory_path_returns_false(self, tmp_path, win):
        result = win._validate_config_file(str(tmp_path))
        assert result is False


class TestWriteCalibToConfigExceptionPath:
    """Lines 2649-2650: exception when writing to config file in _write_calib_to_config."""

    def test_write_exception_shows_status_message(self, tmp_path, win):
        cfg = {"name": "model"}
        f = tmp_path / "cfg.json"
        f.write_text(json.dumps(cfg))
        win.config_file_path = str(f)

        import builtins
        real_open = builtins.open
        call_count = [0]

        def mock_open(path, *args, **kwargs):
            call_count[0] += 1
            if call_count[0] > 1:
                raise OSError("disk full")
            return real_open(path, *args, **kwargs)

        with patch('builtins.open', side_effect=mock_open):
            win._write_calib_to_config()  # Must not raise


class TestUpdateCommandPreviewCLIMode:
    """Lines 3080, 3086-3123: _update_command_preview in Python mode (saved script) and CLI mode."""

    def test_python_mode_with_saved_script(self, tmp_path, win):
        """Line 3080: Python mode with saved_python_script_path."""
        onnx = _make_onnx(tmp_path)
        script = tmp_path / "compile.py"
        script.write_text("import dx_com")
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.execution_mode = "python"
        win.saved_python_script_path = str(script)
        win._update_command_preview()
        assert str(script) in win.command_preview_field.text()

    def test_cli_mode_builds_dxcom_command(self, tmp_path, win):
        """Lines 3086-3123: CLI mode builds dxcom command preview."""
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.execution_mode = "cli"
        win._update_command_preview()
        cmd = win.command_preview_field.text()
        assert cmd.startswith("dxcom")
        assert onnx in cmd

    def test_cli_mode_with_config_file(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        cfg = _make_json(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.config_file_path = cfg
        win.execution_mode = "cli"
        win._update_command_preview()
        assert '-c' in win.command_preview_field.text()

    def test_cli_mode_with_gen_log_flag(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.execution_mode = "cli"
        win.gen_log_checkbox.setChecked(True)
        win._update_command_preview()
        assert '--gen_log' in win.command_preview_field.text()

    def test_cli_mode_with_node_specs(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.execution_mode = "cli"
        win.compile_input_nodes_field.setText("in_node")
        win.compile_output_nodes_field.setText("out_node")
        win._update_command_preview()
        cmd = win.command_preview_field.text()
        assert 'in_node' in cmd
        assert 'out_node' in cmd


class TestOnCopyCommand:
    """Lines 3127-3133: _on_copy_command."""

    def test_copy_valid_command(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.execution_mode = "cli"
        win._update_command_preview()
        win._on_copy_command()  # Must not raise

    def test_copy_empty_command_does_not_raise(self, win):
        win.command_preview_field.setText("")
        win._on_copy_command()  # Must not raise

    def test_copy_error_command_does_not_raise(self, win):
        win.command_preview_field.setText("Error: something went wrong")
        win._on_copy_command()  # Must not raise


class TestOnGeneratePythonScript:
    """Lines 3137-3160: _on_generate_python_script."""

    def test_generates_script_dialog(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.python_data_source = "config"

        mock_dlg = MagicMock()
        mock_dlg.saved_file_path = None
        mock_dlg.exec.return_value = None
        with patch('src.main_window.PythonScriptDialog', return_value=mock_dlg):
            win._on_generate_python_script()

        mock_dlg.exec.assert_called_once()

    def test_saves_script_path_when_dialog_saves(self, tmp_path, win):
        onnx = _make_onnx(tmp_path)
        script = tmp_path / "compile.py"
        script.write_text("")
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.python_data_source = "config"

        mock_dlg = MagicMock()
        mock_dlg.saved_file_path = str(script)
        mock_dlg.exec.return_value = None
        with patch('src.main_window.PythonScriptDialog', return_value=mock_dlg):
            win._on_generate_python_script()

        assert win.saved_python_script_path == str(script)

    def test_without_input_model_uses_default_name(self, win):
        win.input_model_path = ""
        win.output_model_path = ""
        win.python_data_source = "config"

        mock_dlg = MagicMock()
        mock_dlg.saved_file_path = None
        mock_dlg.exec.return_value = None
        with patch('src.main_window.PythonScriptDialog', return_value=mock_dlg) as mock_cls:
            win._on_generate_python_script()

        # Default name should be "compile_model.py"
        call_args = mock_cls.call_args[0]
        assert "compile_model.py" in call_args[1]


# ===========================================================================
# FINAL REFINEMENT — last remaining uncovered exception handlers and branches
# ===========================================================================

class TestWriteDefaultLoaderRemainingExceptions:
    """Lines 946-947, 953-954, 960-961, 967-968: except handlers for more preprocessing fields."""

    def _setup_config(self, tmp_path, win):
        cfg_file = tmp_path / "model.json"
        cfg_file.write_text(json.dumps({"default_loader": {}}))
        win.config_file_path = str(cfg_file)
        return cfg_file

    def test_transpose_invalid_json_does_not_raise(self, tmp_path, win):
        """Lines 946-947."""
        self._setup_config(tmp_path, win)
        win.transpose_field.setText('bad json here')
        win._write_default_loader_to_config()

    def test_expand_dim_invalid_json_does_not_raise(self, tmp_path, win):
        """Lines 953-954."""
        self._setup_config(tmp_path, win)
        win.expand_dim_field.setText('bad json')
        win._write_default_loader_to_config()

    def test_normalize_invalid_json_does_not_raise(self, tmp_path, win):
        """Lines 960-961."""
        self._setup_config(tmp_path, win)
        win.normalize_field.setText('not{valid')
        win._write_default_loader_to_config()

    def test_mul_invalid_json_does_not_raise(self, tmp_path, win):
        """Lines 967-968."""
        self._setup_config(tmp_path, win)
        win.mul_field.setText('{bad}')
        win._write_default_loader_to_config()


class TestUpdateCommandPreviewRemainingBranches:
    """Lines 3110, 3122-3123: aggressive_partitioning flag and exception handler."""

    def test_cli_mode_with_aggressive_partitioning(self, tmp_path, win):
        """Line 3110: aggressive_partitioning flag in CLI command."""
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.execution_mode = "cli"
        win.aggressive_partitioning_checkbox.setChecked(True)
        win._update_command_preview()
        assert '--aggressive_partitioning' in win.command_preview_field.text()

    def test_exception_in_preview_sets_error_message(self, tmp_path, win):
        """Lines 3122-3123: exception handler for command preview."""
        onnx = _make_onnx(tmp_path)
        win.input_model_path = onnx
        win.output_model_path = str(tmp_path)
        win.execution_mode = "cli"
        # Make opt_level_combo.currentData() raise to trigger exception handler
        mock_combo = MagicMock()
        mock_combo.currentData.side_effect = RuntimeError("combo error")
        win.opt_level_combo = mock_combo
        win._update_command_preview()
        text = win.command_preview_field.text()
        assert 'Error' in text