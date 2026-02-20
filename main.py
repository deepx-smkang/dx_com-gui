#!/usr/bin/env python3
"""
DXCom GUI - Main application entry point.

This module serves as the entry point for the DXCom GUI application.
It initializes the Qt application, creates the main window, and starts
the event loop.

Usage:
    python main.py [options]
    
Command line options:
    --input FILE        Path to input ONNX model
    --output FILE       Path to output DXNN file
    --theme THEME       UI theme (light/dark)
    --dxcom-path PATH   Custom DXCom compiler path
    --debug             Enable debug logging

Example:
    python main.py --input model.onnx --theme dark
"""
import sys
import argparse
from PySide6.QtWidgets import QApplication
from src import MainWindow


def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description='DXCom GUI - ONNX to DXNN Model Compiler',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--input',
        metavar='FILE',
        help='Input ONNX model file path'
    )
    
    parser.add_argument(
        '--output',
        metavar='FILE',
        help='Output DXNN file path'
    )
    
    parser.add_argument(
        '--theme',
        choices=['light', 'dark'],
        default='light',
        help='UI theme (default: light)'
    )
    
    parser.add_argument(
        '--dxcom-path',
        metavar='PATH',
        help='Custom DXCom compiler path'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    return parser.parse_args()


def main():
    """
    Main application entry point.
    
    Initializes the Qt application framework, creates and displays
    the main window, then starts the Qt event loop.
    
    Returns:
        int: Application exit code (0 for success, non-zero for errors)
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Create Qt application instance
    app = QApplication(sys.argv)
    
    # Force Fusion style to prevent system theme (dark mode) from interfering
    app.setStyle('Fusion')
    
    # Set application metadata
    app.setApplicationName("DXCom GUI")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("DXCom")
    app.setOrganizationDomain("example.com")
    
    # Set application icon globally
    from PySide6.QtGui import QIcon
    import os
    
    icon = QIcon()
    icon_sizes = ['deepx_16.png', 'deepx_32.png', 'deepx_64.png', 'deepx_128.png']
    
    # Try to find icons
    base_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources'),
    ]
    
    for base_path in base_paths:
        for icon_file in icon_sizes:
            icon_path = os.path.join(base_path, icon_file)
            if os.path.exists(icon_path):
                icon.addFile(icon_path)
        if not icon.isNull():
            app.setWindowIcon(icon)
            break
    
    # Create and show main window
    window = MainWindow()
    
    # Apply command line arguments
    if args.input:
        window.set_input_path(args.input)
    if args.output:
        window.set_output_path(args.output)
    if args.theme:
        window.apply_theme(args.theme)
    if args.dxcom_path:
        window.set_dxcom_path(args.dxcom_path)
    if args.debug:
        window.enable_debug_logging()
    
    window.show()
    
    # Start event loop and return exit code
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
