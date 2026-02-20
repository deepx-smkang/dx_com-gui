"""
DXCom subprocess wrapper with Qt threading support.

This module provides a non-blocking interface for executing the dxcom compiler
as a subprocess. It uses QThread for async execution and emits signals for
real-time progress updates, output capture, and completion/error handling.
"""
import subprocess
import os
import time
import re
from typing import Dict, Optional, List
from PySide6.QtCore import QThread, Signal, QObject
from .error_handler import DXComErrorParser, DXComError, format_error_for_display


def strip_ansi_codes(text: str) -> str:
    """
    Remove ANSI escape codes from text.
    
    Args:
        text: Text potentially containing ANSI codes
        
    Returns:
        Text with ANSI codes removed
    """
    # Pattern matches ANSI escape sequences including cursor movement, colors, etc.
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


class DXComExecutor(QThread):
    """
    Thread for executing dxcom compiler as a subprocess.
    
    This class runs the dxcom compiler in a separate thread to avoid blocking
    the GUI. It captures stdout/stderr in real-time and emits signals for
    progress updates, output, and completion.
    
    Signals:
        output_received (str): Emitted when stdout/stderr output is received
        progress_updated (int, str): Emitted with progress percentage and message
        compilation_finished (bool, str): Emitted on completion with (success, message)
        error_occurred (str): Emitted when an error occurs (simple message)
        error_details (DXComError): Emitted with detailed error information
    """
    
    # Qt Signals
    output_received = Signal(str)  # Raw output line
    progress_updated = Signal(int, str)  # (percentage, message)
    compilation_finished = Signal(bool, str)  # (success, final_message)
    error_occurred = Signal(str)  # Error message (simple string for backward compat)
    error_details = Signal(object)  # DXComError object with detailed information
    
    def __init__(self, 
                 input_path: str,
                 output_path: str,
                 compiler_options: Dict,
                 timeout: Optional[int] = None,
                 python_script_path: Optional[str] = None,
                 parent: Optional[QObject] = None):
        """
        Initialize the DXCom executor.
        
        Args:
            input_path: Path to input ONNX model file
            output_path: Path for output DXNN model file
            compiler_options: Dictionary of compiler options:
                - config_path: Path to config JSON file
                - opt_level: Optimization level (0 or 1)
                - gen_log: Generate log file (bool)
                - aggressive_partitioning: Enable aggressive partitioning (bool)
                - compile_input_nodes: Comma-separated input node names (str)
                - compile_output_nodes: Comma-separated output node names (str)
            timeout: Maximum execution time in seconds (None for no timeout)
            python_script_path: If provided, execute this Python script instead of dxcom CLI
            parent: Parent QObject (optional)
        """
        super().__init__(parent)
        
        self.input_path = input_path
        self.output_path = output_path
        self.compiler_options = compiler_options
        self.timeout = timeout
        self.python_script_path = python_script_path  # NEW: for Python mode
        
        self._process: Optional[subprocess.Popen] = None
        self._should_stop = False
        self._start_time: Optional[float] = None
        self._output_buffer: List[str] = []  # Store all output for error parsing
        
    def run(self):
        """
        Execute the dxcom compiler subprocess.
        
        This method runs in a separate thread. It builds the command,
        starts the subprocess, captures output in real-time, and emits
        signals for GUI updates.
        """
        try:
            # Build command line arguments
            if self.python_script_path:
                # Python mode: execute the Python script
                import sys
                cmd = [sys.executable, self.python_script_path]
            else:
                # CLI mode: execute dxcom command
                cmd = self._build_command()
            
            # Emit initial progress
            self.progress_updated.emit(0, "Starting compilation...")
            self.output_received.emit(f"Executing: {' '.join(cmd)}\n")
            
            # Start subprocess with output capture
            self._start_time = time.time()
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merge stderr into stdout
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            # Read output line by line with timeout checking
            line_count = 0
            for line in self._process.stdout:
                # Check timeout
                if self.timeout and (time.time() - self._start_time) > self.timeout:
                    self._terminate_process()
                    self._handle_timeout()
                    return
                
                # Check cancellation
                if self._should_stop:
                    self._terminate_process()
                    self.compilation_finished.emit(False, "Compilation cancelled by user")
                    return
                
                # Strip ANSI escape codes from output
                clean_line = strip_ansi_codes(line)
                
                # Store cleaned output for error parsing
                self._output_buffer.append(clean_line)
                
                # Emit cleaned output
                self.output_received.emit(clean_line)
                
                # Update progress based on output patterns
                line_count += 1
                progress = self._estimate_progress(clean_line, line_count)
                if progress is not None:
                    self.progress_updated.emit(progress, self._extract_progress_message(clean_line))
            
            # Wait for process to complete
            return_code = self._process.wait()
            
            # Check result
            if return_code == 0:
                self.progress_updated.emit(100, "Compilation completed successfully")
                self.compilation_finished.emit(True, "Compilation completed successfully")
            else:
                self._handle_process_failure(return_code)
                
        except FileNotFoundError as e:
            self._handle_exception(e, "dxcom command not found")
            
        except Exception as e:
            self._handle_exception(e, "Unexpected error during compilation")
            
        finally:
            self._process = None
    
    def _handle_timeout(self):
        """Handle compilation timeout."""
        output = ''.join(self._output_buffer)
        error = DXComErrorParser.parse_error(
            exit_code=None,
            output=output,
            exception=TimeoutError(f"Compilation timed out after {self.timeout} seconds")
        )
        
        error_msg = error.user_message
        self.error_occurred.emit(error_msg)
        self.error_details.emit(error)
        self.output_received.emit(f"\n{format_error_for_display(error)}\n")
        self.compilation_finished.emit(False, error_msg)
    
    def _handle_process_failure(self, exit_code: int):
        """Handle non-zero exit code from dxcom process."""
        output = ''.join(self._output_buffer)
        error = DXComErrorParser.parse_error(
            exit_code=exit_code,
            output=output,
            exception=None
        )
        
        error_msg = error.user_message
        self.error_occurred.emit(error_msg)
        self.error_details.emit(error)
        self.output_received.emit(f"\n{format_error_for_display(error)}\n")
        self.compilation_finished.emit(False, error_msg)
    
    def _handle_exception(self, exception: Exception, context: str):
        """Handle Python exceptions during execution."""
        output = ''.join(self._output_buffer)
        error = DXComErrorParser.parse_error(
            exit_code=None,
            output=output,
            exception=exception
        )
        
        error_msg = error.user_message
        self.error_occurred.emit(error_msg)
        self.error_details.emit(error)
        self.output_received.emit(f"\n{format_error_for_display(error)}\n")
        self.compilation_finished.emit(False, error_msg)
    
    def _build_command(self) -> List[str]:
        """
        Build the dxcom command line arguments.
        
        Format: dxcom -m input.onnx -o output_dir -c config.json [options]
        
        Returns:
            List of command arguments
        """
        cmd = ['dxcom']
        
        # Required: Model path (-m)
        cmd.extend(['-m', self.input_path])
        
        # Required: Output directory (-o)
        # dxcom expects output directory, not output file
        output_dir = os.path.dirname(self.output_path)
        if not output_dir:
            output_dir = '.'
        cmd.extend(['-o', output_dir])
        
        # Configuration file
        if self.compiler_options.get('config_path'):
            cmd.extend(['-c', self.compiler_options['config_path']])
        
        # Optimization level
        opt_level = self.compiler_options.get('opt_level', 0)
        cmd.extend(['--opt_level', str(opt_level)])
        
        # Boolean flags
        if self.compiler_options.get('gen_log', False):
            cmd.append('--gen_log')
        
        if self.compiler_options.get('aggressive_partitioning', False):
            cmd.append('--aggressive_partitioning')
        
        # Optional node specifications
        if self.compiler_options.get('compile_input_nodes'):
            cmd.extend(['--compile_input_nodes', self.compiler_options['compile_input_nodes']])
        
        if self.compiler_options.get('compile_output_nodes'):
            cmd.extend(['--compile_output_nodes', self.compiler_options['compile_output_nodes']])
        
        # Calibration options
        if self.compiler_options.get('calib_method'):
            cmd.extend(['--calib_method', self.compiler_options['calib_method']])
        
        if self.compiler_options.get('calib_num') is not None:
            cmd.extend(['--calib_num', str(self.compiler_options['calib_num'])])
        
        return cmd
    
    def _estimate_progress(self, line: str, line_count: int) -> Optional[int]:
        """
        Estimate compilation progress based on output.
        
        This is a heuristic estimator. It looks for known progress indicators
        in the dxcom output or estimates based on line count.
        
        Args:
            line: Current output line
            line_count: Number of lines processed so far
            
        Returns:
            Progress percentage (0-100) or None if not determinable
        """
        line_lower = line.lower()
        
        # Look for explicit progress indicators
        if 'loading' in line_lower or 'parsing' in line_lower:
            return 10
        elif 'optimizing' in line_lower or 'optimization' in line_lower:
            return 40
        elif 'compiling' in line_lower:
            return 60
        elif 'writing' in line_lower or 'saving' in line_lower:
            return 90
        elif 'complete' in line_lower or 'success' in line_lower:
            return 100
        
        # Fallback: estimate based on line count (rough approximation)
        # Assume typical compilation produces 20-100 lines
        if line_count <= 5:
            return 15
        elif line_count <= 10:
            return 30
        elif line_count <= 20:
            return 50
        elif line_count <= 40:
            return 70
        else:
            return 85
    
    def _extract_progress_message(self, line: str) -> str:
        """
        Extract a user-friendly progress message from output line.
        
        Args:
            line: Output line
            
        Returns:
            Progress message string
        """
        # Clean up the line
        line = line.strip()
        
        # Truncate long lines
        if len(line) > 100:
            line = line[:97] + "..."
        
        return line if line else "Processing..."
    
    def stop(self):
        """
        Request the compilation to stop.
        
        This sets a flag that will cause the thread to terminate the
        subprocess on the next output line read.
        """
        self._should_stop = True
        
    def _terminate_process(self):
        """Terminate the subprocess if it's running."""
        if self._process and self._process.poll() is None:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()


class DXComWrapper:
    """
    High-level wrapper for DXCom compilation.
    
    This class provides a simple interface for GUI components to start
    compilation without directly managing threads.
    
    Example:
        wrapper = DXComWrapper()
        executor = wrapper.compile(
            input_path="/path/to/model.onnx",
            output_path="/path/to/output.dxnn",
            compiler_options={...}
        )
        # Connect signals
        executor.output_received.connect(lambda line: print(line))
        executor.compilation_finished.connect(lambda success, msg: print(msg))
        # Start execution
        executor.start()
    """
    
    def __init__(self):
        """Initialize the DXCom wrapper."""
        self._current_executor: Optional[DXComExecutor] = None
        self.default_timeout: Optional[int] = 300  # 5 minutes default timeout
    
    def compile(self,
                input_path: str,
                output_path: str,
                compiler_options: Dict,
                timeout: Optional[int] = None) -> DXComExecutor:
        """
        Create and return a DXComExecutor for compilation.
        
        Args:
            input_path: Path to input ONNX model
            output_path: Path for output DXNN model
            compiler_options: Dictionary of compiler options
            timeout: Maximum execution time in seconds (None for default, 0 for no timeout)
            
        Returns:
            DXComExecutor instance (not started yet)
            
        Note:
            Caller must call .start() on the returned executor to begin
            compilation. This allows connecting signals before execution.
        """
        # Stop any previous compilation
        if self._current_executor and self._current_executor.isRunning():
            self._current_executor.stop()
            self._current_executor.wait()
        
        # Determine timeout value
        if timeout is None:
            timeout = self.default_timeout
        elif timeout == 0:
            timeout = None  # No timeout
        
        # Create new executor
        self._current_executor = DXComExecutor(
            input_path=input_path,
            output_path=output_path,
            compiler_options=compiler_options,
            timeout=timeout
        )
        
        return self._current_executor
    
    def compile_with_python(self,
                           script_path: str,
                           input_path: str,
                           output_path: str,
                           timeout: Optional[int] = None) -> DXComExecutor:
        """
        Create and return a DXComExecutor for Python script-based compilation.
        
        Args:
            script_path: Path to the temporary Python script
            input_path: Path to input ONNX model (for display purposes)
            output_path: Path for output DXNN model (for display purposes)
            timeout: Maximum execution time in seconds (None for default, 0 for no timeout)
            
        Returns:
            DXComExecutor instance (not started yet)
            
        Note:
            Caller must call .start() on the returned executor to begin
            compilation. This allows connecting signals before execution.
        """
        # Stop any previous compilation
        if self._current_executor and self._current_executor.isRunning():
            self._current_executor.stop()
            self._current_executor.wait()
        
        # Determine timeout value
        if timeout is None:
            timeout = self.default_timeout
        elif timeout == 0:
            timeout = None  # No timeout
        
        # Create executor with Python script path
        self._current_executor = DXComExecutor(
            input_path=input_path,
            output_path=output_path,
            compiler_options={},  # Not used in Python mode
            timeout=timeout,
            python_script_path=script_path  # Pass the script path
        )
        
        return self._current_executor
    
    def is_running(self) -> bool:
        """
        Check if compilation is currently running.
        
        Returns:
            True if compilation is in progress
        """
        return (self._current_executor is not None and 
                self._current_executor.isRunning())
    
    def stop_current(self):
        """Stop the current compilation if one is running."""
        if self._current_executor:
            self._current_executor.stop()
    
    def wait_for_completion(self, timeout_ms: int = -1) -> bool:
        """
        Wait for current compilation to complete.
        
        Args:
            timeout_ms: Timeout in milliseconds (-1 for infinite)
            
        Returns:
            True if compilation finished within timeout
        """
        if self._current_executor:
            return self._current_executor.wait(timeout_ms)
        return True
