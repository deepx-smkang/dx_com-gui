"""
JSON Configuration Editor Dialog.

Provides a separate window to view and edit JSON configuration files
for DXCom compiler with syntax validation.
"""
import json
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCharFormat, QColor, QSyntaxHighlighter


class JsonSyntaxHighlighter(QSyntaxHighlighter):
    """Simple JSON syntax highlighter."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Define formats
        self.key_format = QTextCharFormat()
        self.key_format.setForeground(QColor("#569cd6"))  # Blue for keys
        self.key_format.setFontWeight(QFont.Weight.Bold)
        
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#ce9178"))  # Orange for strings
        
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor("#b5cea8"))  # Light green for numbers
        
        self.bool_format = QTextCharFormat()
        self.bool_format.setForeground(QColor("#569cd6"))  # Blue for booleans
        
        self.bracket_format = QTextCharFormat()
        self.bracket_format.setForeground(QColor("#ffd700"))  # Gold for brackets
    
    def highlightBlock(self, text):
        """Apply syntax highlighting to a block of text."""
        # Highlight JSON keys (quoted strings followed by colon)
        import re
        
        # Keys: "key":
        for match in re.finditer(r'"([^"]+)"\s*:', text):
            self.setFormat(match.start(), match.end() - match.start(), self.key_format)
        
        # String values: "value" (not followed by colon)
        for match in re.finditer(r':\s*"([^"]*)"', text):
            start = match.start() + text[match.start():].index('"')
            length = len(match.group(0)) - (start - match.start())
            self.setFormat(start, length, self.string_format)
        
        # Numbers
        for match in re.finditer(r'\b\d+\.?\d*\b', text):
            self.setFormat(match.start(), match.end() - match.start(), self.number_format)
        
        # Booleans and null
        for match in re.finditer(r'\b(true|false|null)\b', text):
            self.setFormat(match.start(), match.end() - match.start(), self.bool_format)
        
        # Brackets
        for match in re.finditer(r'[{}\[\]]', text):
            self.setFormat(match.start(), 1, self.bracket_format)


class JsonConfigDialog(QDialog):
    """Dialog for viewing and editing JSON configuration."""
    
    def __init__(self, json_path, parent=None):
        super().__init__(parent)
        self.json_path = json_path
        self.original_content = ""
        self.modified = False
        
        self.setWindowTitle(f"JSON Configuration - {json_path.split('/')[-1]}")
        self.setMinimumSize(700, 600)
        self.setModal(False)  # Allow interaction with main window
        
        self._setup_ui()
        self._load_json()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header
        header_label = QLabel("JSON Configuration Editor")
        header_label.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 5px;")
        layout.addWidget(header_label)
        
        # File path label
        self.path_label = QLabel(f"File: {self.json_path}")
        self.path_label.setStyleSheet("color: #888; padding: 2px;")
        layout.addWidget(self.path_label)
        
        # JSON editor
        self.json_editor = QTextEdit()
        self.json_editor.setFont(QFont("Courier New", 10))
        self.json_editor.setPlaceholderText("JSON configuration will appear here...")
        self.json_editor.textChanged.connect(self._on_text_changed)
        
        # Apply syntax highlighting
        self.highlighter = JsonSyntaxHighlighter(self.json_editor.document())
        
        layout.addWidget(self.json_editor)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; font-style: italic; padding: 2px;")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Validate button
        validate_btn = QPushButton("Validate JSON")
        validate_btn.setToolTip("Check if JSON syntax is valid")
        validate_btn.clicked.connect(self._validate_json)
        button_layout.addWidget(validate_btn)
        
        # Format button
        format_btn = QPushButton("Format")
        format_btn.setToolTip("Auto-format JSON with proper indentation")
        format_btn.clicked.connect(self._format_json)
        button_layout.addWidget(format_btn)
        
        # Save button
        self.save_btn = QPushButton("Save")
        self.save_btn.setToolTip("Save changes to file")
        self.save_btn.clicked.connect(self._save_json)
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _load_json(self):
        """Load JSON content from file."""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.original_content = content
                
                # Try to parse and pretty-print
                try:
                    data = json.loads(content)
                    formatted = json.dumps(data, indent=2, ensure_ascii=False)
                    self.json_editor.setPlainText(formatted)
                except json.JSONDecodeError:
                    # If invalid JSON, show as-is
                    self.json_editor.setPlainText(content)
                    self.status_label.setText("⚠ Warning: Invalid JSON syntax")
                    self.status_label.setStyleSheet("color: #ff6b6b; font-style: italic;")
                
                self.modified = False
                self.save_btn.setEnabled(False)
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load JSON file:\n{str(e)}"
            )
            self.close()
    
    def _on_text_changed(self):
        """Handle text changes in the editor."""
        current_content = self.json_editor.toPlainText()
        self.modified = (current_content != self.original_content)
        self.save_btn.setEnabled(self.modified)
        
        if self.modified:
            self.status_label.setText("● Modified (unsaved changes)")
            self.status_label.setStyleSheet("color: #ffa500; font-style: italic;")
        else:
            self.status_label.setText("")
    
    def _validate_json(self):
        """Validate JSON syntax."""
        content = self.json_editor.toPlainText()
        
        if not content.strip():
            QMessageBox.warning(self, "Validation", "JSON content is empty")
            return
        
        try:
            json.loads(content)
            QMessageBox.information(
                self,
                "Validation Success",
                "✓ JSON syntax is valid!"
            )
            self.status_label.setText("✓ Valid JSON")
            self.status_label.setStyleSheet("color: #4CAF50; font-style: italic;")
        except json.JSONDecodeError as e:
            QMessageBox.warning(
                self,
                "Validation Error",
                f"Invalid JSON syntax:\n\n{str(e)}"
            )
            self.status_label.setText(f"✗ Invalid JSON: {str(e)}")
            self.status_label.setStyleSheet("color: #ff6b6b; font-style: italic;")
    
    def _format_json(self):
        """Auto-format JSON with proper indentation."""
        content = self.json_editor.toPlainText()
        
        try:
            data = json.loads(content)
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            self.json_editor.setPlainText(formatted)
            self.status_label.setText("✓ JSON formatted")
            self.status_label.setStyleSheet("color: #4CAF50; font-style: italic;")
        except json.JSONDecodeError as e:
            QMessageBox.warning(
                self,
                "Format Error",
                f"Cannot format invalid JSON:\n\n{str(e)}"
            )
    
    def _save_json(self):
        """Save JSON content to file."""
        content = self.json_editor.toPlainText()
        
        # Validate before saving
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            reply = QMessageBox.question(
                self,
                "Invalid JSON",
                f"JSON syntax is invalid:\n\n{str(e)}\n\nSave anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.original_content = content
            self.modified = False
            self.save_btn.setEnabled(False)
            
            self.status_label.setText("✓ Saved successfully")
            self.status_label.setStyleSheet("color: #4CAF50; font-style: italic;")
            
            QMessageBox.information(
                self,
                "Save Success",
                f"Configuration saved to:\n{self.json_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save JSON file:\n{str(e)}"
            )
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Close anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        
        event.accept()
