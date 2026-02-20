"""
Environment validation module for DXCom compilation.

This module validates that the system environment meets all prerequisites
for successful dxcom compilation, including:
- DXCom compiler installation
- Python version compatibility
- Disk space availability
- File system permissions
- System resources
"""
import sys
import os
import shutil
import subprocess
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationResult:
    """Result of an environment validation check."""
    passed: bool
    message: str
    severity: str = "error"  # "error", "warning", "info"
    details: Optional[str] = None
    
    def __str__(self):
        prefix = "✓" if self.passed else "✗"
        return f"{prefix} {self.message}"


@dataclass
class EnvironmentValidation:
    """Complete environment validation results."""
    overall_valid: bool
    checks: List[ValidationResult] = field(default_factory=list)
    errors: List[ValidationResult] = field(default_factory=list)
    warnings: List[ValidationResult] = field(default_factory=list)
    
    def add_check(self, result: ValidationResult):
        """Add a validation check result."""
        self.checks.append(result)
        if not result.passed:
            if result.severity == "error":
                self.errors.append(result)
                self.overall_valid = False
            elif result.severity == "warning":
                self.warnings.append(result)
    
    def get_summary(self) -> str:
        """Get a human-readable summary of validation results."""
        lines = []
        
        if self.overall_valid:
            lines.append("✓ Environment validation passed")
        else:
            lines.append("✗ Environment validation failed")
        
        if self.errors:
            lines.append(f"\nErrors ({len(self.errors)}):")
            for error in self.errors:
                lines.append(f"  • {error.message}")
                if error.details:
                    lines.append(f"    {error.details}")
        
        if self.warnings:
            lines.append(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                lines.append(f"  • {warning.message}")
                if warning.details:
                    lines.append(f"    {warning.details}")
        
        return "\n".join(lines)
    
    def get_error_messages(self) -> List[str]:
        """Get list of error messages."""
        return [error.message for error in self.errors]
    
    def get_warning_messages(self) -> List[str]:
        """Get list of warning messages."""
        return [warning.message for warning in self.warnings]


class EnvironmentValidator:
    """
    Validates system environment for DXCom compilation.
    
    Performs comprehensive checks to ensure the system is ready
    for compilation including compiler availability, Python version,
    disk space, permissions, and other prerequisites.
    """
    
    # Configuration constants
    MIN_PYTHON_VERSION = (3, 8)
    RECOMMENDED_PYTHON_VERSION = (3, 9)
    MIN_DISK_SPACE_MB = 100  # Minimum free disk space in MB
    RECOMMENDED_DISK_SPACE_MB = 500
    COMPILATION_TEMP_SPACE_MB = 50  # Estimated temp space needed for compilation
    
    def __init__(self):
        """Initialize the environment validator."""
        self._validation_cache: Optional[EnvironmentValidation] = None
    
    def validate(self, force_refresh: bool = False, 
                 output_path: Optional[str] = None) -> EnvironmentValidation:
        """
        Perform complete environment validation.
        
        Args:
            force_refresh: If True, bypass cache and re-validate
            output_path: Optional output path to check for write permissions
            
        Returns:
            EnvironmentValidation object with all check results
        """
        if self._validation_cache and not force_refresh:
            return self._validation_cache
        
        validation = EnvironmentValidation(overall_valid=True)
        
        # Run all validation checks
        validation.add_check(self._check_dxcom_installed())
        validation.add_check(self._check_python_version())
        validation.add_check(self._check_disk_space())
        
        if output_path:
            validation.add_check(self._check_write_permissions(output_path))
        
        validation.add_check(self._check_system_resources())
        validation.add_check(self._check_temp_directory())
        
        self._validation_cache = validation
        return validation
    
    def validate_compilation_ready(self, output_path: str) -> EnvironmentValidation:
        """
        Validate environment is ready for compilation with specific output path.
        
        Args:
            output_path: The output file path for compilation
            
        Returns:
            EnvironmentValidation object
        """
        validation = EnvironmentValidation(overall_valid=True)
        
        # Critical checks for compilation
        validation.add_check(self._check_dxcom_installed())
        validation.add_check(self._check_python_version())
        validation.add_check(self._check_write_permissions(output_path))
        validation.add_check(self._check_disk_space(output_path))
        
        return validation
    
    def _check_dxcom_installed(self) -> ValidationResult:
        """Check if dxcom compiler is installed and accessible."""
        dxcom_path = shutil.which('dxcom')
        
        if not dxcom_path:
            return ValidationResult(
                passed=False,
                message="DXCom compiler not found",
                severity="error",
                details="Please install dxcom and ensure it is in your system PATH"
            )
        
        # Try to verify it's the correct dxcom
        try:
            result = subprocess.run(
                [dxcom_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            output = (result.stdout + result.stderr).lower()
            if 'dxcom' in output or 'deepx' in output or result.returncode == 0:
                return ValidationResult(
                    passed=True,
                    message=f"DXCom compiler found at {dxcom_path}",
                    severity="info"
                )
            else:
                return ValidationResult(
                    passed=False,
                    message="Found 'dxcom' but could not verify it's the DEEPX compiler",
                    severity="error",
                    details=f"Path: {dxcom_path}"
                )
                
        except subprocess.TimeoutExpired:
            return ValidationResult(
                passed=False,
                message="DXCom compiler verification timed out",
                severity="warning",
                details="The compiler exists but did not respond to --version"
            )
        except Exception as e:
            return ValidationResult(
                passed=False,
                message="Could not verify dxcom compiler",
                severity="error",
                details=str(e)
            )
    
    def _check_python_version(self) -> ValidationResult:
        """Check if Python version is compatible."""
        current_version = sys.version_info[:2]
        
        if current_version < self.MIN_PYTHON_VERSION:
            return ValidationResult(
                passed=False,
                message=f"Python version too old: {current_version[0]}.{current_version[1]}",
                severity="error",
                details=f"Minimum required: {self.MIN_PYTHON_VERSION[0]}.{self.MIN_PYTHON_VERSION[1]}"
            )
        
        if current_version < self.RECOMMENDED_PYTHON_VERSION:
            return ValidationResult(
                passed=True,
                message=f"Python {current_version[0]}.{current_version[1]} is supported",
                severity="warning",
                details=f"Python {self.RECOMMENDED_PYTHON_VERSION[0]}.{self.RECOMMENDED_PYTHON_VERSION[1]}+ is recommended"
            )
        
        return ValidationResult(
            passed=True,
            message=f"Python version {current_version[0]}.{current_version[1]} is compatible",
            severity="info"
        )
    
    def _check_disk_space(self, output_path: Optional[str] = None) -> ValidationResult:
        """Check if sufficient disk space is available."""
        try:
            # Determine which path to check
            if output_path:
                # Check the directory where output will be written
                check_path = Path(output_path).parent
                if not check_path.exists():
                    # If parent doesn't exist, go up until we find an existing directory
                    while not check_path.exists() and check_path != check_path.parent:
                        check_path = check_path.parent
            else:
                # Check current working directory
                check_path = Path.cwd()
            
            # Get disk usage statistics
            stat = shutil.disk_usage(check_path)
            free_mb = stat.free / (1024 * 1024)
            
            if free_mb < self.MIN_DISK_SPACE_MB:
                return ValidationResult(
                    passed=False,
                    message=f"Insufficient disk space: {free_mb:.1f} MB free",
                    severity="error",
                    details=f"Minimum {self.MIN_DISK_SPACE_MB} MB required at {check_path}"
                )
            
            if free_mb < self.RECOMMENDED_DISK_SPACE_MB:
                return ValidationResult(
                    passed=True,
                    message=f"Low disk space: {free_mb:.1f} MB free",
                    severity="warning",
                    details=f"Recommended: {self.RECOMMENDED_DISK_SPACE_MB} MB or more"
                )
            
            return ValidationResult(
                passed=True,
                message=f"Sufficient disk space available: {free_mb:.1f} MB",
                severity="info"
            )
            
        except Exception as e:
            return ValidationResult(
                passed=True,  # Don't fail compilation if we can't check
                message="Could not verify disk space",
                severity="warning",
                details=str(e)
            )
    
    def _check_write_permissions(self, output_path: str) -> ValidationResult:
        """Check if we have write permissions for the output path."""
        try:
            output_file = Path(output_path)
            output_dir = output_file.parent
            
            # Check if output file already exists
            if output_file.exists():
                # Check if we can write to existing file
                if not os.access(output_file, os.W_OK):
                    return ValidationResult(
                        passed=False,
                        message="No write permission for output file",
                        severity="error",
                        details=f"Cannot write to: {output_path}"
                    )
            else:
                # Check if output directory exists
                if not output_dir.exists():
                    # Try to create the directory
                    try:
                        output_dir.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        return ValidationResult(
                            passed=False,
                            message="Cannot create output directory",
                            severity="error",
                            details=f"Failed to create: {output_dir}\nError: {str(e)}"
                        )
                
                # Check if we can write to the directory
                if not os.access(output_dir, os.W_OK):
                    return ValidationResult(
                        passed=False,
                        message="No write permission for output directory",
                        severity="error",
                        details=f"Cannot write to: {output_dir}"
                    )
            
            return ValidationResult(
                passed=True,
                message="Write permissions verified for output path",
                severity="info"
            )
            
        except Exception as e:
            return ValidationResult(
                passed=False,
                message="Could not verify write permissions",
                severity="error",
                details=str(e)
            )
    
    def _check_system_resources(self) -> ValidationResult:
        """Check if system has adequate resources (best effort)."""
        try:
            # Try to get memory info (platform dependent)
            if sys.platform.startswith('linux'):
                try:
                    with open('/proc/meminfo', 'r') as f:
                        meminfo = f.read()
                        # Extract available memory
                        for line in meminfo.split('\n'):
                            if line.startswith('MemAvailable:'):
                                mem_kb = int(line.split()[1])
                                mem_mb = mem_kb / 1024
                                
                                if mem_mb < 256:  # Less than 256 MB
                                    return ValidationResult(
                                        passed=True,
                                        message=f"Low system memory: {mem_mb:.0f} MB available",
                                        severity="warning",
                                        details="Compilation may be slow with limited memory"
                                    )
                                
                                return ValidationResult(
                                    passed=True,
                                    message=f"Adequate system memory: {mem_mb:.0f} MB available",
                                    severity="info"
                                )
                except Exception:
                    pass
            
            # If we can't check memory, just pass
            return ValidationResult(
                passed=True,
                message="System resources not verified (platform dependent)",
                severity="info"
            )
            
        except Exception:
            return ValidationResult(
                passed=True,
                message="System resource check skipped",
                severity="info"
            )
    
    def _check_temp_directory(self) -> ValidationResult:
        """Check if temporary directory is accessible."""
        try:
            import tempfile
            
            temp_dir = tempfile.gettempdir()
            
            # Check if temp directory exists and is writable
            if not os.path.exists(temp_dir):
                return ValidationResult(
                    passed=False,
                    message="Temporary directory does not exist",
                    severity="error",
                    details=f"Expected temp dir: {temp_dir}"
                )
            
            if not os.access(temp_dir, os.W_OK):
                return ValidationResult(
                    passed=False,
                    message="Temporary directory is not writable",
                    severity="error",
                    details=f"Cannot write to: {temp_dir}"
                )
            
            # Try to create a temp file to verify
            try:
                with tempfile.NamedTemporaryFile(mode='w', delete=True) as tf:
                    tf.write('test')
                    tf.flush()
            except Exception as e:
                return ValidationResult(
                    passed=False,
                    message="Cannot create temporary files",
                    severity="error",
                    details=str(e)
                )
            
            return ValidationResult(
                passed=True,
                message=f"Temporary directory accessible: {temp_dir}",
                severity="info"
            )
            
        except Exception as e:
            return ValidationResult(
                passed=True,  # Don't fail compilation if we can't check
                message="Temporary directory check skipped",
                severity="warning",
                details=str(e)
            )
    
    def clear_cache(self):
        """Clear cached validation results."""
        self._validation_cache = None
    
    def quick_check(self) -> Tuple[bool, str]:
        """
        Perform a quick environment check.
        
        Returns:
            Tuple of (is_valid, message)
        """
        # Just check the most critical items
        dxcom_check = self._check_dxcom_installed()
        if not dxcom_check.passed:
            return False, dxcom_check.message
        
        python_check = self._check_python_version()
        if not python_check.passed:
            return False, python_check.message
        
        return True, "Environment ready for compilation"


# Global validator instance
_validator = EnvironmentValidator()


def validate_environment(force_refresh: bool = False) -> EnvironmentValidation:
    """
    Convenience function to validate environment.
    
    Args:
        force_refresh: If True, bypass cache and re-validate
        
    Returns:
        EnvironmentValidation object
    """
    return _validator.validate(force_refresh=force_refresh)


def validate_for_compilation(output_path: str) -> EnvironmentValidation:
    """
    Convenience function to validate environment for compilation.
    
    Args:
        output_path: The output file path for compilation
        
    Returns:
        EnvironmentValidation object
    """
    return _validator.validate_compilation_ready(output_path)


def quick_environment_check() -> Tuple[bool, str]:
    """
    Quick environment check for critical prerequisites.
    
    Returns:
        Tuple of (is_valid, message)
    """
    return _validator.quick_check()


def clear_validation_cache():
    """Clear cached validation results."""
    _validator.clear_cache()
