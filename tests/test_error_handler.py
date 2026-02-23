#!/usr/bin/env python3
"""
Unit tests for DXCom error handling.

Tests error parsing, categorization, and message formatting.
"""
import unittest
from src.error_handler import (
    DXComError, DXComErrorParser, ErrorCategory,
    format_error_for_display
)


class TestErrorParsing(unittest.TestCase):
    """Test error parsing and categorization."""
    
    def test_input_file_not_found(self):
        """Test parsing of input file not found error."""
        output = "Error: Cannot open input file '/path/to/model.onnx'\nFile not found"
        error = DXComErrorParser.parse_error(exit_code=1, output=output)
        
        self.assertEqual(error.category, ErrorCategory.INPUT_ERROR)
        self.assertEqual(error.exit_code, 1)
        self.assertIn("file", error.user_message.lower())
        self.assertTrue(len(error.suggestions) > 0)
    
    def test_invalid_onnx_model(self):
        """Test parsing of invalid ONNX model error."""
        output = "Error: Invalid ONNX model format\nFailed to parse model"
        error = DXComErrorParser.parse_error(exit_code=2, output=output)
        
        self.assertEqual(error.category, ErrorCategory.INPUT_ERROR)
        self.assertIn("input", error.user_message.lower())
    
    def test_output_write_error(self):
        """Test parsing of output write error."""
        output = "Error: Cannot write to output file '/path/output.dxnn'\nPermission denied"
        error = DXComErrorParser.parse_error(exit_code=3, output=output)
        
        self.assertEqual(error.category, ErrorCategory.OUTPUT_ERROR)
        self.assertIn("output", error.user_message.lower())
    
    def test_memory_error(self):
        """Test parsing of out of memory error."""
        output = "Fatal: Out of memory\nMemory allocation failed for tensor"
        error = DXComErrorParser.parse_error(exit_code=4, output=output)
        
        self.assertEqual(error.category, ErrorCategory.MEMORY_ERROR)
        self.assertIn("memory", error.user_message.lower())
        self.assertIn("memory", error.suggestions[0].lower())
    
    def test_unsupported_operator(self):
        """Test parsing of unsupported operator error."""
        output = "Error: Unsupported operator 'CustomOp'\nOperator not implemented in dxcom"
        error = DXComErrorParser.parse_error(exit_code=5, output=output)
        
        self.assertEqual(error.category, ErrorCategory.UNSUPPORTED_OP)
        self.assertIn("unsupported", error.user_message.lower())
    
    def test_config_file_error(self):
        """Test parsing of config file error."""
        output = "Error: Cannot open config file 'config.json'\nConfig file not found"
        error = DXComErrorParser.parse_error(exit_code=6, output=output)
        
        self.assertEqual(error.category, ErrorCategory.CONFIG_ERROR)
        self.assertIn("config", error.user_message.lower())
    
    def test_file_not_found_exception(self):
        """Test handling of FileNotFoundError exception."""
        exception = FileNotFoundError("dxcom: command not found")
        error = DXComErrorParser.parse_error(
            exit_code=None,
            output="",
            exception=exception
        )
        
        self.assertEqual(error.category, ErrorCategory.FILE_NOT_FOUND)
        self.assertIsNone(error.exit_code)
        self.assertIn("not found", error.user_message.lower())
        self.assertTrue(len(error.suggestions) > 0)
    
    def test_timeout_exception(self):
        """Test handling of TimeoutError exception."""
        exception = TimeoutError("Process timed out after 300 seconds")
        error = DXComErrorParser.parse_error(
            exit_code=None,
            output="Some partial output...",
            exception=exception
        )
        
        self.assertEqual(error.category, ErrorCategory.TIMEOUT)
        self.assertIsNone(error.exit_code)
        self.assertIn("timed out", error.user_message.lower())
    
    def test_generic_exception(self):
        """Test handling of generic exceptions."""
        exception = RuntimeError("Unexpected error occurred")
        error = DXComErrorParser.parse_error(
            exit_code=None,
            output="",
            exception=exception
        )
        
        self.assertEqual(error.category, ErrorCategory.CRASH)
        self.assertIn("RuntimeError", error.user_message)
    
    def test_generic_process_failure(self):
        """Test generic process failure without specific error pattern."""
        output = "Some generic error output without keywords"
        error = DXComErrorParser.parse_error(exit_code=99, output=output)
        
        self.assertEqual(error.category, ErrorCategory.PROCESS_FAILURE)
        self.assertEqual(error.exit_code, 99)
        self.assertIn("99", error.user_message)
    
    def test_multiple_error_lines_extraction(self):
        """Test extraction of relevant error lines from output."""
        output = """Starting compilation...
Loading model...
Optimizing graph...
Error: Unsupported operator 'CustomLayer'
Fatal: Cannot continue compilation
Process terminated
"""
        error = DXComErrorParser.parse_error(exit_code=1, output=output)
        
        self.assertIsNotNone(error.technical_details)
        self.assertIn("Error", error.technical_details)
        self.assertIn("Fatal", error.technical_details)


class TestErrorFormatting(unittest.TestCase):
    """Test error formatting for display."""
    
    def test_format_for_display(self):
        """Test formatting error for display with technical details."""
        error = DXComError(
            category=ErrorCategory.INPUT_ERROR,
            exit_code=1,
            message="File not found",
            user_message="Failed to read input file",
            suggestions=["Check file path", "Verify file exists"],
            technical_details="Error: /path/to/file.onnx not found"
        )
        
        formatted = format_error_for_display(error, include_technical=True)
        
        self.assertIn("COMPILATION ERROR", formatted)
        self.assertIn("Failed to read input file", formatted)
        self.assertIn("Exit Code: 1", formatted)
        self.assertIn("Suggestions:", formatted)
        self.assertIn("Check file path", formatted)
        self.assertIn("Technical Details:", formatted)
        self.assertIn("/path/to/file.onnx", formatted)
    
    def test_format_for_display_without_technical(self):
        """Test formatting error for display without technical details."""
        error = DXComError(
            category=ErrorCategory.TIMEOUT,
            exit_code=None,
            message="Timeout",
            user_message="Compilation timed out",
            suggestions=["Try smaller model"],
            technical_details="Long output..."
        )
        
        formatted = format_error_for_display(error, include_technical=False)
        
        self.assertIn("Compilation timed out", formatted)
        self.assertNotIn("Long output", formatted)


class TestErrorSuggestions(unittest.TestCase):
    """Test error suggestion generation."""
    
    def test_input_error_suggestions(self):
        """Test suggestions for input errors."""
        error = DXComErrorParser.parse_error(
            exit_code=1,
            output="Error: Cannot open input file",
            exception=None
        )
        
        suggestions = error.suggestions
        self.assertTrue(any("path" in s.lower() for s in suggestions))
        self.assertTrue(any("valid" in s.lower() or "onnx" in s.lower() for s in suggestions))
    
    def test_output_error_suggestions(self):
        """Test suggestions for output errors."""
        error = DXComErrorParser.parse_error(
            exit_code=1,
            output="Error: Failed to write output file",
            exception=None
        )
        
        suggestions = error.suggestions
        self.assertTrue(any("permission" in s.lower() or "write" in s.lower() for s in suggestions))
        self.assertTrue(any("disk" in s.lower() or "space" in s.lower() for s in suggestions))
    
    def test_memory_error_suggestions(self):
        """Test suggestions for memory errors."""
        error = DXComErrorParser.parse_error(
            exit_code=1,
            output="Fatal: Out of memory",
            exception=None
        )
        
        suggestions = error.suggestions
        self.assertTrue(any("memory" in s.lower() or "ram" in s.lower() for s in suggestions))
    
    def test_timeout_suggestions(self):
        """Test suggestions for timeout errors."""
        error = DXComErrorParser.parse_error(
            exit_code=None,
            output="Partial output...",
            exception=TimeoutError("Timeout")
        )
        
        suggestions = error.suggestions
        self.assertTrue(any("smaller" in s.lower() or "model" in s.lower() for s in suggestions))
        self.assertTrue(any("optimization" in s.lower() or "level" in s.lower() for s in suggestions))


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def test_empty_output(self):
        """Test handling of empty output."""
        error = DXComErrorParser.parse_error(exit_code=1, output="")
        
        self.assertIsNotNone(error)
        self.assertEqual(error.category, ErrorCategory.PROCESS_FAILURE)
    
    def test_no_exit_code_no_exception(self):
        """Test handling when neither exit code nor exception provided."""
        error = DXComErrorParser.parse_error(exit_code=None, output="Some output")
        
        self.assertIsNotNone(error)
        self.assertEqual(error.category, ErrorCategory.UNKNOWN)
    
    def test_very_long_output(self):
        """Test handling of very long output."""
        long_output = "\n".join([f"Line {i}" for i in range(1000)])
        long_output += "\nError: Something went wrong\n"
        
        error = DXComErrorParser.parse_error(exit_code=1, output=long_output)
        
        self.assertIsNotNone(error.technical_details)
        # Should extract relevant lines, not all 1000
        detail_lines = error.technical_details.split('\n')
        self.assertLessEqual(len(detail_lines), 25)  # Should be limited


if __name__ == '__main__':
    unittest.main()
