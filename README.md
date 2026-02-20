# DXCom GUI - ONNX to DXNN Model Compiler

A desktop application for compiling ONNX models to DXNN format using the DXCom compiler. Built with PySide6 (Qt for Python), it provides an intuitive interface for deep neural network model conversion.

## Features

- **Two Execution Modes**: Switch between CLI and Python API compilation modes
- **Data Source Selection**: Choose between Config File or PyTorch DataLoader (Python mode)
- **Default Loader Configuration**: Configure a full image preprocessing pipeline (color conversion, resize, center crop, transpose, expand dim, normalize, mul/add/subtract/div)
- **JSON Config Editor**: Built-in editor for viewing and editing compiler config files
- **Python Script Generator**: Generate standalone Python compilation scripts
- **Real-time Output Logs**: Live compilation progress with scrollable output
- **Intelligent Error Handling**: Detailed error messages with actionable fix suggestions
- **Automatic DXCom Detection**: Finds the DXCom compiler from the system PATH
- **Environment Validation**: Pre-flight checks before compilation
- **Theme Support**: Light and dark UI modes
- **Settings Persistence**: Configurable default paths and preferences

## Requirements

### System Requirements
- **Operating System**: Linux (Ubuntu 18.04+)
- **Python**: 3.8 or higher
- **Display**: X11 or Wayland display server

### Dependencies
- **PySide6** ≥ 6.4.0 (Qt for Python)
- **DXCom Compiler**: The ONNX to DXNN compiler (installed separately)

## Installation

### Install from Source

```bash
# Clone the repository
git clone https://github.com/DEEPX-AI/dx_com-gui.git
cd dx_com-gui

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the package (creates the `dxcom-gui` entry point)
pip install .

# Run
dxcom-gui
```

### Run Without Installing

```bash
cd dx_com-gui
pip install PySide6
python main.py
```

## Usage

### Basic Workflow

1. **Launch the application**
   ```bash
   dxcom-gui
   # or: python main.py
   ```

2. **Select execution mode** — click `[ Python ]` or `[ CLI ]` at the top of the window.

3. **Configure inputs**:
   - **Input ONNX Model**: Browse to your `.onnx` file
   - **Output Directory**: Select where the compiled model will be saved

4. **Configure compilation** (optional):
   - **Config File**: Select or edit a JSON compiler config (click **Edit** to open the built-in editor)
   - **Optimization Level**: Set the optimization level
   - **Calibration Method / Calibration Samples** (Python mode)
   - **Quantization Device** (Python mode)
   - **Input Nodes / Output Nodes / Enhanced Scheme** (optional)
   - **Generate log file** / **Aggressive partitioning** checkboxes

5. **Configure preprocessing** (Python mode with DataLoader):
   - Select **PyTorch DataLoader** as the data source
   - Set **Dataset Path** and file extensions
   - Fill in any preprocessing fields: Convert Color, Resize, Center Crop, Transpose, Expand Dim, Normalize, Mul, Add, Subtract, Div

6. **Compile** — click `Compile Model` and monitor the real-time output log.

7. **Generate Script** (optional) — click `Generate Python Script` to produce a standalone `.py` file.

### Command Line Options

```
dxcom-gui [OPTIONS]

  --input FILE        Input ONNX model file path (pre-loads on launch)
  --output FILE       Output file path (pre-fills the output directory)
  --theme THEME       UI theme: light or dark  [default: light]
  --dxcom-path PATH   Custom path to the DXCom compiler executable
  -h, --help          Show this help message and exit
```

**Examples:**
```bash
# Open with a pre-loaded model
dxcom-gui --input model.onnx

# Use dark theme with a custom compiler path
dxcom-gui --theme dark --dxcom-path /opt/dxcom/bin/dxcom
```

## Configuration

### Application Settings

Settings are stored in `~/.dxcom_gui/settings.json`:

```json
{
    "theme": "light",
    "auto_save_preset": false,
    "default_input_path": "",
    "default_output_path": "",
    "default_json_path": "",
    "default_dataset_path": "",
    "max_recent_files": 10,
    "show_tooltips": true,
    "confirm_overwrite": true,
    "auto_scroll_logs": true
}
```

### Default Paths

Open **Settings** from the menu to configure default browse directories:

| Setting | Description |
|---|---|
| Default Input Path | Pre-fills the ONNX model browser |
| Default Output Path | Pre-fills the output directory browser |
| Default JSON Path | Pre-fills the config file browser |
| Default Dataset Path | Pre-fills the dataset directory browser |

### DXCom Compiler Detection

The application finds `dxcom` from the **system PATH**. Make sure `dxcom` is on your PATH before launching.

To override with a specific executable:
```bash
dxcom-gui --dxcom-path /path/to/dxcom
```

## Troubleshooting

**DXCom Compiler Not Found**
- Ensure DXCom is installed and on your system PATH: `which dxcom`
- Or use `--dxcom-path /path/to/dxcom` to specify the executable directly

**Compilation Fails**
- Verify the ONNX model is valid
- Review the output log for specific error messages
- Try a different optimization level or config file

**GUI Doesn't Launch**
- Check PySide6 is installed: `pip list | grep PySide6`
- For X11 issues: `export QT_QPA_PLATFORM=xcb`

**Getting Help**
- `docs/INSTALLATION.md` — full installation and troubleshooting guide
- `docs/USER_GUIDE.md` — detailed usage instructions

## Project Structure

```
dx_com-gui/
├── main.py                      # Alternate entry point
├── requirements.txt             # Runtime dependency (PySide6)
├── pyproject.toml               # Build config; entry point: dxcom-gui
├── setup.py
├── CHANGELOG.md
├── src/
│   ├── __init__.py
│   ├── __main__.py              # Primary entry point (argparse)
│   ├── main_window.py           # Main GUI window
│   ├── dxcom_wrapper.py         # CLI/Python subprocess wrapper
│   ├── dxcom_detector.py        # Compiler detection logic
│   ├── settings_manager.py      # Application settings
│   ├── settings_dialog.py       # Settings UI
│   ├── error_handler.py         # Error parsing
│   ├── error_dialog.py          # Error display UI
│   ├── environment_validator.py # System pre-flight checks
│   ├── json_config_dialog.py    # JSON config editor dialog
│   ├── python_script_dialog.py  # Python script generator dialog
│   ├── themes.py                # Light/dark theme stylesheets
│   └── resources/               # Icons bundled with the package
│       ├── deepx.png
│       ├── deepx_16.png
│       ├── deepx_32.png
│       ├── deepx_64.png
│       └── deepx_128.png
├── tests/
│   ├── requirements.txt              # Development/test dependencies
│   ├── test_settings_manager.py
│   ├── test_dxcom_detector.py
│   ├── test_dxcom_wrapper.py
│   ├── test_error_handler.py
│   ├── test_environment_validator.py
│   ├── test_command_builder.py
│   └── test_sample_models.py
├── docs/
│   ├── INSTALLATION.md
│   └── USER_GUIDE.md
├── resources/
│   ├── deepx.png                # Application icon (16/32/64/128 px variants also included)
│   ├── deepx_16.png
│   ├── deepx_32.png
│   ├── deepx_64.png
│   └── deepx_128.png
```

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage report
python -m pytest --cov=src tests/

# Run a specific test file
python -m pytest tests/test_settings_manager.py -v
```

### Building the Package

```bash
pip install -r tests/requirements.txt
python -m build
```