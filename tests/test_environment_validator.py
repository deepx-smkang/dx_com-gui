"""
Tests for environment validation module.
"""
import sys
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.environment_validator import (
    EnvironmentValidator,
    ValidationResult,
    EnvironmentValidation,
    validate_environment,
    validate_for_compilation,
    quick_environment_check
)


class TestValidationResult:
    """Tests for ValidationResult dataclass."""
    
    def test_validation_result_creation(self):
        """Test creating a ValidationResult."""
        result = ValidationResult(
            passed=True,
            message="Test passed",
            severity="info"
        )
        
        assert result.passed is True
        assert result.message == "Test passed"
        assert result.severity == "info"
        assert result.details is None
    
    def test_validation_result_str(self):
        """Test string representation."""
        passed = ValidationResult(passed=True, message="Test passed")
        failed = ValidationResult(passed=False, message="Test failed")
        
        assert str(passed).startswith("✓")
        assert str(failed).startswith("✗")


class TestEnvironmentValidation:
    """Tests for EnvironmentValidation dataclass."""
    
    def test_empty_validation(self):
        """Test creating empty validation."""
        validation = EnvironmentValidation(overall_valid=True)
        
        assert validation.overall_valid is True
        assert len(validation.checks) == 0
        assert len(validation.errors) == 0
        assert len(validation.warnings) == 0
    
    def test_add_passed_check(self):
        """Test adding a passed check."""
        validation = EnvironmentValidation(overall_valid=True)
        
        check = ValidationResult(passed=True, message="Test", severity="info")
        validation.add_check(check)
        
        assert len(validation.checks) == 1
        assert len(validation.errors) == 0
        assert len(validation.warnings) == 0
        assert validation.overall_valid is True
    
    def test_add_error_check(self):
        """Test adding a failed check with error severity."""
        validation = EnvironmentValidation(overall_valid=True)
        
        check = ValidationResult(passed=False, message="Error", severity="error")
        validation.add_check(check)
        
        assert len(validation.checks) == 1
        assert len(validation.errors) == 1
        assert validation.overall_valid is False
    
    def test_add_warning_check(self):
        """Test adding a failed check with warning severity."""
        validation = EnvironmentValidation(overall_valid=True)
        
        check = ValidationResult(passed=False, message="Warning", severity="warning")
        validation.add_check(check)
        
        assert len(validation.checks) == 1
        assert len(validation.warnings) == 1
        assert validation.overall_valid is True  # Warnings don't fail overall
    
    def test_get_summary(self):
        """Test getting summary text."""
        validation = EnvironmentValidation(overall_valid=True)
        
        validation.add_check(ValidationResult(passed=True, message="Check 1", severity="info"))
        validation.add_check(ValidationResult(passed=False, message="Warning 1", severity="warning"))
        
        summary = validation.get_summary()
        
        assert "passed" in summary.lower()
        assert "Warning 1" in summary
    
    def test_get_error_messages(self):
        """Test getting error messages."""
        validation = EnvironmentValidation(overall_valid=True)
        
        validation.add_check(ValidationResult(passed=False, message="Error 1", severity="error"))
        validation.add_check(ValidationResult(passed=False, message="Error 2", severity="error"))
        
        errors = validation.get_error_messages()
        assert len(errors) == 2
        assert "Error 1" in errors
        assert "Error 2" in errors
    
    def test_get_summary_when_failed(self):
        """get_summary() with a failing validation (line 59: ✗ branch)."""
        validation = EnvironmentValidation(overall_valid=True)
        validation.add_check(ValidationResult(
            passed=False, message="Compiler missing", severity="error"))
        summary = validation.get_summary()
        assert "failed" in summary.lower() or "✗" in summary

    def test_get_summary_with_error_details(self):
        """get_summary() includes error details when present (lines 62-66)."""
        validation = EnvironmentValidation(overall_valid=True)
        validation.add_check(ValidationResult(
            passed=False, message="Disk full",
            severity="error", details="Free: 0 MB"))
        summary = validation.get_summary()
        assert "Disk full" in summary
        assert "Free: 0 MB" in summary

    def test_get_summary_with_warning_details(self):
        """get_summary() includes warning details when present (line 73)."""
        validation = EnvironmentValidation(overall_valid=True)
        validation.add_check(ValidationResult(
            passed=False, message="Low memory",
            severity="warning", details="512 MB available"))
        summary = validation.get_summary()
        assert "Low memory" in summary
        assert "512 MB available" in summary

    def test_get_warning_messages(self):
        """Test getting warning messages."""
        validation = EnvironmentValidation(overall_valid=True)
        
        validation.add_check(ValidationResult(passed=False, message="Warning 1", severity="warning"))
        
        warnings = validation.get_warning_messages()
        assert len(warnings) == 1
        assert "Warning 1" in warnings


class TestEnvironmentValidator:
    """Tests for EnvironmentValidator class."""
    
    def test_validator_creation(self):
        """Test creating a validator."""
        validator = EnvironmentValidator()
        assert validator is not None
    
    def test_check_python_version(self):
        """Test Python version check."""
        validator = EnvironmentValidator()
        result = validator._check_python_version()
        
        # Should always pass on current Python (we're running the test!)
        assert result.passed is True
        assert "python" in result.message.lower()
    
    def test_check_disk_space(self):
        """Test disk space check."""
        validator = EnvironmentValidator()
        result = validator._check_disk_space()
        
        # Should check current directory
        assert result.message is not None
        assert "disk space" in result.message.lower()
    
    def test_check_disk_space_with_path(self):
        """Test disk space check with specific path."""
        validator = EnvironmentValidator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_output.dxnn")
            result = validator._check_disk_space(test_file)
            
            assert result.message is not None
            assert "disk space" in result.message.lower()
    
    def test_check_write_permissions_temp_dir(self):
        """Test write permissions check with writable temp directory."""
        validator = EnvironmentValidator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_output.dxnn")
            result = validator._check_write_permissions(test_file)
            
            assert result.passed is True
            assert "write" in result.message.lower()
    
    def test_check_write_permissions_creates_directory(self):
        """Test that write permission check creates missing directories."""
        validator = EnvironmentValidator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "subdir", "nested", "test.dxnn")
            result = validator._check_write_permissions(nested_path)
            
            # Should pass and create the directory structure
            assert result.passed is True
            assert os.path.exists(os.path.dirname(nested_path))
    
    def test_check_write_permissions_existing_file(self):
        """Test write permissions check with existing file."""
        validator = EnvironmentValidator()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dxnn', delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write("test")
        
        try:
            result = validator._check_write_permissions(tmp_path)
            assert result.passed is True
        finally:
            os.unlink(tmp_path)
    
    def test_check_temp_directory(self):
        """Test temporary directory check."""
        validator = EnvironmentValidator()
        result = validator._check_temp_directory()
        
        # Temp directory should be accessible
        assert result.passed is True
        assert "temp" in result.message.lower()
    
    def test_check_system_resources(self):
        """Test system resources check."""
        validator = EnvironmentValidator()
        result = validator._check_system_resources()
        
        # Should always pass (best effort check)
        assert result.passed is True
    
    def test_validate_full(self):
        """Test full validation."""
        validator = EnvironmentValidator()
        validation = validator.validate()
        
        assert isinstance(validation, EnvironmentValidation)
        assert len(validation.checks) > 0
    
    def test_validate_with_output_path(self):
        """Test validation with output path."""
        validator = EnvironmentValidator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.dxnn")
            validation = validator.validate(output_path=output_path)
            
            assert isinstance(validation, EnvironmentValidation)
            # Should include write permission check
            assert any("write" in check.message.lower() for check in validation.checks)
    
    def test_validate_compilation_ready(self):
        """Test compilation readiness validation."""
        validator = EnvironmentValidator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.dxnn")
            validation = validator.validate_compilation_ready(output_path)
            
            assert isinstance(validation, EnvironmentValidation)
            # Should include critical checks
            check_messages = [check.message.lower() for check in validation.checks]
            assert any("dxcom" in msg or "compiler" in msg for msg in check_messages)
            assert any("python" in msg for msg in check_messages)
            assert any("write" in msg for msg in check_messages)
    
    def test_quick_check(self):
        """Test quick environment check."""
        validator = EnvironmentValidator()
        is_valid, message = validator.quick_check()
        
        assert isinstance(is_valid, bool)
        assert isinstance(message, str)
        assert len(message) > 0
    
    def test_cache_functionality(self):
        """Test that validation results are cached."""
        validator = EnvironmentValidator()
        
        # First validation
        validation1 = validator.validate()
        
        # Second validation (should be cached)
        validation2 = validator.validate()
        
        # Should be the same object
        assert validation1 is validation2
        
        # Force refresh should create new object
        validation3 = validator.validate(force_refresh=True)
        assert validation1 is not validation3
    
    def test_clear_cache(self):
        """Test clearing validation cache."""
        validator = EnvironmentValidator()
        
        # Run validation to populate cache
        validation1 = validator.validate()
        
        # Clear cache
        validator.clear_cache()
        
        # Next validation should be new
        validation2 = validator.validate()
        assert validation1 is not validation2


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""
    
    def test_validate_environment(self):
        """Test validate_environment convenience function."""
        validation = validate_environment()
        
        assert isinstance(validation, EnvironmentValidation)
        assert len(validation.checks) > 0
    
    def test_validate_for_compilation(self):
        """Test validate_for_compilation convenience function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.dxnn")
            validation = validate_for_compilation(output_path)
            
            assert isinstance(validation, EnvironmentValidation)
    
    def test_quick_environment_check(self):
        """Test quick_environment_check convenience function."""
        is_valid, message = quick_environment_check()
        
        assert isinstance(is_valid, bool)
        assert isinstance(message, str)


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_write_permissions_nonexistent_parent(self):
        """Test write permissions with deeply nested nonexistent path."""
        validator = EnvironmentValidator()
        
        # Use a path that definitely doesn't exist
        nonexistent = "/this/path/definitely/does/not/exist/output.dxnn"
        
        # Should handle gracefully (may pass or fail depending on permissions)
        result = validator._check_write_permissions(nonexistent)
        assert result is not None
        assert isinstance(result, ValidationResult)
    
    def test_disk_space_invalid_path(self):
        """Test disk space check with invalid path."""
        validator = EnvironmentValidator()
        
        # Should handle gracefully
        result = validator._check_disk_space("/definitely/nonexistent/path/file.dxnn")
        assert result is not None
    
    def test_validation_with_mixed_results(self):
        """Test validation with mix of passed, failed, and warning checks."""
        validation = EnvironmentValidation(overall_valid=True)
        
        validation.add_check(ValidationResult(passed=True, message="Pass", severity="info"))
        validation.add_check(ValidationResult(passed=False, message="Warn", severity="warning"))
        validation.add_check(ValidationResult(passed=False, message="Error", severity="error"))
        
        assert validation.overall_valid is False
        assert len(validation.checks) == 3
        assert len(validation.errors) == 1
        assert len(validation.warnings) == 1


def test_module_integration():
    """Test that module can be imported and used."""
    # Verify all public APIs are accessible
    from src.environment_validator import (
        EnvironmentValidator,
        ValidationResult,
        EnvironmentValidation,
        validate_environment,
        validate_for_compilation,
        quick_environment_check,
        clear_validation_cache
    )
    
    # Run a full integration test
    validation = validate_environment()
    assert validation is not None
    
    is_valid, message = quick_environment_check()
    assert message is not None
    
    # Clear cache
    clear_validation_cache()


# ---------------------------------------------------------------------------
# Additional edge-case tests to improve branch coverage
# ---------------------------------------------------------------------------


class TestDXComInstalledBranches:
    """Coverage for _check_dxcom_installed() when dxcom is found."""

    def test_dxcom_not_found(self):
        """shutil.which returns None → 'not found' result (line 162)."""
        validator = EnvironmentValidator()
        with patch('src.environment_validator.shutil.which', return_value=None):
            result = validator._check_dxcom_installed()
        assert result.passed is False
        assert 'not found' in result.message.lower()

    def test_dxcom_found_verified_deepx_output(self):
        """dxcom found and --version returns 'deepx' in output → passes."""
        validator = EnvironmentValidator()
        fake_result = type('R', (), {'stdout': 'deepx 1.0', 'stderr': '', 'returncode': 0})()
        with patch('src.environment_validator.shutil.which', return_value='/usr/bin/dxcom'), \
             patch('subprocess.run', return_value=fake_result):
            result = validator._check_dxcom_installed()
        assert result.passed is True
        assert 'found' in result.message.lower()

    def test_dxcom_found_returncode_zero(self):
        """dxcom found and --version exits 0 (even without keyword) → passes."""
        validator = EnvironmentValidator()
        fake_result = type('R', (), {'stdout': 'something', 'stderr': '', 'returncode': 0})()
        with patch('src.environment_validator.shutil.which', return_value='/usr/bin/dxcom'), \
             patch('subprocess.run', return_value=fake_result):
            result = validator._check_dxcom_installed()
        assert result.passed is True

    def test_dxcom_found_but_unrecognised(self):
        """dxcom found but output doesn't contain dxcom/deepx and exits non-zero."""
        validator = EnvironmentValidator()
        fake_result = type('R', (), {'stdout': 'other tool 2.0', 'stderr': '', 'returncode': 1})()
        with patch('src.environment_validator.shutil.which', return_value='/usr/bin/dxcom'), \
             patch('subprocess.run', return_value=fake_result):
            result = validator._check_dxcom_installed()
        assert result.passed is False
        assert 'verify' in result.message.lower() or 'could not' in result.message.lower()

    def test_dxcom_found_timeout(self):
        """dxcom found but --version times out."""
        validator = EnvironmentValidator()
        with patch('src.environment_validator.shutil.which', return_value='/usr/bin/dxcom'), \
             patch('subprocess.run', side_effect=subprocess.TimeoutExpired(
                 cmd='dxcom', timeout=5)):
            result = validator._check_dxcom_installed()
        assert result.passed is False
        assert 'timed out' in result.message.lower() or 'timeout' in result.message.lower()

    def test_dxcom_found_exception(self):
        """dxcom found but subprocess raises generic exception."""
        validator = EnvironmentValidator()
        with patch('src.environment_validator.shutil.which', return_value='/usr/bin/dxcom'), \
             patch('subprocess.run', side_effect=OSError('permission denied')):
            result = validator._check_dxcom_installed()
        assert result.passed is False


class TestPythonVersionTooOld:
    """Coverage for _check_python_version() when Python is too old or just-supported."""

    def test_python_version_too_old(self):
        """MIN_PYTHON_VERSION set higher than current → fails."""
        validator = EnvironmentValidator()
        validator.MIN_PYTHON_VERSION = (4, 0)  # future version
        result = validator._check_python_version()
        assert result.passed is False
        assert 'too old' in result.message.lower()

    def test_python_version_needs_upgrade_warning(self):
        """MIN <= current < RECOMMENDED → passes with warning (line 221)."""
        validator = EnvironmentValidator()
        import sys
        current = sys.version_info[:2]
        # Set MIN = current, RECOMMENDED = current + 1 major
        validator.MIN_PYTHON_VERSION = current
        validator.RECOMMENDED_PYTHON_VERSION = (current[0], current[1] + 1)
        result = validator._check_python_version()
        assert result.passed is True
        assert result.severity == 'warning'


class TestDiskSpaceWithOutputPath:
    """Coverage for _check_disk_space() with non-existent parent path and disk conditions."""

    def test_disk_space_traverses_to_existing_parent(self):
        """disk_space check with deeply nested non-existent output path."""
        validator = EnvironmentValidator()
        # Use a path whose parent doesn't exist; the function traverses up
        nested = '/nonexistent_root_xyz/a/b/c/output.dxnn'
        result = validator._check_disk_space(nested)
        # Should handle gracefully (ultimately reach / which exists)
        assert result is not None
        assert isinstance(result, ValidationResult)

    def test_disk_space_insufficient(self):
        """When free space < MIN_DISK_SPACE_MB → fails (line 254)."""
        from unittest.mock import MagicMock
        validator = EnvironmentValidator()
        validator.MIN_DISK_SPACE_MB = 1000  # require 1 GB
        fake_stat = MagicMock()
        fake_stat.free = 50 * 1024 * 1024  # 50 MB available
        with patch('shutil.disk_usage', return_value=fake_stat):
            result = validator._check_disk_space()
        assert result.passed is False
        assert 'insufficient' in result.message.lower()

    def test_disk_space_low_warning(self):
        """When MIN <= free < RECOMMENDED → warning (line 262)."""
        from unittest.mock import MagicMock
        validator = EnvironmentValidator()
        validator.MIN_DISK_SPACE_MB = 50
        validator.RECOMMENDED_DISK_SPACE_MB = 500
        fake_stat = MagicMock()
        fake_stat.free = 100 * 1024 * 1024  # 100 MB
        with patch('shutil.disk_usage', return_value=fake_stat):
            result = validator._check_disk_space()
        assert result.passed is True
        assert result.severity == 'warning'
        assert 'low' in result.message.lower()

    def test_disk_space_exception_returns_warning(self):
        """Exception from shutil.disk_usage → warning (lines 275-276)."""
        validator = EnvironmentValidator()
        with patch('shutil.disk_usage', side_effect=OSError('no such device')):
            result = validator._check_disk_space()
        assert result.passed is True
        assert result.severity == 'warning'


class TestWritePermissionsEdgeCases:
    """Coverage for _check_write_permissions() edge cases."""

    def test_existing_writable_file(self, tmp_path):
        """Output file already exists and is writable (covers line 213 branch)."""
        validator = EnvironmentValidator()
        # Create an actual file so output_file.exists() is True
        existing = tmp_path / 'model.dxnn'
        existing.write_text('content')
        result = validator._check_write_permissions(str(existing))
        assert result.passed is True

    def test_existing_non_writable_file(self, tmp_path):
        """Output file exists but has no write permission (line 293-297 branch)."""
        import stat as stat_module
        validator = EnvironmentValidator()
        existing = tmp_path / 'readonly.dxnn'
        existing.write_text('content')
        # Remove write permission
        existing.chmod(stat_module.S_IRUSR | stat_module.S_IRGRP)
        try:
            result = validator._check_write_permissions(str(existing))
            assert result.passed is False
            assert 'write' in result.message.lower() or 'permission' in result.message.lower()
        finally:
            # Restore permission so cleanup works
            existing.chmod(stat_module.S_IRUSR | stat_module.S_IWUSR)

    def test_no_write_permission_for_output_directory(self, tmp_path):
        """Directory exists but has no write permission (line 315)."""
        import stat as stat_module
        validator = EnvironmentValidator()
        readonly_dir = tmp_path / 'readonly'
        readonly_dir.mkdir()
        readonly_dir.chmod(stat_module.S_IRUSR | stat_module.S_IXUSR)
        try:
            result = validator._check_write_permissions(
                str(readonly_dir / 'output.dxnn'))
            assert result.passed is False
        finally:
            readonly_dir.chmod(stat_module.S_IRUSR | stat_module.S_IWUSR | stat_module.S_IXUSR)

    def test_directory_creation_fails(self, tmp_path, monkeypatch):
        """Directory creation raises OSError (covers lines 304 branch)."""
        validator = EnvironmentValidator()
        nested = str(tmp_path / 'newdir' / 'output.dxnn')

        from pathlib import Path as RealPath

        original_mkdir = RealPath.mkdir

        def fail_mkdir(self, *args, **kwargs):
            raise OSError('no space left on device')

        monkeypatch.setattr(RealPath, 'mkdir', fail_mkdir)
        result = validator._check_write_permissions(nested)
        assert result.passed is False
        assert 'directory' in result.message.lower()

    def test_write_permissions_general_exception(self):
        """Exception in Path() raises → outer except (lines 328-329)."""
        validator = EnvironmentValidator()
        with patch('src.environment_validator.Path', side_effect=TypeError('bad path')):
            result = validator._check_write_permissions('/some/path.dxnn')
        assert result.passed is False
        assert 'permissions' in result.message.lower() or 'verify' in result.message.lower()


class TestSystemResourcesBranches:
    """Coverage for _check_system_resources() memory branches."""

    def _make_meminfo_mock(self, mem_kb):
        """Create a mock open that returns fake /proc/meminfo content."""
        import builtins
        from io import StringIO
        content = f"MemTotal:        8192000 kB\nMemAvailable:    {mem_kb} kB\n"

        real_open = builtins.open

        def mock_open(path, *args, **kwargs):
            if path == '/proc/meminfo':
                return StringIO(content)
            return real_open(path, *args, **kwargs)

        return mock_open

    def test_linux_low_memory(self, monkeypatch):
        """On Linux, when available memory < 256 MB → warning (line 354-360)."""
        import sys as _sys
        monkeypatch.setattr(_sys, 'platform', 'linux')

        fake_open = self._make_meminfo_mock(131072)  # 128 MB in kB
        with patch('builtins.open', side_effect=fake_open):
            validator = EnvironmentValidator()
            result = validator._check_system_resources()
        assert result.passed is True
        assert 'low' in result.message.lower() or 'memory' in result.message.lower()

    def test_linux_adequate_memory(self, monkeypatch):
        """On Linux, when available memory > 256 MB → passes (lines 373-374)."""
        import sys as _sys
        monkeypatch.setattr(_sys, 'platform', 'linux')

        fake_open = self._make_meminfo_mock(2097152)  # 2 GB in kB
        with patch('builtins.open', side_effect=fake_open):
            validator = EnvironmentValidator()
            result = validator._check_system_resources()
        assert result.passed is True
        assert 'adequate' in result.message.lower() or 'memory' in result.message.lower()

    def test_non_linux_platform(self, monkeypatch):
        """On non-Linux, returns generic 'not verified' result (line 389)."""
        import sys as _sys
        monkeypatch.setattr(_sys, 'platform', 'win32')
        validator = EnvironmentValidator()
        result = validator._check_system_resources()
        assert result.passed is True

    def test_linux_meminfo_parse_error(self, monkeypatch):
        """When /proc/meminfo read fails with exception → falls through (line 397 path)."""
        import sys as _sys, builtins
        monkeypatch.setattr(_sys, 'platform', 'linux')

        real_open = builtins.open

        def mock_open(path, *args, **kwargs):
            if path == '/proc/meminfo':
                raise IOError('permission denied')
            return real_open(path, *args, **kwargs)

        with patch('builtins.open', side_effect=mock_open):
            validator = EnvironmentValidator()
            result = validator._check_system_resources()
        assert result.passed is True

    def test_system_resources_outer_exception(self, monkeypatch):
        """Outer exception in _check_system_resources → skipped result (lines 373-374)."""
        import sys as _sys
        # Setting platform to None makes sys.platform.startswith() raise AttributeError
        # which is caught by the outer except Exception block
        monkeypatch.setattr(_sys, 'platform', None)
        validator = EnvironmentValidator()
        result = validator._check_system_resources()
        assert result.passed is True
        assert 'skipped' in result.message.lower()


class TestTempDirectoryEdgeCases:
    """Coverage for _check_temp_directory() when NamedTemporaryFile fails."""

    def test_temp_file_creation_fails(self):
        """When NamedTemporaryFile raises, returns 'Cannot create temporary files'."""
        validator = EnvironmentValidator()
        with patch('tempfile.NamedTemporaryFile', side_effect=OSError('disk full')):
            result = validator._check_temp_directory()
        assert result.passed is False
        assert 'temporary' in result.message.lower()

    def test_temp_dir_does_not_exist(self):
        """When temp directory does not exist → error result (line 389)."""
        validator = EnvironmentValidator()
        with patch('tempfile.gettempdir', return_value='/nonexistent_temp_xyz_12345'), \
             patch('os.path.exists', return_value=False):
            result = validator._check_temp_directory()
        assert result.passed is False
        assert 'exist' in result.message.lower()

    def test_temp_dir_not_writable(self, tmp_path):
        """When temp directory is not writable → error result (line 397)."""
        validator = EnvironmentValidator()
        with patch('tempfile.gettempdir', return_value=str(tmp_path)), \
             patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=False):
            result = validator._check_temp_directory()
        assert result.passed is False
        assert 'writable' in result.message.lower() or 'write' in result.message.lower()

    def test_temp_directory_outer_exception(self):
        """Exception in tempfile.gettempdir() → outer except in temp check."""
        validator = EnvironmentValidator()
        with patch('tempfile.gettempdir', side_effect=RuntimeError('module failure')):
            result = validator._check_temp_directory()
        assert result.passed is True  # outer except returns passed=True with warning
        assert result.severity == 'warning'


class TestQuickCheckPythonFails:
    """Coverage for quick_check() when dxcom or python version check fails."""

    def test_quick_check_dxcom_not_found(self):
        """quick_check returns False when dxcom not found (line 445)."""
        with patch('src.environment_validator.shutil.which', return_value=None):
            validator = EnvironmentValidator()
            is_valid, message = validator.quick_check()
        assert is_valid is False
        assert message

    def test_quick_check_python_too_old(self):
        """quick_check returns False when python version appears too old (line 449)."""
        # Make dxcom check pass
        fake_result = type('R', (), {'stdout': 'dxcom 1.0', 'stderr': '', 'returncode': 0})()
        with patch('src.environment_validator.shutil.which', return_value='/usr/bin/dxcom'), \
             patch('subprocess.run', return_value=fake_result):
            validator = EnvironmentValidator()
            # Set MIN version higher than current so python check fails
            validator.MIN_PYTHON_VERSION = (4, 0)
            is_valid, message = validator.quick_check()
        assert is_valid is False
        assert message  # has some message


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
