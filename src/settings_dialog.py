"""
Settings dialog for DXCom GUI application preferences.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QCheckBox, QComboBox, QLineEdit, QPushButton,
    QGroupBox, QFormLayout, QSpinBox, QFileDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt


class SettingsDialog(QDialog):
    """Dialog for editing application settings."""
    
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("Settings")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        
        self._setup_ui()
        self._load_current_settings()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # General tab
        general_tab = self._create_general_tab()
        tabs.addTab(general_tab, "General")
        
        # Appearance tab
        appearance_tab = self._create_appearance_tab()
        tabs.addTab(appearance_tab, "Appearance")
        
        # Advanced tab
        advanced_tab = self._create_advanced_tab()
        tabs.addTab(advanced_tab, "Advanced")
        
        layout.addWidget(tabs)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.RestoreDefaults
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(
            self._on_restore_defaults
        )
        layout.addWidget(button_box)
    
    def _create_general_tab(self) -> QWidget:
        """Create the general settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Default paths group
        paths_group = QGroupBox("Default Paths")
        paths_layout = QFormLayout()
        
        # Default input path
        input_layout = QHBoxLayout()
        self.default_input_field = QLineEdit()
        input_layout.addWidget(self.default_input_field)
        browse_input_btn = QPushButton("Browse...")
        browse_input_btn.clicked.connect(self._browse_default_input)
        input_layout.addWidget(browse_input_btn)
        paths_layout.addRow("Default Input Path:", input_layout)
        
        # Default output path
        output_layout = QHBoxLayout()
        self.default_output_field = QLineEdit()
        output_layout.addWidget(self.default_output_field)
        browse_output_btn = QPushButton("Browse...")
        browse_output_btn.clicked.connect(self._browse_default_output)
        output_layout.addWidget(browse_output_btn)
        paths_layout.addRow("Default Output Path:", output_layout)

        # Default JSON config path
        json_layout = QHBoxLayout()
        self.default_json_field = QLineEdit()
        json_layout.addWidget(self.default_json_field)
        browse_json_btn = QPushButton("Browse...")
        browse_json_btn.clicked.connect(self._browse_default_json)
        json_layout.addWidget(browse_json_btn)
        paths_layout.addRow("Default JSON Path:", json_layout)

        # Default Dataset path
        dataset_layout = QHBoxLayout()
        self.default_dataset_field = QLineEdit()
        dataset_layout.addWidget(self.default_dataset_field)
        browse_dataset_btn = QPushButton("Browse...")
        browse_dataset_btn.clicked.connect(self._browse_default_dataset)
        dataset_layout.addWidget(browse_dataset_btn)
        paths_layout.addRow("Default Dataset Path:", dataset_layout)

        paths_group.setLayout(paths_layout)
        layout.addWidget(paths_group)
        
        # Behavior group
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QFormLayout()
        
        self.auto_save_checkbox = QCheckBox("Auto-save preset after successful compilation")
        behavior_layout.addRow(self.auto_save_checkbox)
        
        self.confirm_overwrite_checkbox = QCheckBox("Confirm before overwriting files")
        behavior_layout.addRow(self.confirm_overwrite_checkbox)
        
        self.show_tooltips_checkbox = QCheckBox("Show tooltips")
        behavior_layout.addRow(self.show_tooltips_checkbox)
        
        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)
        
        layout.addStretch()
        return widget
    
    def _create_appearance_tab(self) -> QWidget:
        """Create the appearance settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        appearance_group = QGroupBox("Theme")
        appearance_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        appearance_layout.addRow("Application Theme:", self.theme_combo)
        
        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)
        
        # Log viewer group
        log_group = QGroupBox("Log Viewer")
        log_layout = QFormLayout()
        
        self.auto_scroll_checkbox = QCheckBox("Auto-scroll to bottom during compilation")
        log_layout.addRow(self.auto_scroll_checkbox)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        layout.addStretch()
        return widget
    
    def _create_advanced_tab(self) -> QWidget:
        """Create the advanced settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        advanced_group = QGroupBox("Advanced")
        advanced_layout = QFormLayout()
        
        self.max_recent_spinbox = QSpinBox()
        self.max_recent_spinbox.setMinimum(1)
        self.max_recent_spinbox.setMaximum(50)
        advanced_layout.addRow("Maximum Recent Files:", self.max_recent_spinbox)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # Actions group
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()
        
        clear_recent_btn = QPushButton("Clear Recent Files History")
        clear_recent_btn.clicked.connect(self._on_clear_recent_files)
        actions_layout.addWidget(clear_recent_btn)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        layout.addStretch()
        return widget
    
    def _load_current_settings(self):
        """Load current settings into UI."""
        settings = self.settings_manager.get_all()
        
        # General
        self.default_input_field.setText(settings.get('default_input_path', ''))
        self.default_output_field.setText(settings.get('default_output_path', ''))
        self.default_json_field.setText(settings.get('default_json_path', ''))
        self.default_dataset_field.setText(settings.get('default_dataset_path', ''))
        self.auto_save_checkbox.setChecked(settings.get('auto_save_preset', False))
        self.confirm_overwrite_checkbox.setChecked(settings.get('confirm_overwrite', True))
        self.show_tooltips_checkbox.setChecked(settings.get('show_tooltips', True))
        
        # Appearance
        theme = settings.get('theme', 'light')
        self.theme_combo.setCurrentText(theme.capitalize())
        self.auto_scroll_checkbox.setChecked(settings.get('auto_scroll_logs', True))
        
        # Advanced
        self.max_recent_spinbox.setValue(settings.get('max_recent_files', 10))
    
    def _browse_default_input(self):
        """Browse for default input directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Default Input Directory"
        )
        if directory:
            self.default_input_field.setText(directory)
    
    def _browse_default_output(self):
        """Browse for default output directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Default Output Directory"
        )
        if directory:
            self.default_output_field.setText(directory)

    def _browse_default_json(self):
        """Browse for default JSON config directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Default JSON Config Directory"
        )
        if directory:
            self.default_json_field.setText(directory)

    def _browse_default_dataset(self):
        """Browse for default dataset directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Default Dataset Directory"
        )
        if directory:
            self.default_dataset_field.setText(directory)
    
    def _on_accept(self):
        """Save settings and close dialog."""
        new_settings = {
            'default_input_path': self.default_input_field.text(),
            'default_output_path': self.default_output_field.text(),
            'default_json_path': self.default_json_field.text(),
            'default_dataset_path': self.default_dataset_field.text(),
            'auto_save_preset': self.auto_save_checkbox.isChecked(),
            'confirm_overwrite': self.confirm_overwrite_checkbox.isChecked(),
            'show_tooltips': self.show_tooltips_checkbox.isChecked(),
            'theme': self.theme_combo.currentText().lower(),
            'auto_scroll_logs': self.auto_scroll_checkbox.isChecked(),
            'max_recent_files': self.max_recent_spinbox.value(),
        }
        
        # Check if theme changed
        old_theme = self.settings_manager.get('theme', 'light')
        new_theme = new_settings['theme']
        theme_changed = old_theme != new_theme
        
        self.settings_manager.update_settings(new_settings)
        
        # Notify parent if theme changed
        if theme_changed and self.parent():
            self.parent().apply_theme(new_theme)
        
        self.accept()
    
    def _on_restore_defaults(self):
        """Restore default settings."""
        self.settings_manager.reset_to_defaults()
        self._load_current_settings()
    
    def _on_clear_recent_files(self):
        """Clear recent files history."""
        self.settings_manager.clear_recent_files()
        if self.parent():
            self.parent()._update_recent_files_menu()
