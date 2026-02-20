# Integration Guide: Connecting DXComWrapper to MainWindow

## Overview

This guide shows how to integrate the `DXComWrapper` module with the existing `MainWindow` to enable actual compilation functionality.

## Step 1: Import the Wrapper

Add to `src/main_window.py`:

```python
from .dxcom_wrapper import DXComWrapper
```

## Step 2: Initialize Wrapper in __init__

In `MainWindow.__init__()`, add:

```python
# DXCom wrapper for compilation
self.dxcom_wrapper = DXComWrapper()
self.current_executor = None
```

## Step 3: Connect Compile Button

Find where `self.compile_button` is created and add:

```python
self.compile_button.clicked.connect(self._on_compile_clicked)
```

## Step 4: Implement Compilation Handler

Add this method to `MainWindow`:

```python
def _on_compile_clicked(self):
    """Handle compile button click - start compilation."""
    # Validate inputs
    if not self.input_model_path or not self.output_model_path:
        QMessageBox.warning(self, "Validation Error", 
                          "Please specify input and output paths")
        return
    
    # Get configuration
    compiler_options = self.get_compiler_options()
    
    # Create executor
    self.current_executor = self.dxcom_wrapper.compile(
        input_path=self.input_model_path,
        output_path=self.output_model_path,
        compiler_options=compiler_options
    )
    
    # Connect signals
    self.current_executor.output_received.connect(self._on_output_received)
    self.current_executor.progress_updated.connect(self._on_progress_updated)
    self.current_executor.compilation_finished.connect(self._on_compilation_finished)
    self.current_executor.error_occurred.connect(self._on_error_occurred)
    
    # Update UI state
    self.compile_button.setEnabled(False)
    self.compile_button.setText("Compiling...")
    
    # Start compilation
    self.current_executor.start()
    
    # Update status bar
    self.statusBar().showMessage("Compilation started...")
```

## Step 5: Implement Signal Handlers

Add these methods to handle compilation events:

```python
def _on_output_received(self, line: str):
    """Handle compiler output line."""
    # Display in output widget (if you have one)
    # For now, just print or store
    print(f"[DXCOM] {line}", end='')

def _on_progress_updated(self, percentage: int, message: str):
    """Handle progress update."""
    self.statusBar().showMessage(f"Compiling: {percentage}% - {message}")

def _on_compilation_finished(self, success: bool, message: str):
    """Handle compilation completion."""
    # Re-enable compile button
    self.compile_button.setEnabled(True)
    self.compile_button.setText("Compile")
    
    # Show result
    if success:
        QMessageBox.information(self, "Success", 
                              f"Compilation completed!\n\n{message}")
        self.statusBar().showMessage("Compilation successful", 5000)
    else:
        QMessageBox.warning(self, "Compilation Failed", 
                          f"Compilation failed.\n\n{message}")
        self.statusBar().showMessage("Compilation failed", 5000)

def _on_error_occurred(self, error_message: str):
    """Handle compilation error."""
    QMessageBox.critical(self, "Error", error_message)
    self.statusBar().showMessage(f"Error: {error_message}", 5000)
```

## Step 6: (Optional) Add Cancel Button

If you want to allow canceling compilation:

```python
# In _setup_ui():
self.cancel_button = QPushButton("Cancel")
self.cancel_button.setEnabled(False)
self.cancel_button.clicked.connect(self._on_cancel_clicked)

# Handler:
def _on_cancel_clicked(self):
    """Cancel ongoing compilation."""
    if self.dxcom_wrapper.is_running():
        self.dxcom_wrapper.stop_current()
        self.statusBar().showMessage("Cancelling compilation...", 3000)
```

## Step 7: Update UI State Management

Modify `_on_compile_clicked` to disable/enable buttons:

```python
def _on_compile_clicked(self):
    # ... (previous code)
    
    # Update UI state
    self.compile_button.setEnabled(False)
    self.cancel_button.setEnabled(True)  # If you have one
    
    # ... start compilation

def _on_compilation_finished(self, success: bool, message: str):
    # ... (previous code)
    
    # Reset UI state
    self.compile_button.setEnabled(True)
    self.cancel_button.setEnabled(False)  # If you have one
```

## Complete Example

Here's a minimal complete integration:

```python
# In main_window.py

from .dxcom_wrapper import DXComWrapper

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... existing init code ...
        
        # Add wrapper
        self.dxcom_wrapper = DXComWrapper()
        self.current_executor = None
        
        # ... rest of init ...
    
    def _setup_ui(self):
        # ... existing UI setup ...
        
        # Connect compile button
        self.compile_button.clicked.connect(self._on_compile_clicked)
    
    def _on_compile_clicked(self):
        if not self.input_model_path or not self.output_model_path:
            QMessageBox.warning(self, "Error", "Please specify input and output")
            return
        
        self.current_executor = self.dxcom_wrapper.compile(
            input_path=self.input_model_path,
            output_path=self.output_model_path,
            compiler_options=self.get_compiler_options()
        )
        
        self.current_executor.output_received.connect(
            lambda line: print(f"[OUT] {line}", end='')
        )
        self.current_executor.progress_updated.connect(
            lambda pct, msg: self.statusBar().showMessage(f"{pct}% - {msg}")
        )
        self.current_executor.compilation_finished.connect(
            self._on_compilation_finished
        )
        self.current_executor.error_occurred.connect(
            lambda err: QMessageBox.critical(self, "Error", err)
        )
        
        self.compile_button.setEnabled(False)
        self.current_executor.start()
    
    def _on_compilation_finished(self, success: bool, message: str):
        self.compile_button.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.warning(self, "Failed", message)
```

## Testing

1. Ensure `dxcom` is in your PATH
2. Run the application: `python main.py`
3. Select input ONNX file
4. Select output path
5. Configure compiler options
6. Click "Compile"
7. Watch the status bar for progress
8. See result dialog when complete

## Next Steps

After basic integration works:

1. Add output display widget (QTextEdit) for compiler output
2. Add progress bar widget
3. Add cancel functionality
4. Add compilation history
5. Save compilation logs

## Troubleshooting

**Problem**: "dxcom not found" error
- **Solution**: Ensure dxcom is installed and in PATH

**Problem**: GUI freezes during compilation
- **Solution**: Check that you're using `.start()` not `.run()` on executor

**Problem**: Signals not working
- **Solution**: Connect signals BEFORE calling `.start()`

**Problem**: Multiple clicks start multiple compilations
- **Solution**: Disable compile button during compilation
