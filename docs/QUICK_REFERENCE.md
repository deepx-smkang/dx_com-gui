# DXCom Wrapper - Quick Reference

## Import

```python
from .dxcom_wrapper import DXComWrapper
```

## Initialize (once, in __init__)

```python
self.dxcom_wrapper = DXComWrapper()
self.current_executor = None
```

## Start Compilation

```python
executor = self.dxcom_wrapper.compile(
    input_path=self.input_model_path,
    output_path=self.output_model_path,
    compiler_options=self.get_compiler_options()
)

# Connect signals
executor.output_received.connect(handler)      # (str)
executor.progress_updated.connect(handler)     # (int, str)
executor.compilation_finished.connect(handler) # (bool, str)
executor.error_occurred.connect(handler)       # (str)

# Start
executor.start()
```

## Signal Handlers

```python
def on_output(line: str):
    """Raw compiler output"""
    print(line, end='')

def on_progress(percentage: int, message: str):
    """Progress update"""
    status_bar.showMessage(f"{percentage}% - {message}")

def on_finished(success: bool, message: str):
    """Compilation complete"""
    if success:
        show_success_dialog(message)
    else:
        show_error_dialog(message)

def on_error(error: str):
    """Error occurred"""
    show_error_dialog(error)
```

## Cancel Compilation

```python
if self.dxcom_wrapper.is_running():
    self.dxcom_wrapper.stop_current()
```

## Check Status

```python
is_running = self.dxcom_wrapper.is_running()
```

## Common Patterns

### Disable UI During Compilation

```python
def start_compile():
    self.compile_button.setEnabled(False)
    executor.start()

def on_finished(success, msg):
    self.compile_button.setEnabled(True)
```

### Display Output in TextEdit

```python
executor.output_received.connect(self.output_widget.append)
```

### Update ProgressBar

```python
executor.progress_updated.connect(
    lambda pct, msg: self.progress_bar.setValue(pct)
)
```

### Show StatusBar Updates

```python
executor.progress_updated.connect(
    lambda pct, msg: self.statusBar().showMessage(f"{pct}% - {msg}")
)
```

## Error Messages

- `"dxcom not found"` → Install dxcom or add to PATH
- `"Compilation failed with exit code N"` → Check dxcom output
- Other exceptions → Check input paths and permissions

## Important Notes

⚠️ **Always connect signals BEFORE calling .start()**

⚠️ **Use .start() not .run()** (.run() blocks the GUI!)

⚠️ **Disable compile button during execution**

✅ **Signals are thread-safe** (Qt handles this automatically)

✅ **Executor cleans up automatically** on completion or error

## Full Example

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dxcom_wrapper = DXComWrapper()
        self.compile_button.clicked.connect(self._on_compile)
    
    def _on_compile(self):
        executor = self.dxcom_wrapper.compile(
            input_path=self.input_model_path,
            output_path=self.output_model_path,
            compiler_options=self.get_compiler_options()
        )
        
        executor.output_received.connect(
            self.output_display.append
        )
        executor.progress_updated.connect(
            lambda pct, msg: self.statusBar().showMessage(f"{pct}%: {msg}")
        )
        executor.compilation_finished.connect(
            self._on_finished
        )
        executor.error_occurred.connect(
            lambda err: QMessageBox.critical(self, "Error", err)
        )
        
        self.compile_button.setEnabled(False)
        executor.start()
    
    def _on_finished(self, success, message):
        self.compile_button.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.warning(self, "Failed", message)
```
