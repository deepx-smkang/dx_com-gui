# API Reference - DXCom GUI

Technical reference for developers working with DXCom GUI codebase.

## Table of Contents

1. [Module Overview](#module-overview)
2. [Core Classes](#core-classes)
3. [Error Handling](#error-handling)
4. [Settings Management](#settings-management)
5. [Compiler Integration](#compiler-integration)
6. [UI Components](#ui-components)

## Module Overview

### Package Structure

```
src/
├── __init__.py              # Package initialization
├── main_window.py           # Main application window
├── dxcom_wrapper.py         # DXCom subprocess wrapper
├── dxcom_detector.py        # Compiler detection logic
├── environment_validator.py # System requirements validation
├── error_handler.py         # Error parsing and handling
├── error_dialog.py          # Error display UI
├── settings_manager.py      # Application settings
├── settings_dialog.py       # Settings UI
└── themes.py               # Theme definitions
```

## Core Classes

### MainWindow

Main application window class.

**Module:** `src.main_window`

**Class:** `MainWindow(QMainWindow)`

#### Constructor

```python
def __init__(self, parent: Optional[QWidget] = None)
```

Initializes the main application window.

**Parameters:**
- `parent`: Optional parent widget

**Example:**
```python
from src.main_window import MainWindow
window = MainWindow()
window.show()
```

#### Public Methods

##### set_input_path

```python
def set_input_path(self, path: str) -> None
```

Set the input ONNX model file path.

**Parameters:**
- `path`: Path to ONNX model file

**Example:**
```python
window.set_input_path("/path/to/model.onnx")
```

##### set_output_path

```python
def set_output_path(self, path: str) -> None
```

Set the output DXNN file path.

**Parameters:**
- `path`: Path for output DXNN file

##### start_compilation

```python
def start_compilation(self) -> bool
```

Start the compilation process.

**Returns:**
- `bool`: True if started successfully, False otherwise

**Raises:**
- `ValueError`: If input/output paths are invalid
- `FileNotFoundError`: If input file doesn't exist

##### apply_theme

```python
def apply_theme(self, theme_name: str) -> None
```

Apply a UI theme.

**Parameters:**
- `theme_name`: Theme name ("light", "dark", or "system")

#### Signals

```python
compilation_started = Signal()
compilation_finished = Signal(bool, str)  # success, message
error_occurred = Signal(str)
```

### DXComExecutor

Thread for executing DXCom compiler.

**Module:** `src.dxcom_wrapper`

**Class:** `DXComExecutor(QThread)`

#### Constructor

```python
def __init__(
    self,
    input_path: str,
    output_path: str,
    compiler_options: Dict[str, Any],
    timeout: Optional[int] = None,
    parent: Optional[QObject] = None
)
```

Initialize the DXCom executor thread.

**Parameters:**
- `input_path`: Path to input ONNX model
- `output_path`: Path for output DXNN file
- `compiler_options`: Compiler configuration options
- `timeout`: Optional timeout in seconds
- `parent`: Optional parent QObject

**Example:**
```python
executor = DXComExecutor(
    input_path="model.onnx",
    output_path="model.dxnn",
    compiler_options={
        'optimization_level': '3',
        'target_device': 'NPU',
        'precision': 'float16'
    }
)
executor.start()
```

#### Signals

```python
output_received = Signal(str)             # Output line
progress_updated = Signal(int, str)       # percentage, message
compilation_finished = Signal(bool, str)  # success, message
error_occurred = Signal(str)              # Error message
error_details = Signal(object)            # DXComError object
```

#### Public Methods

##### run

```python
def run(self) -> None
```

Execute the compilation in thread. Called automatically when `start()` is invoked.

##### terminate_compilation

```python
def terminate_compilation(self) -> None
```

Safely terminate the running compilation.

### DXComDetector

Detects DXCom compiler installation.

**Module:** `src.dxcom_detector`

**Class:** `DXComDetector`

#### Constructor

```python
def __init__(self)
```

Initialize the DXCom detector.

#### Public Methods

##### detect_dxcom

```python
def detect_dxcom(self) -> Dict[str, Any]
```

Detect DXCom compiler installation.

**Returns:**
- Dictionary with detection results:
  ```python
  {
      'found': bool,
      'paths': List[str],
      'version': Optional[str],
      'capabilities': List[str]
  }
  ```

**Example:**
```python
from src.dxcom_detector import DXComDetector

detector = DXComDetector()
result = detector.detect_dxcom()

if result['found']:
    print(f"Found DXCom at: {result['paths'][0]}")
    print(f"Version: {result['version']}")
else:
    print("DXCom not found")
```

##### validate_dxcom_path

```python
def validate_dxcom_path(self, path: str) -> bool
```

Validate a specific DXCom path.

**Parameters:**
- `path`: Path to DXCom executable

**Returns:**
- `bool`: True if path is valid DXCom compiler

## Error Handling

### DXComError

Error information class.

**Module:** `src.error_handler`

**Class:** `DXComError`

#### Attributes

```python
error_type: str          # Error category
message: str             # Error message
exit_code: int          # Process exit code
line_number: Optional[int]  # Error line number
context: Optional[str]   # Additional context
suggestions: List[str]   # Fix suggestions
details: Dict[str, Any]  # Additional details
```

#### Constructor

```python
def __init__(
    self,
    error_type: str,
    message: str,
    exit_code: int = 1,
    line_number: Optional[int] = None,
    context: Optional[str] = None,
    suggestions: Optional[List[str]] = None,
    details: Optional[Dict[str, Any]] = None
)
```

**Example:**
```python
error = DXComError(
    error_type="CompilationError",
    message="Unsupported operation: Conv3D",
    line_number=42,
    suggestions=[
        "Check model compatibility",
        "Use ONNX optimizer"
    ]
)
```

### DXComErrorParser

Parses DXCom error output.

**Module:** `src.error_handler`

**Class:** `DXComErrorParser`

#### Public Methods

##### parse_error_output

```python
def parse_error_output(
    self,
    error_output: str,
    exit_code: int
) -> DXComError
```

Parse error output from DXCom.

**Parameters:**
- `error_output`: Error text from stderr
- `exit_code`: Process exit code

**Returns:**
- `DXComError`: Parsed error information

##### suggest_fix

```python
def suggest_fix(self, error: DXComError) -> List[str]
```

Generate fix suggestions for an error.

**Parameters:**
- `error`: DXComError object

**Returns:**
- List of fix suggestions

**Example:**
```python
parser = DXComErrorParser()
error = parser.parse_error_output(stderr_text, exit_code)
suggestions = parser.suggest_fix(error)

for suggestion in suggestions:
    print(f"• {suggestion}")
```

### format_error_for_display

Utility function for formatting errors.

```python
def format_error_for_display(error: DXComError) -> str
```

**Parameters:**
- `error`: DXComError object

**Returns:**
- Formatted error string for display

**Example:**
```python
from src.error_handler import format_error_for_display

formatted = format_error_for_display(error)
print(formatted)
```

## Settings Management

### SettingsManager

Manages application settings and preferences.

**Module:** `src.settings_manager`

**Class:** `SettingsManager`

#### Constructor

```python
def __init__(self)
```

Initialize settings manager. Automatically loads existing settings.

#### Public Methods

##### get

```python
def get(self, key: str, default: Any = None) -> Any
```

Get a setting value.

**Parameters:**
- `key`: Setting key
- `default`: Default value if key not found

**Returns:**
- Setting value or default

**Example:**
```python
from src.settings_manager import SettingsManager

settings = SettingsManager()
theme = settings.get('theme', 'light')
max_recent = settings.get('max_recent_files', 10)
```

##### set

```python
def set(self, key: str, value: Any) -> None
```

Set a setting value.

**Parameters:**
- `key`: Setting key
- `value`: Setting value

##### save_settings

```python
def save_settings(self) -> bool
```

Save settings to disk.

**Returns:**
- `bool`: True if saved successfully

##### add_recent_file

```python
def add_recent_file(self, file_path: str) -> None
```

Add file to recent files list.

**Parameters:**
- `file_path`: Path to file

##### get_recent_files

```python
def get_recent_files(self) -> List[str]
```

Get list of recent files.

**Returns:**
- List of file paths, most recent first

##### clear_recent_files

```python
def clear_recent_files(self) -> None
```

Clear recent files history.

## Compiler Integration

### Command Building

```python
def build_dxcom_command(
    dxcom_path: str,
    input_path: str,
    output_path: str,
    options: Dict[str, Any]
) -> List[str]
```

Build DXCom command line.

**Module:** `src.dxcom_wrapper`

**Parameters:**
- `dxcom_path`: Path to DXCom executable
- `input_path`: Input ONNX file
- `output_path`: Output DXNN file
- `options`: Compiler options

**Returns:**
- Command as list of arguments

**Example:**
```python
command = build_dxcom_command(
    dxcom_path="/usr/bin/dxcom",
    input_path="model.onnx",
    output_path="model.dxnn",
    options={
        'optimization_level': '3',
        'target_device': 'NPU',
        'precision': 'float16',
        'batch_size': '1'
    }
)
# Result: ['/usr/bin/dxcom', '-i', 'model.onnx', '-o', 'model.dxnn', '-O', '3', ...]
```

## UI Components

### Theme System

**Module:** `src.themes`

#### Functions

##### get_theme

```python
def get_theme(theme_name: str) -> str
```

Get theme stylesheet.

**Parameters:**
- `theme_name`: Theme name ("light" or "dark")

**Returns:**
- Qt stylesheet string

##### apply_theme_to_app

```python
def apply_theme_to_app(app: QApplication, theme_name: str) -> None
```

Apply theme to entire application.

**Parameters:**
- `app`: QApplication instance
- `theme_name`: Theme name

**Example:**
```python
from src.themes import apply_theme_to_app

app = QApplication([])
apply_theme_to_app(app, "dark")
```

### Custom Widgets

#### CompilerOptionsWidget

Widget for compiler options configuration.

**Module:** `src.main_window`

**Class:** `CompilerOptionsWidget(QWidget)`

**Properties:**
- `options`: Dict of current option values

**Methods:**
- `get_options()`: Get all option values
- `set_options(options: Dict)`: Set option values
- `reset_to_defaults()`: Reset to default values

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_settings_manager.py

# Run with coverage
python -m pytest --cov=src tests/
```

### Test Utilities

**Module:** `tests.helpers`

```python
def create_mock_onnx_model(path: Path) -> None
    """Create mock ONNX model for testing."""

def create_test_settings() -> SettingsManager:
    """Create settings manager for testing."""
```

## Examples

### Basic Usage

```python
from PySide6.QtWidgets import QApplication
from src.main_window import MainWindow

# Create application
app = QApplication([])

# Create main window
window = MainWindow()

# Configure compilation
window.set_input_path("model.onnx")
window.set_output_path("model.dxnn")

# Show window
window.show()

# Run application
app.exec()
```

### Programmatic Compilation

```python
from src.dxcom_wrapper import DXComExecutor
from PySide6.QtCore import QCoreApplication

app = QCoreApplication([])

# Create executor
executor = DXComExecutor(
    input_path="model.onnx",
    output_path="model.dxnn",
    compiler_options={
        'optimization_level': '3',
        'target_device': 'NPU'
    }
)

# Connect signals
executor.progress_updated.connect(
    lambda p, m: print(f"Progress: {p}% - {m}")
)
executor.compilation_finished.connect(
    lambda s, m: print(f"{'Success' if s else 'Failed'}: {m}")
)

# Start compilation
executor.start()

app.exec()
```

### Custom Error Handling

```python
from src.error_handler import DXComErrorParser

parser = DXComErrorParser()

# Parse error
error = parser.parse_error_output(stderr_output, exit_code)

# Get suggestions
suggestions = parser.suggest_fix(error)

# Display
print(f"Error: {error.message}")
print("Suggestions:")
for suggestion in suggestions:
    print(f"  • {suggestion}")
```

---

For more examples, see the `examples/` directory in the repository.
