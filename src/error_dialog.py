"""
GUI Error Dialog for displaying compilation errors.

Provides user-friendly error dialogs with detailed information,
suggestions, and options to view technical details.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from .error_handler import DXComError, format_error_for_display


class ErrorDialog(QDialog):
    """
    Dialog for displaying compilation errors with detailed information.
    
    Shows user-friendly error message with suggestions and optionally
    detailed technical information.
    """
    
    def __init__(self, error: DXComError, parent=None):
        """
        Initialize the error dialog.
        
        Args:
            error: DXComError object with error details
            parent: Parent widget
        """
        super().__init__(parent)
        self.error = error
        
        self.setWindowTitle("Compilation Error")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Error icon and title
        header_layout = QHBoxLayout()
        
        # Error message
        error_label = QLabel(self.error.user_message)
        error_label.setWordWrap(True)
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        error_label.setFont(font)
        header_layout.addWidget(error_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Exit code if available
        if self.error.exit_code is not None:
            exit_code_label = QLabel(f"Exit code: {self.error.exit_code}")
            exit_code_label.setStyleSheet("color: #666;")
            layout.addWidget(exit_code_label)
        
        # Suggestions section
        if self.error.suggestions:
            suggestions_label = QLabel("<b>Suggestions:</b>")
            layout.addWidget(suggestions_label)
            
            for i, suggestion in enumerate(self.error.suggestions, 1):
                suggestion_text = QLabel(f"  {i}. {suggestion}")
                suggestion_text.setWordWrap(True)
                suggestion_text.setStyleSheet("margin-left: 10px;")
                layout.addWidget(suggestion_text)
        
        layout.addSpacing(10)
        
        # Technical details section (collapsible)
        if self.error.technical_details:
            details_label = QLabel("<b>Technical Details:</b>")
            layout.addWidget(details_label)
            
            self.details_text = QTextEdit()
            self.details_text.setReadOnly(True)
            self.details_text.setPlainText(self.error.technical_details)
            self.details_text.setMaximumHeight(150)
            self.details_text.setStyleSheet("""
                QTextEdit {
                    background-color: #f5f5f5;
                    border: 1px solid #ccc;
                    font-family: monospace;
                    font-size: 9pt;
                }
            """)
            layout.addWidget(self.details_text)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Copy error button
        copy_button = QPushButton("Copy Error Details")
        copy_button.clicked.connect(self._on_copy_error)
        button_layout.addWidget(copy_button)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.setDefault(True)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def _on_copy_error(self):
        """Copy full error details to clipboard."""
        from PySide6.QtWidgets import QApplication
        
        error_text = format_error_for_display(self.error, include_technical=True)
        clipboard = QApplication.clipboard()
        clipboard.setText(error_text)
        
        # Show brief confirmation
        QMessageBox.information(
            self,
            "Copied",
            "Error details copied to clipboard.",
            QMessageBox.Ok
        )


def show_error_dialog(error: DXComError, parent=None) -> int:
    """
    Show error dialog for a DXComError.
    
    Args:
        error: DXComError object
        parent: Parent widget
        
    Returns:
        Dialog result code
    """
    dialog = ErrorDialog(error, parent)
    return dialog.exec()


def show_simple_error(title: str, message: str, parent=None):
    """
    Show a simple error message box.
    
    Args:
        title: Dialog title
        message: Error message
        parent: Parent widget
    """
    QMessageBox.critical(parent, title, message, QMessageBox.Ok)
