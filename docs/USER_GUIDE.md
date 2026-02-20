# User Guide

## Launching the Application

```bash
# If installed via pip
dxcom-gui

# With a specific model pre-loaded
dxcom-gui --input /path/to/model.onnx

# With a custom compiler path
dxcom-gui --dxcom-path /path/to/dxcom

# Override theme on launch
dxcom-gui --theme dark

# Without installing
python main.py
```

---

## Main Window Layout

The window has two fixed sections at the top and a scrollable configuration area below.

### Fixed Header
- **Execution Mode**: `[ Python ]  [ CLI ]` — selects whether to invoke dxcom via its Python API or CLI
- **Data Source** *(Python mode only)*: `[ Config File ]  [ PyTorch DataLoader ]` — selects how calibration data is provided

### Scrollable Configuration

Three group boxes stacked vertically:

**1. Input / Output Configuration**
- Input ONNX Model (Browse button)
- Output Directory (Browse button)

**2. Compiler Configuration**
- Config File — path to JSON config (Browse + Edit buttons; Edit opens the built-in JSON editor)
- Optimization Level
- Calibration Method *(Python mode)*
- Calibration Samples *(Python mode)*
- Quantization Device *(Python mode)*
- Generate log file *(checkbox)*
- Aggressive partitioning *(checkbox)*
- *Optional:* Input Nodes, Output Nodes, Enhanced Scheme *(Python mode)*

**3. Default Loader Configuration** *(Python + DataLoader mode)*
- Dataset Path (Browse button)
- File Extensions
- *Preprocessing:* Convert Color, Resize, Center Crop, Transpose, Expand Dim, Normalize, Mul, Add, Subtract, Div

### Bottom Area
- **Compile Model** / **Cancel** buttons
- **Generate Python Script** button — produces a standalone `.py` compilation script
- Status bar
- Output log (scrollable, real-time)

---

## Basic Workflow

### CLI Mode

1. Select **CLI** mode.
2. Set **Input ONNX Model** and **Output Directory**.
3. Optionally select a **Config File**.
4. Click **Compile Model**.

### Python Mode (Config File)

1. Select **Python** mode and **Config File** data source.
2. Set **Input ONNX Model** and **Output Directory**.
3. Set **Config File**, **Optimization Level**, **Calibration Method/Samples**, **Quantization Device** as needed.
4. Click **Compile Model**.

### Python Mode (PyTorch DataLoader)

1. Select **Python** mode and **PyTorch DataLoader** data source.
2. Set **Input ONNX Model** and **Output Directory**.
3. Set **Dataset Path**, **File Extensions**, and any preprocessing fields.
4. Click **Compile Model**.

---

## JSON Config Editor

Click **Edit** next to the Config File field to open the built-in editor. The editor lets you view and modify the JSON config directly before compilation.

---

## Python Script Generator

Click **Generate Python Script** to produce a standalone `.py` file that replicates the current configuration. The generated script can be run independently without the GUI.

---

## Settings

Open via **Edit → Settings** or `Ctrl+,`.

| Setting | Description | Default |
|---|---|---|
| `theme` | `light` or `dark` | `light` |
| `default_input_path` | Default directory for ONNX model browser | `""` |
| `default_output_path` | Default directory for output browser | `""` |
| `default_json_path` | Default directory for config file browser | `""` |
| `default_dataset_path` | Default directory for dataset browser | `""` |
| `max_recent_files` | Number of recent files to remember | `10` |
| `show_tooltips` | Show field tooltips | `true` |
| `confirm_overwrite` | Confirm before overwriting output | `true` |
| `auto_scroll_logs` | Auto-scroll the output log | `true` |

Settings are saved to `~/.dxcom_gui/settings.json`.

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+O` | Open ONNX file |
| `Ctrl+J` | Open JSON config |
| `Ctrl+R` | Run compilation |
| `Ctrl+T` | Toggle light/dark theme |
| `Ctrl+,` | Open settings |
| `Ctrl+Q` | Quit |
| `F1` | Show keyboard shortcuts |

---

## Troubleshooting

**DXCom not found**
- Ensure `dxcom` is on your system PATH: `which dxcom`
- Or launch with: `dxcom-gui --dxcom-path /path/to/dxcom`
- **Desktop launcher only**: `~/.bashrc` is not sourced by desktop apps. Add your
  PATH entry to `~/.profile` instead so the desktop launcher picks it up:
  ```bash
  echo 'export PATH="/path/to/dxcom/bin:$PATH"' >> ~/.profile
  # Then log out and back in
  ```

**Compilation fails**
- Check the output log for the specific error message
- Verify the ONNX model is valid
- Try adjusting the optimization level or config file

**GUI doesn't launch**
- Check PySide6 is installed: `pip list | grep PySide6`
- For X11 issues: `export QT_QPA_PLATFORM=xcb`
