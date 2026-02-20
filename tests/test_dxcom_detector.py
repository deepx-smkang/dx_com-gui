"""
Unit tests for dxcom_detector module.
"""
import unittest
from unittest.mock import patch, MagicMock
import subprocess
from src.dxcom_detector import (
    DXComDetector, DXComInfo, 
    check_dxcom_available, get_dxcom_status
)


class TestDXComDetector(unittest.TestCase):
    """Test cases for DXComDetector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector = DXComDetector()
        self.detector.clear_cache()  # Clear any cached results
    
    def test_dxcom_not_found(self):
        """Test when dxcom is not in PATH."""
        with patch('shutil.which', return_value=None):
            info = self.detector.detect()
            
            self.assertFalse(info.available)
            self.assertIsNone(info.path)
            self.assertIsNone(info.version)
            self.assertIn("not found", info.error_message.lower())
            self.assertFalse(info.is_valid())
    
    def test_dxcom_found_with_version(self):
        """Test when dxcom is found and returns version."""
        mock_result = MagicMock()
        mock_result.stdout = "dxcom version 1.2.3"
        mock_result.stderr = ""
        
        with patch('shutil.which', return_value='/usr/bin/dxcom'):
            with patch('subprocess.run', return_value=mock_result):
                info = self.detector.detect()
                
                self.assertTrue(info.available)
                self.assertEqual(info.path, '/usr/bin/dxcom')
                self.assertEqual(info.version, '1.2.3')
                self.assertIsNone(info.error_message)
                self.assertTrue(info.is_valid())
    
    def test_dxcom_found_no_version(self):
        """Test when dxcom is found but version cannot be determined."""
        mock_result = MagicMock()
        mock_result.stdout = "dxcom compiler tool"
        mock_result.stderr = ""
        
        with patch('shutil.which', return_value='/usr/bin/dxcom'):
            with patch('subprocess.run', return_value=mock_result):
                info = self.detector.detect()
                
                self.assertTrue(info.available)
                self.assertEqual(info.path, '/usr/bin/dxcom')
                self.assertIn("--version", info.version)  # Should indicate detection method
                self.assertIsNone(info.error_message)
                self.assertTrue(info.is_valid())
    
    def test_dxcom_found_but_wrong_tool(self):
        """Test when a command named dxcom exists but is not the DEEPX compiler."""
        mock_result = MagicMock()
        mock_result.stdout = "completely unrelated output"
        mock_result.stderr = ""
        
        with patch('shutil.which', return_value='/usr/bin/dxcom'):
            with patch('subprocess.run', return_value=mock_result):
                info = self.detector.detect()
                
                self.assertFalse(info.available)
                self.assertEqual(info.path, '/usr/bin/dxcom')
                self.assertIsNone(info.version)
                self.assertIn("could not verify", info.error_message.lower())
                self.assertFalse(info.is_valid())
    
    def test_version_extraction_patterns(self):
        """Test various version string patterns."""
        test_cases = [
            ("version 1.2.3", "1.2.3"),
            ("dxcom v2.0.1", "2.0.1"),
            ("dxcom 3.4.5 compiler", "3.4.5"),
            ("Version: 1.0.0", "1.0.0"),
        ]
        
        for output, expected_version in test_cases:
            version = self.detector._extract_version(output)
            self.assertEqual(version, expected_version, 
                           f"Failed to extract version from: {output}")
    
    def test_caching(self):
        """Test that detection results are cached."""
        with patch('shutil.which', return_value='/usr/bin/dxcom') as mock_which:
            mock_result = MagicMock()
            mock_result.stdout = "dxcom version 1.0.0"
            mock_result.stderr = ""
            
            with patch('subprocess.run', return_value=mock_result) as mock_run:
                # First call should execute detection
                info1 = self.detector.detect()
                self.assertEqual(mock_which.call_count, 1)
                self.assertTrue(mock_run.called)
                
                # Second call should use cache
                info2 = self.detector.detect()
                self.assertEqual(mock_which.call_count, 1)  # Should not increase
                
                # Results should be the same object
                self.assertIs(info1, info2)
    
    def test_force_refresh(self):
        """Test that force_refresh bypasses cache."""
        with patch('shutil.which', return_value='/usr/bin/dxcom') as mock_which:
            mock_result = MagicMock()
            mock_result.stdout = "dxcom version 1.0.0"
            mock_result.stderr = ""
            
            with patch('subprocess.run', return_value=mock_result):
                # First call
                self.detector.detect()
                self.assertEqual(mock_which.call_count, 1)
                
                # Force refresh should re-detect
                self.detector.detect(force_refresh=True)
                self.assertEqual(mock_which.call_count, 2)
    
    def test_subprocess_timeout(self):
        """Test handling of subprocess timeout."""
        with patch('shutil.which', return_value='/usr/bin/dxcom'):
            with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('dxcom', 5)):
                info = self.detector.detect()
                
                # Should fail gracefully
                self.assertFalse(info.available)
                self.assertIsNone(info.version)
    
    def test_get_user_friendly_status_success(self):
        """Test user-friendly status message for successful detection."""
        mock_result = MagicMock()
        mock_result.stdout = "dxcom version 1.2.3"
        mock_result.stderr = ""
        
        with patch('shutil.which', return_value='/usr/bin/dxcom'):
            with patch('subprocess.run', return_value=mock_result):
                status_type, message = self.detector.get_user_friendly_status()
                
                self.assertEqual(status_type, 'success')
                self.assertIn('detected', message.lower())
                self.assertIn('1.2.3', message)
    
    def test_get_user_friendly_status_error(self):
        """Test user-friendly status message for detection failure."""
        with patch('shutil.which', return_value=None):
            status_type, message = self.detector.get_user_friendly_status()
            
            self.assertEqual(status_type, 'error')
            self.assertIn('not', message.lower())


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    def test_check_dxcom_available(self):
        """Test check_dxcom_available function."""
        with patch('shutil.which', return_value='/usr/bin/dxcom'):
            mock_result = MagicMock()
            mock_result.stdout = "dxcom version 1.0.0"
            mock_result.stderr = ""
            
            with patch('subprocess.run', return_value=mock_result):
                info = check_dxcom_available()
                self.assertIsInstance(info, DXComInfo)
                self.assertTrue(info.is_valid())
    
    def test_get_dxcom_status(self):
        """Test get_dxcom_status function."""
        with patch('shutil.which', return_value='/usr/bin/dxcom'):
            mock_result = MagicMock()
            mock_result.stdout = "dxcom version 1.0.0"
            mock_result.stderr = ""
            
            with patch('subprocess.run', return_value=mock_result):
                status_type, message = get_dxcom_status()
                self.assertIsInstance(status_type, str)
                self.assertIsInstance(message, str)
                self.assertEqual(status_type, 'success')


if __name__ == '__main__':
    unittest.main()
