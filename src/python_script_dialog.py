"""
Python Script Editor Dialog.

Provides a separate window to view and edit generated Python compilation scripts
with syntax highlighting.
"""
import os
import re
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCharFormat, QColor, QSyntaxHighlighter


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    """Simple Python syntax highlighter."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Define formats
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#569cd6"))  # Blue for keywords
        self.keyword_format.setFontWeight(QFont.Weight.Bold)
        
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#ce9178"))  # Orange for strings
        
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#6a9955"))  # Green for comments
        
        self.function_format = QTextCharFormat()
        self.function_format.setForeground(QColor("#dcdcaa"))  # Yellow for functions
        
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor("#b5cea8"))  # Light green for numbers
        
        self.builtin_format = QTextCharFormat()
        self.builtin_format.setForeground(QColor("#4ec9b0"))  # Cyan for builtins
        
        # Python keywords
        self.keywords = [
            'import', 'from', 'def', 'class', 'if', 'else', 'elif', 'for', 'while',
            'return', 'try', 'except', 'finally', 'with', 'as', 'in', 'is', 'not',
            'and', 'or', 'True', 'False', 'None', 'pass', 'break', 'continue'
        ]
        
        # Python builtins
        self.builtins = [
            'print', 'len', 'range', 'str', 'int', 'float', 'list', 'dict', 'set',
            'tuple', 'open', 'file', 'type', 'isinstance', 'hasattr', 'getattr'
        ]
    
    def highlightBlock(self, text):
        """Apply syntax highlighting to a block of text."""
        # Comments (highest priority)
        for match in re.finditer(r'#.*$', text):
            self.setFormat(match.start(), match.end() - match.start(), self.comment_format)
        
        # Triple-quoted strings
        for match in re.finditer(r'""".*?"""', text, re.DOTALL):
            self.setFormat(match.start(), match.end() - match.start(), self.string_format)
        
        for match in re.finditer(r"'''.*?'''", text, re.DOTALL):
            self.setFormat(match.start(), match.end() - match.start(), self.string_format)
        
        # Single and double quoted strings
        for match in re.finditer(r'"[^"\\]*(\\.[^"\\]*)*"', text):
            self.setFormat(match.start(), match.end() - match.start(), self.string_format)
        
        for match in re.finditer(r"'[^'\\]*(\\.[^'\\]*)*'", text):
            self.setFormat(match.start(), match.end() - match.start(), self.string_format)
        
        # Raw strings
        for match in re.finditer(r'r"[^"]*"', text):
            self.setFormat(match.start(), match.end() - match.start(), self.string_format)
        
        for match in re.finditer(r"r'[^']*'", text):
            self.setFormat(match.start(), match.end() - match.start(), self.string_format)
        
        # Keywords
        for keyword in self.keywords:
            pattern = r'\b' + keyword + r'\b'
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), self.keyword_format)
        
        # Builtins
        for builtin in self.builtins:
            pattern = r'\b' + builtin + r'\b'
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), self.builtin_format)
        
        # Function definitions
        for match in re.finditer(r'\bdef\s+(\w+)', text):
            start = match.start(1)
            length = match.end(1) - start
            self.setFormat(start, length, self.function_format)
        
        # Function calls
        for match in re.finditer(r'\b(\w+)\s*\(', text):
            if match.group(1) not in self.keywords:
                start = match.start(1)
                length = match.end(1) - start
                self.setFormat(start, length, self.function_format)
        
        # Numbers
        for match in re.finditer(r'\b\d+\.?\d*\b', text):
            self.setFormat(match.start(), match.end() - match.start(), self.number_format)


class PythonScriptDialog(QDialog):
    """Dialog for viewing and editing generated Python scripts."""
    
    def __init__(self, script_content: str, default_filename: str = "compile_model.py", parent=None):
        super().__init__(parent)
        self.script_content = script_content
        self.default_filename = default_filename
        self.has_unsaved_changes = False
        self.saved_file_path = None  # Track the saved file path
        
        self.setWindowTitle("Python Script Editor")
        self.setMinimumSize(900, 700)
        self.setModal(False)  # Allow interaction with main window
        
        self._setup_ui()
        self._load_content()
    
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        
        # Info label
        info_label = QLabel(
            "Review and edit the generated Python script. "
            "Click 'Save' to write it to a file."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Text editor with syntax highlighting
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Courier New", 10))
        self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                selection-background-color: #264f78;
            }
        """)
        self.text_edit.textChanged.connect(self._on_text_changed)
        
        # Apply syntax highlighting
        self.highlighter = PythonSyntaxHighlighter(self.text_edit.document())
        
        layout.addWidget(self.text_edit)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Save button
        save_button = QPushButton("Save As...")
        save_button.setMinimumWidth(100)
        save_button.setToolTip("Save script to a Python file")
        save_button.clicked.connect(self._on_save)
        button_layout.addWidget(save_button)
        
        # Copy to clipboard button
        copy_button = QPushButton("Copy to Clipboard")
        copy_button.setMinimumWidth(130)
        copy_button.setToolTip("Copy script to clipboard")
        copy_button.clicked.connect(self._on_copy)
        button_layout.addWidget(copy_button)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.setMinimumWidth(100)
        close_button.setToolTip("Close editor")
        close_button.clicked.connect(self._on_close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def _load_content(self):
        """Load the script content into the editor."""
        self.text_edit.setPlainText(self.script_content)
        self.has_unsaved_changes = False
    
    def _on_text_changed(self):
        """Handle text changes."""
        self.has_unsaved_changes = True
    
    def _on_save(self):
        """Save the script to a file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Python Script",
            self.default_filename,
            "Python Files (*.py);;All Files (*)"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.text_edit.toPlainText())
            
            # Make executable on Unix systems
            if os.name != 'nt':  # Not Windows
                os.chmod(file_path, 0o755)
            
            self.has_unsaved_changes = False
            self.saved_file_path = file_path  # Store the saved path
            
            QMessageBox.information(
                self,
                "Script Saved",
                f"Python script saved successfully!\n\n"
                f"Location: {file_path}\n\n"
                f"This script will be used when you click 'Compile'.\n"
                f"To generate a new script, click 'Generate Python Script' again.",
                QMessageBox.StandardButton.Ok
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save script:\n{str(e)}",
                QMessageBox.StandardButton.Ok
            )
    
    def _on_copy(self):
        """Copy script to clipboard."""
        QApplication.clipboard().setText(self.text_edit.toPlainText())
        QMessageBox.information(
            self,
            "Copied",
            "Script copied to clipboard!",
            QMessageBox.StandardButton.Ok
        )
    
    def _on_close(self):
        """Close the dialog."""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Close without saving?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
        
        self.accept()
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Close without saving?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        
        event.accept()
