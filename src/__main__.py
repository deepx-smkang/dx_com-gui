#!/usr/bin/env python3
"""
DXCom GUI - Package entry point.

This module allows the package to be run as: python -m src
"""
import sys
import argparse
from PySide6.QtWidgets import QApplication
from . import MainWindow


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
        '--theme',
        choices=['light', 'dark'],
        default=None,
        help='UI theme (default: light)'
    )
    
    parser.add_argument(
        '--dxcom-path',
        metavar='PATH',
        help='Custom DXCom compiler path'
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
    
    # Set application metadata
    app.setApplicationName("DXCom GUI")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("DXCom")
    app.setOrganizationDomain("example.com")
    
    # Set application icon globally
    import os
    from PySide6.QtGui import QIcon
    
    icon = QIcon()
    icon_sizes = ['deepx_16.png', 'deepx_32.png', 'deepx_64.png', 'deepx_128.png']
    
    # Icons live in src/resources/ (installed as src.resources package data)
    base_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources'),
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
    if args.theme:
        window.apply_theme(args.theme)
    if args.dxcom_path:
        window.set_dxcom_path(args.dxcom_path)

    window.show()
    
    # Start event loop and return exit code
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
