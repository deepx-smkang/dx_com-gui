# DXCom Wrapper Module

## Overview

The `dxcom_wrapper.py` module provides a non-blocking, thread-safe interface for executing the dxcom compiler as a subprocess. It integrates seamlessly with PySide6/Qt applications and provides real-time progress updates through Qt signals.

## Architecture

### Components

1. **DXComExecutor** (QThread)
   - Executes dxcom in a separate thread
   - Captures stdout/stderr in real-time
   - Emits signals for progress, output, and completion
   - Handles process lifecycle (start, stop, cleanup)

2. **DXComWrapper** (High-level interface)
   - Simple API for starting compilation
   - Manages executor lifecycle
   - Prevents multiple simultaneous compilations

## Usage

### Basic Example

```python
from dxcom_wrapper import DXComWrapper

# Create wrapper
wrapper = DXComWrapper()

# Prepare compilation parameters
executor = wrapper.compile(
    input_path="/path/to/model.onnx",
    output_path="/path/to/output.dxnn",
    compiler_options={
        'config_path': '/path/to/config.json',
        'opt_level': 1,
        'gen_log': True,
        'aggressive_partitioning': False,
        'compile_input_nodes': '',
        'compile_output_nodes': ''
    }
)

# Connect signals (before starting!)
executor.output_received.connect(handle_output)
executor.progress_updated.connect(handle_progress)
executor.compilation_finished.connect(handle_completion)
executor.error_occurred.connect(handle_error)

# Start execution
executor.start()
```

### Integration with MainWindow

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dxcom_wrapper = DXComWrapper()
        self.current_executor = None
        # ... rest of init
    
    def on_compile_clicked(self):
        # Get configuration
        input_path = self.input_model_path
        output_path = self.output_model_path
        compiler_options = self.get_compiler_options()
        
        # Create executor
        self.current_executor = self.dxcom_wrapper.compile(
            input_path=input_path,
            output_path=output_path,
            compiler_options=compiler_options
        )
        
        # Connect to UI
        self.current_executor.output_received.connect(
            self.output_display.append
        )
        self.current_executor.progress_updated.connect(
            self.update_progress_bar
        )
        self.current_executor.compilation_finished.connect(
            self.on_compilation_finished
        )
        self.current_executor.error_occurred.connect(
            self.show_error_message
        )
        
        # Start
        self.current_executor.start()
        
        # Update UI state
        self.compile_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
```

## Signals

### DXComExecutor.output_received(str)
Emitted for each line of stdout/stderr output.

**Parameters:**
- `line` (str): Raw output line including newline

**Use case:** Display compiler output in a text widget

### DXComExecutor.progress_updated(int, str)
Emitted when progress can be estimated from output.

**Parameters:**
- `percentage` (int): Progress percentage 0-100
- `message` (str): User-friendly progress description

**Use case:** Update progress bar and status label

### DXComExecutor.compilation_finished(bool, str)
Emitted when compilation completes (success or failure).

**Parameters:**
- `success` (bool): True if compilation succeeded
- `message` (str): Final status message

**Use case:** Show completion dialog, re-enable compile button

### DXComExecutor.error_occurred(str)
Emitted when an error occurs (e.g., dxcom not found).

**Parameters:**
- `error_message` (str): Error description

**Use case:** Show error dialog, log error

## Methods

### DXComWrapper.compile()
Create a new executor for compilation.

**Returns:** DXComExecutor instance (not started)

**Note:** Must call `.start()` to begin execution

### DXComWrapper.is_running()
Check if compilation is in progress.

**Returns:** bool

### DXComWrapper.stop_current()
Stop current compilation if running.

### DXComExecutor.stop()
Request graceful termination of compilation.

### DXComExecutor.start()
Begin execution in separate thread.

## Command Line Building

The wrapper builds dxcom commands like:

```bash
dxcom input.onnx output.dxnn -c config.json --opt_level 1 --gen_log
```

All compiler options from `get_compiler_options()` are translated to appropriate command-line arguments.

## Error Handling

The wrapper handles several error scenarios:

1. **dxcom not found**: Emits error_occurred signal with helpful message
2. **Process failure**: Captures exit code and emits compilation_finished with success=False
3. **Unexpected exceptions**: Caught and reported via error_occurred signal
4. **User cancellation**: Gracefully terminates process

## Thread Safety

- DXComExecutor runs in a separate QThread
- All GUI updates happen through Qt signals (thread-safe)
- Process termination is handled safely
- No direct GUI calls from worker thread

## Progress Estimation

Progress is estimated using heuristics:

1. **Pattern matching**: Looks for keywords like "loading", "optimizing", "compiling"
2. **Line counting**: Estimates progress based on output volume
3. **Explicit progress**: Future dxcom versions may provide explicit progress info

Current estimates:
- 0-15%: Starting, loading model
- 15-40%: Parsing and initial processing
- 40-70%: Optimization passes
- 70-90%: Code generation
- 90-100%: Writing output, finalizing

## Testing

Use the provided test script:

```bash
python test_dxcom_wrapper.py
```

Modify the paths in the script to point to real ONNX models for actual testing.

## Dependencies

- PySide6 (Qt6 for Python)
- subprocess (Python standard library)
- typing (Python standard library)

No external packages beyond PySide6 required.
