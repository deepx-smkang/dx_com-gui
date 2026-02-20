"""
Tests for environment validation module.
"""
import sys
import os
import tempfile
import shutil
from pathlib import Path
import pytest

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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
