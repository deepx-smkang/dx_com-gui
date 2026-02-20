"""
DXCom availability and version detection utility.

This module provides functionality to detect if dxcom is installed,
verify it's the correct tool, and retrieve version information.
"""
import subprocess
import shutil
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class DXComInfo:
    """Information about installed dxcom."""
    available: bool
    path: Optional[str] = None
    version: Optional[str] = None
    error_message: Optional[str] = None
    
    def is_valid(self) -> bool:
        """Check if dxcom is available and valid."""
        return self.available and self.path is not None


class DXComDetector:
    """
    Detector for dxcom compiler availability and version.
    
    This class checks if dxcom is installed on the system, validates
    it's the correct tool, and retrieves version information.
    """
    
    def __init__(self):
        """Initialize the detector."""
        self._cached_info: Optional[DXComInfo] = None
    
    def detect(self, force_refresh: bool = False) -> DXComInfo:
        """
        Detect dxcom availability and version.
        
        Args:
            force_refresh: If True, bypass cache and re-detect
            
        Returns:
            DXComInfo object with detection results
        """
        if self._cached_info and not force_refresh:
            return self._cached_info
        
        # Check if dxcom command exists
        dxcom_path = shutil.which('dxcom')
        
        if not dxcom_path:
            self._cached_info = DXComInfo(
                available=False,
                error_message="dxcom command not found in PATH. Please install dxcom compiler."
            )
            return self._cached_info
        
        # Try to get version and validate it's the right tool
        version = self._get_version(dxcom_path)
        
        if version is None:
            self._cached_info = DXComInfo(
                available=False,
                path=dxcom_path,
                error_message="Found 'dxcom' command but could not verify it's the DEEPX compiler."
            )
            return self._cached_info
        
        # Success - dxcom is available and valid
        self._cached_info = DXComInfo(
            available=True,
            path=dxcom_path,
            version=version
        )
        return self._cached_info
    
    def _get_version(self, dxcom_path: str) -> Optional[str]:
        """
        Get dxcom version by running it.
        
        Args:
            dxcom_path: Full path to dxcom executable
            
        Returns:
            Version string or None if unable to determine
        """
        # Try common version flags
        version_flags = ['--version', '-v', '--help', '-h']
        
        for flag in version_flags:
            try:
                result = subprocess.run(
                    [dxcom_path, flag],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                # Check if output contains version or dxcom identifiers
                output = result.stdout + result.stderr
                output_lower = output.lower()
                
                # Look for version patterns
                if any(keyword in output_lower for keyword in ['dxcom', 'deepx', 'version']):
                    # Try to extract version number
                    version = self._extract_version(output)
                    if version:
                        return version
                    # If no version found but validated as dxcom, return flag used
                    return f"installed (detected via {flag})"
                    
            except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
                continue
        
        # Could not determine version
        return None
    
    def _extract_version(self, output: str) -> Optional[str]:
        """
        Extract version string from command output.
        
        Args:
            output: Command output text
            
        Returns:
            Version string or None
        """
        import re
        
        # Common version patterns
        patterns = [
            r'version\s+(\d+\.\d+\.\d+)',
            r'v(\d+\.\d+\.\d+)',
            r'dxcom\s+(\d+\.\d+\.\d+)',
            r'(\d+\.\d+\.\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def get_user_friendly_status(self) -> Tuple[str, str]:
        """
        Get user-friendly status message for display.
        
        Returns:
            Tuple of (status_type, message) where status_type is
            'success', 'warning', or 'error'
        """
        info = self.detect()
        
        if info.is_valid():
            if info.version:
                return ('success', f'dxcom detected: {info.version} at {info.path}')
            else:
                return ('success', f'dxcom detected at {info.path}')
        else:
            return ('error', info.error_message or 'dxcom not available')
    
    def clear_cache(self):
        """Clear cached detection results."""
        self._cached_info = None


# Global detector instance
_detector = DXComDetector()


def check_dxcom_available() -> DXComInfo:
    """
    Convenience function to check dxcom availability.
    
    Returns:
        DXComInfo object with detection results
    """
    return _detector.detect()


def get_dxcom_status() -> Tuple[str, str]:
    """
    Convenience function to get user-friendly status.
    
    Returns:
        Tuple of (status_type, message)
    """
    return _detector.get_user_friendly_status()


def refresh_dxcom_detection():
    """Force refresh of dxcom detection."""
    _detector.detect(force_refresh=True)
