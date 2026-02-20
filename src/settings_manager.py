"""
Settings manager for DXCom GUI application.
Handles application preferences and recent files history.
"""
import json
import os
from typing import List, Dict, Any
from pathlib import Path


class SettingsManager:
    """Manages application settings and recent files history."""
    
    DEFAULT_SETTINGS = {
        'theme': 'light',
        'auto_save_preset': False,
        'default_input_path': '',
        'default_output_path': '',
        'default_json_path': '',
        'default_dataset_path': '',
        'max_recent_files': 10,
        'show_tooltips': True,
        'confirm_overwrite': True,
        'auto_scroll_logs': True,
    }
    
    def __init__(self):
        """Initialize settings manager."""
        self.settings_dir = Path.home() / '.dxcom_gui'
        self.settings_file = self.settings_dir / 'settings.json'
        self.recent_files_file = self.settings_dir / 'recent_files.json'
        
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.recent_files = []
        
        self._ensure_settings_dir()
        self._load_settings()
        self._load_recent_files()
    
    def _ensure_settings_dir(self):
        """Ensure settings directory exists."""
        self.settings_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_settings(self):
        """Load settings from file."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    self.settings.update(loaded)
            except Exception as e:
                print(f"Error loading settings: {e}")
    
    def _save_settings(self):
        """Save settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def _load_recent_files(self):
        """Load recent files from file."""
        if self.recent_files_file.exists():
            try:
                with open(self.recent_files_file, 'r') as f:
                    self.recent_files = json.load(f)
            except Exception as e:
                print(f"Error loading recent files: {e}")
                self.recent_files = []
    
    def _save_recent_files(self):
        """Save recent files to file."""
        try:
            with open(self.recent_files_file, 'w') as f:
                json.dump(self.recent_files, f, indent=2)
        except Exception as e:
            print(f"Error saving recent files: {e}")
    
    def get(self, key: str, default=None) -> Any:
        """Get a setting value."""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a setting value and save."""
        self.settings[key] = value
        self._save_settings()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings."""
        return self.settings.copy()

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings (public alias for get_all)."""
        return self.get_all()

    def save_settings(self):
        """Save settings to file (public alias for _save_settings)."""
        self._save_settings()
    
    def update_settings(self, new_settings: Dict[str, Any]):
        """Update multiple settings at once."""
        self.settings.update(new_settings)
        self._save_settings()
    
    def add_recent_file(self, file_path: str):
        """Add a file to recent files list."""
        if not file_path:
            return
        
        # Remove if already exists
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        
        # Add to front
        self.recent_files.insert(0, file_path)
        
        # Limit list size
        max_recent = self.settings.get('max_recent_files', 10)
        self.recent_files = self.recent_files[:max_recent]
        
        self._save_recent_files()
    
    def get_recent_files(self) -> List[str]:
        """Get list of recent files."""
        return self.recent_files.copy()
    
    def clear_recent_files(self):
        """Clear recent files list."""
        self.recent_files = []
        self._save_recent_files()
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self.settings = self.DEFAULT_SETTINGS.copy()
        self._save_settings()
