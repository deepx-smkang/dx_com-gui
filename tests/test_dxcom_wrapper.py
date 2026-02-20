#!/usr/bin/env python3
"""
Test/demo script for DXCom wrapper.

This script demonstrates how to use the DXComWrapper and DXComExecutor classes.
It can be used for testing the wrapper independently of the GUI.
"""
import sys
import os
from PySide6.QtCore import QCoreApplication

# Add parent directory to path to import src package
sys.path.insert(0, os.path.dirname(__file__))

from src.dxcom_wrapper import DXComWrapper


def main():
    """Run a test compilation."""
    app = QCoreApplication(sys.argv)
    
    # Example configuration
    input_path = "/path/to/model.onnx"
    output_path = "/path/to/output.dxnn"
    compiler_options = {
        'config_path': '/path/to/config.json',
        'opt_level': 1,
        'gen_log': True,
        'aggressive_partitioning': False,
        'compile_input_nodes': '',
        'compile_output_nodes': ''
    }
    
    # Create wrapper
    wrapper = DXComWrapper()
    
    # Create executor
    executor = wrapper.compile(
        input_path=input_path,
        output_path=output_path,
        compiler_options=compiler_options
    )
    
    # Connect signals
    executor.output_received.connect(lambda line: print(f"[OUTPUT] {line}", end=''))
    executor.progress_updated.connect(lambda pct, msg: print(f"[PROGRESS] {pct}% - {msg}"))
    executor.error_occurred.connect(lambda err: print(f"[ERROR] {err}"))
    executor.compilation_finished.connect(
        lambda success, msg: (
            print(f"\n[FINISHED] Success={success}, Message={msg}"),
            app.quit()
        )
    )
    
    print("=" * 60)
    print("DXCom Wrapper Test")
    print("=" * 60)
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"Options: {compiler_options}")
    print("=" * 60)
    print("\nStarting compilation...\n")
    
    # Start execution
    executor.start()
    
    # Run event loop
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
