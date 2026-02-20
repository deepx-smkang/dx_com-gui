"""
Unit tests for SettingsManager.
"""
import unittest
import tempfile
import shutil
import json
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.settings_manager import SettingsManager


class TestSettingsManager(unittest.TestCase):
    """Test cases for SettingsManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_home = Path.home()
        # Temporarily override settings directory for testing
        self.manager = SettingsManager()
        self.manager.settings_dir = Path(self.test_dir) / '.dxcom_gui'
        self.manager.settings_file = self.manager.settings_dir / 'settings.json'
        self.manager.recent_files_file = self.manager.settings_dir / 'recent_files.json'
        self.manager._ensure_settings_dir()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)
    
    def test_default_settings(self):
        """Test that default settings are loaded correctly."""
        self.assertEqual(self.manager.get('theme'), 'light')
        self.assertEqual(self.manager.get('max_recent_files'), 10)
        self.assertTrue(self.manager.get('show_tooltips'))
    
    def test_set_and_get_setting(self):
        """Test setting and getting a configuration value."""
        self.manager.set('theme', 'dark')
        self.assertEqual(self.manager.get('theme'), 'dark')
        
        self.manager.set('max_recent_files', 5)
        self.assertEqual(self.manager.get('max_recent_files'), 5)
    
    def test_save_and_load_settings(self):
        """Test persistence of settings."""
        self.manager.set('theme', 'dark')
        self.manager.set('auto_save_preset', True)
        self.manager.save_settings()
        
        # Create new manager instance to load settings
        new_manager = SettingsManager()
        new_manager.settings_dir = self.manager.settings_dir
        new_manager.settings_file = self.manager.settings_file
        new_manager.recent_files_file = self.manager.recent_files_file
        new_manager._load_settings()
        
        self.assertEqual(new_manager.get('theme'), 'dark')
        self.assertTrue(new_manager.get('auto_save_preset'))
    
    def test_recent_files_management(self):
        """Test adding and managing recent files."""
        test_files = [
            '/path/to/model1.onnx',
            '/path/to/model2.onnx',
            '/path/to/model3.onnx'
        ]
        
        for file in test_files:
            self.manager.add_recent_file(file)
        
        recent = self.manager.get_recent_files()
        self.assertEqual(len(recent), 3)
        self.assertEqual(recent[0], test_files[2])  # Most recent first
    
    def test_recent_files_duplicate_handling(self):
        """Test that duplicate files are moved to top."""
        self.manager.add_recent_file('/path/to/model1.onnx')
        self.manager.add_recent_file('/path/to/model2.onnx')
        self.manager.add_recent_file('/path/to/model1.onnx')  # Duplicate
        
        recent = self.manager.get_recent_files()
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0], '/path/to/model1.onnx')
    
    def test_recent_files_max_limit(self):
        """Test that recent files respects max limit."""
        self.manager.set('max_recent_files', 5)
        
        for i in range(10):
            self.manager.add_recent_file(f'/path/to/model{i}.onnx')
        
        recent = self.manager.get_recent_files()
        self.assertEqual(len(recent), 5)
    
    def test_clear_recent_files(self):
        """Test clearing recent files history."""
        self.manager.add_recent_file('/path/to/model1.onnx')
        self.manager.add_recent_file('/path/to/model2.onnx')
        
        self.manager.clear_recent_files()
        recent = self.manager.get_recent_files()
        self.assertEqual(len(recent), 0)
    
    def test_get_all_settings(self):
        """Test retrieving all settings at once."""
        self.manager.set('theme', 'dark')
        all_settings = self.manager.get_all_settings()
        
        self.assertIn('theme', all_settings)
        self.assertEqual(all_settings['theme'], 'dark')
        self.assertIn('max_recent_files', all_settings)


if __name__ == '__main__':
    unittest.main()
