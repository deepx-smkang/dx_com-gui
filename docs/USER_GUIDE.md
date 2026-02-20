# User Guide - DXCom GUI

Comprehensive guide for using the DXCom GUI application to compile ONNX models to DXNN format.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Main Window Overview](#main-window-overview)
3. [Basic Usage](#basic-usage)
4. [Advanced Features](#advanced-features)
5. [Settings & Configuration](#settings--configuration)
6. [Troubleshooting](#troubleshooting)
7. [Tips & Best Practices](#tips--best-practices)

## Getting Started

### First Launch

When you first launch DXCom GUI:

1. The application will automatically detect your DXCom compiler installation
2. If not found, you'll be prompted to specify the location
3. Environment validation will check system requirements
4. Default settings will be initialized

### Quick Start Tutorial

**Compile your first model in 3 steps:**

1. **Select Input Model**
   - Click "Browse" button next to "Input ONNX Model"
   - Navigate to your `.onnx` file
   - Example: `resnet50.onnx`

2. **Set Output Path** (optional)
   - Specify where to save the `.dxnn` file
   - Or leave blank to auto-generate from input name
   - Example: `resnet50.dxnn`

3. **Click Compile**
   - Press the "Compile Model" button
   - Monitor progress in the output log
   - Wait for completion message

## Main Window Overview

### Layout

```
┌─────────────────────────────────────────────────────┐
│  DXCom GUI                                [_][□][X] │
├─────────────────────────────────────────────────────┤
│  File  Edit  View  Tools  Help                      │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Input ONNX Model:  [________________] [Browse]     │
│  Output DXNN File:  [________________] [Browse]     │
│                                                      │
│  ┌─ Compiler Options ────────────────────────────┐ │
│  │  Optimization Level: [▼ 3 - Maximum        ] │ │
│  │  Target Device:      [▼ NPU               ] │ │
│  │  Precision:          [▼ float16           ] │ │
│  │  Batch Size:         [▼ 1                 ] │ │
│  │                                              │ │
│  │  [Load Preset ▼]  [Save Preset]            │ │
│  └──────────────────────────────────────────────┘ │
│                                                      │
│  [Compile Model]                                     │
│                                                      │
│  ┌─ Output Log ───────────────────────────────┐    │
│  │  Initializing compilation...                │    │
│  │  Processing model layers...                 │    │
│  │  Progress: ████████░░░░░░░░░░ 50%          │    │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  Recent Files: model1.onnx | model2.onnx | ...      │
└─────────────────────────────────────────────────────┘
```

### UI Components

**File Selection Section**
- Input path field with browse button
- Output path field with browse button
- Drag-and-drop support for input files

**Compiler Options Panel**
- Optimization level dropdown (0-3)
- Target device selector (NPU, GPU, CPU)
- Precision mode (float32, float16, int8, mixed)
- Batch size configuration
- Advanced options (expand/collapse)

**Action Buttons**
- Compile Model: Start compilation
- Cancel: Stop ongoing compilation
- Load/Save Preset: Manage configurations

**Output Log**
- Real-time compilation output
- Progress bar with percentage
- Color-coded messages (info, warning, error)
- Auto-scroll option

**Status Bar**
- Current operation status
- DXCom compiler version
- Quick settings access

## Basic Usage

### Selecting Input Files

**Method 1: Browse Button**
```
1. Click "Browse" next to Input field
2. Navigate to your ONNX model
3. Select file and click "Open"
```

**Method 2: Drag and Drop**
```
1. Open file manager
2. Drag .onnx file onto application window
3. File path auto-populated
```

**Method 3: Recent Files**
```
1. Click recent file name in status bar
2. File automatically loaded
```

**Method 4: Command Line**
```bash
python main.py --input /path/to/model.onnx
```

### Setting Output Path

**Auto-generation** (recommended):
- Leave output field empty
- Path generated as: `{input_name}.dxnn`
- Saves to same directory as input

**Manual specification**:
- Click "Browse" next to Output field
- Choose directory and filename
- Must have `.dxnn` extension

**Output path patterns**:
```
Input:  /home/user/models/resnet50.onnx
Output: /home/user/models/resnet50.dxnn  (auto)

Input:  model.onnx
Output: ./compiled/model_optimized.dxnn  (manual)
```

### Compiler Options

#### Optimization Level
- **0 - None**: No optimization, fastest compilation
- **1 - Basic**: Basic optimizations, balanced
- **2 - Standard**: Standard optimizations (default)
- **3 - Maximum**: Aggressive optimization, slower compilation

**Recommendation**: Start with level 2, use level 3 for production.

#### Target Device
- **NPU**: Neural Processing Unit (specialized hardware)
- **GPU**: Graphics Processing Unit
- **CPU**: Central Processing Unit (fallback)
- **Auto**: Automatic device selection

**Recommendation**: Use NPU if available, otherwise GPU.

#### Precision Mode
- **float32**: Full precision (highest accuracy, largest size)
- **float16**: Half precision (balanced, recommended)
- **int8**: 8-bit quantization (smallest size, faster)
- **mixed**: Mixed precision (automatic optimization)

**Recommendation**: Use float16 for most models, int8 for edge devices.

#### Batch Size
- **1**: Single inference (default, most compatible)
- **2-32**: Batch processing (better throughput)
- **Dynamic**: Variable batch size

**Recommendation**: Use 1 for compatibility, higher for throughput.

### Running Compilation

1. **Verify Configuration**
   - Input file selected ✓
   - Output path valid ✓
   - Options configured ✓

2. **Start Compilation**
   - Click "Compile Model" button
   - Button changes to "Cancel"
   - Progress bar appears

3. **Monitor Progress**
   - Watch output log for updates
   - Progress percentage updates in real-time
   - Look for warnings or errors

4. **Completion**
   - Success: "Compilation successful!" message
   - Output file created at specified path
   - Statistics displayed (time, size, etc.)

### Handling Errors

When compilation fails:

1. **Read Error Message**
   - Detailed error displayed in dialog
   - Error type and cause identified
   - Line number or location (if applicable)

2. **Check Suggestions**
   - Fix suggestions provided
   - Common solutions listed
   - Links to relevant documentation

3. **Review Output Log**
   - Scroll through full output
   - Look for warnings before error
   - Check for missing dependencies

4. **Try Solutions**
   - Apply suggested fixes
   - Adjust compiler options
   - Verify model compatibility

## Advanced Features

### Presets Management

**Creating a Preset:**
```
1. Configure desired compiler options
2. Click "Save Preset" button
3. Enter preset name (e.g., "Mobile Optimized")
4. Click Save
```

**Using a Preset:**
```
1. Click "Load Preset" dropdown
2. Select preset name
3. Options automatically applied
```

**Managing Presets:**
```
1. Open Settings → Presets tab
2. View all saved presets
3. Edit, rename, or delete presets
4. Export/import preset files
```

**Example Presets:**
- **Quick Test**: Optimization 0, float32, NPU
- **Production**: Optimization 3, float16, NPU
- **Edge Device**: Optimization 3, int8, CPU
- **Debugging**: Optimization 0, float32, verbose output

### Batch Processing

Process multiple models at once:

```bash
# Command line batch mode
python main.py --batch models/*.onnx --output-dir ./compiled/

# Or use GUI batch dialog:
# Tools → Batch Compilation
# Add multiple input files
# Configure options once
# Compile all
```

### Environment Validation

**Automatic Checks:**
- Python version compatibility
- PySide6 installation
- DXCom compiler availability
- Disk space for output
- Write permissions

**Manual Validation:**
```
Tools → Validate Environment
```

**Pre-compilation Checks:**
- Input file exists and readable
- Output directory writable
- Sufficient disk space
- DXCom compiler functional

### Theme Customization

**Switch Themes:**
```
Settings → Appearance → Theme
- Light (default)
- Dark
- System (follows OS theme)
```

**Custom Themes:**
```
Settings → Appearance → Custom Theme
- Import .qss stylesheet
- Customize colors and fonts
```

### Keyboard Shortcuts

```
Ctrl+O      Open ONNX file
Ctrl+S      Save preset
Ctrl+R      Run compilation
Ctrl+,      Open settings
Ctrl+Q      Quit application
F5          Refresh DXCom detection
F11         Toggle fullscreen
```

## Settings & Configuration

### Application Settings

**Access Settings:**
```
Edit → Settings
Or: Ctrl+,
```

**General Tab:**
- Default input directory
- Default output directory
- Auto-save presets
- Confirm before overwrite

**Appearance Tab:**
- Theme selection
- Font size
- Show tooltips
- Window size/position

**Compilation Tab:**
- Default optimization level
- Default target device
- Default precision mode
- Timeout settings

**Advanced Tab:**
- DXCom path override
- Compiler arguments
- Environment variables
- Debug logging

### Recent Files

**Configuration:**
```
Settings → General → Recent Files
- Maximum recent files: 10 (adjustable)
- Clear history button
```

**Usage:**
- Click recent file in status bar
- Or: File → Recent Files → [filename]

### Log Output Settings

**Configuration:**
```
Settings → Compilation → Log Output
☑ Auto-scroll logs
☑ Timestamp messages
☑ Color-coded output
☑ Save logs to file
```

**Log Levels:**
- Debug: All messages
- Info: Standard messages (default)
- Warning: Warnings and errors only
- Error: Errors only

## Troubleshooting

### Common Issues

**1. DXCom Not Found**
```
Symptom: "DXCom compiler not detected"
Solutions:
- Install DXCom compiler
- Set DXCOM_PATH environment variable
- Specify path in Settings → Advanced
- Check PATH environment variable
```

**2. Compilation Fails Immediately**
```
Symptom: Error right after starting
Solutions:
- Verify ONNX model is valid
- Check input file permissions
- Ensure output directory exists
- Verify sufficient disk space
```

**3. Model Not Compatible**
```
Symptom: "Unsupported operation" error
Solutions:
- Check DXCom supported operations
- Try different optimization level
- Update DXCom to latest version
- Consider model conversion/simplification
```

**4. Out of Memory**
```
Symptom: Compilation stops with memory error
Solutions:
- Close other applications
- Reduce batch size to 1
- Use int8 precision
- Compile on machine with more RAM
```

**5. Slow Compilation**
```
Symptom: Takes very long time
Solutions:
- Lower optimization level
- Reduce model complexity
- Check system resources
- Disable debug logging
```

### Debug Mode

Enable detailed logging:

```bash
# Run with debug flag
python main.py --debug

# Or set environment variable
export DXCOM_GUI_DEBUG=1
python main.py
```

Debug output includes:
- All subprocess commands
- Environment variables
- Internal state changes
- Detailed error traces

## Tips & Best Practices

### Performance Tips

1. **Use Appropriate Optimization**
   - Development: Level 1-2 (faster compilation)
   - Production: Level 3 (better runtime)

2. **Choose Right Precision**
   - Accuracy critical: float32
   - Balanced: float16 (recommended)
   - Performance critical: int8

3. **Batch Size Selection**
   - Testing: Batch size 1
   - Inference: Match your use case
   - Throughput: Higher batch sizes

### Workflow Tips

1. **Save Presets**
   - Create presets for common workflows
   - Share presets with team

2. **Use Recent Files**
   - Quick access to models you test frequently
   - Clear old entries periodically

3. **Monitor Output**
   - Watch for warnings during compilation
   - Save logs for problematic models

4. **Test Incrementally**
   - Start with quick test compilation (level 0)
   - Then optimize for production (level 3)

### Model Preparation

1. **Validate ONNX Model**
   ```bash
   python -m onnx.checker model.onnx
   ```

2. **Optimize ONNX First**
   ```bash
   python -m onnxoptimizer model.onnx optimized.onnx
   ```

3. **Check Model Info**
   ```bash
   python -m onnx.tools.net_drawer model.onnx model.png
   ```

### Automation

**Script Compilation:**
```python
from src.dxcom_wrapper import compile_model

compile_model(
    input_path="model.onnx",
    output_path="model.dxnn",
    options={
        'optimization_level': '3',
        'target_device': 'NPU',
        'precision': 'float16'
    }
)
```

**Batch Script:**
```bash
#!/bin/bash
for model in models/*.onnx; do
    python main.py --input "$model" \
                   --output "compiled/$(basename $model .onnx).dxnn" \
                   --optimize 3
done
```

## Getting Help

### Resources

- **README**: Project overview and quick start
- **Installation Guide**: `docs/INSTALLATION.md`
- **API Reference**: `docs/API.md` (for developers)
- **FAQ**: `docs/FAQ.md`

### Support Channels

- **GitHub Issues**: Bug reports and feature requests
- **Email**: support@example.com
- **Documentation**: https://docs.example.com
- **Community Forum**: https://forum.example.com

### Reporting Bugs

Include in bug reports:
1. DXCom GUI version
2. Operating system and version
3. Python and PySide6 versions
4. Steps to reproduce
5. Error messages and logs
6. Sample model (if possible)

---

**Happy Compiling!** 🚀
