"""
Error handling for DXCom compilation failures.

This module provides comprehensive error handling for dxcom subprocess execution,
including parsing error messages, categorizing failures, and providing user-friendly
error displays.
"""
import re
from enum import Enum
from typing import Optional, Dict, List
from dataclasses import dataclass


class ErrorCategory(Enum):
    """Categories of compilation errors."""
    PROCESS_FAILURE = "process_failure"      # Non-zero exit code
    TIMEOUT = "timeout"                       # Process timeout
    FILE_NOT_FOUND = "file_not_found"        # dxcom binary not found
    INPUT_ERROR = "input_error"              # Invalid input file
    OUTPUT_ERROR = "output_error"            # Output write failure
    MEMORY_ERROR = "memory_error"            # Out of memory
    UNSUPPORTED_OP = "unsupported_op"        # Unsupported ONNX operator
    CONFIG_ERROR = "config_error"            # Configuration error
    CRASH = "crash"                          # Unexpected crash/exception
    UNKNOWN = "unknown"                      # Unknown error


@dataclass
class DXComError:
    """
    Structured representation of a DXCom error.
    
    Attributes:
        category: Error category
        exit_code: Process exit code (if applicable)
        message: Raw error message from dxcom
        user_message: User-friendly error message
        suggestions: List of suggested fixes
        technical_details: Technical details for advanced users
    """
    category: ErrorCategory
    exit_code: Optional[int]
    message: str
    user_message: str
    suggestions: List[str]
    technical_details: Optional[str] = None


class DXComErrorParser:
    """
    Parser for DXCom error messages.
    
    This class analyzes dxcom output and exit codes to identify error types,
    extract meaningful information, and provide actionable user guidance.
    """
    
    # Error patterns to match in dxcom output
    # NOTE: Order matters! More specific patterns should come first
    ERROR_PATTERNS = [
        # Configuration errors (must come first to avoid being caught by generic patterns)
        (r'config.*(?:not\s+found|cannot\s+(?:open|read))',
         ErrorCategory.CONFIG_ERROR,
         "Configuration file error"),
        
        (r'(?:invalid|malformed|missing)\s+(?:config|configuration|option|parameter)',
         ErrorCategory.CONFIG_ERROR,
         "Configuration error"),
        
        # Output errors (specific, before generic file patterns)
        (r'(?:cannot|failed to|unable to)\s+(?:write|create|save)\s+(?:to\s+)?output',
         ErrorCategory.OUTPUT_ERROR,
         "Failed to write output file"),
        
        # Input/Output errors
        (r'(?:cannot|failed to|unable to)\s+(?:open|read|load|parse)\s+(?:input|file|model)',
         ErrorCategory.INPUT_ERROR,
         "Failed to read input file"),
        
        (r'(?:file|path)\s+not\s+(?:found|exist)',
         ErrorCategory.INPUT_ERROR,
         "File not found"),
        
        (r'(?:invalid|corrupted|malformed)\s+(?:onnx|model|file)',
         ErrorCategory.INPUT_ERROR,
         "Invalid or corrupted ONNX model"),
        
        # Memory errors
        (r'(?:out\s+of\s+memory|memory\s+allocation\s+failed|insufficient\s+memory)',
         ErrorCategory.MEMORY_ERROR,
         "Out of memory"),
        
        # Unsupported operations
        (r'(?:unsupported|unknown|not\s+supported)\s+(?:operator|operation|op|node|layer)',
         ErrorCategory.UNSUPPORTED_OP,
         "Unsupported ONNX operator"),
    ]
    
    @classmethod
    def parse_error(cls,
                   exit_code: Optional[int],
                   output: str,
                   exception: Optional[Exception] = None) -> DXComError:
        """
        Parse compilation error and create structured error object.
        
        Args:
            exit_code: Process exit code (None if process didn't run)
            output: Combined stdout/stderr output from dxcom
            exception: Exception that occurred (if any)
            
        Returns:
            DXComError object with categorized error information
        """
        # Handle exception-based errors first
        if exception:
            return cls._handle_exception(exception, output)
        
        # Handle exit code errors
        if exit_code is not None and exit_code != 0:
            return cls._parse_process_failure(exit_code, output)
        
        # Unknown error (should not reach here)
        return DXComError(
            category=ErrorCategory.UNKNOWN,
            exit_code=exit_code,
            message="Unknown error occurred",
            user_message="An unknown error occurred during compilation",
            suggestions=["Check the output log for details",
                        "Verify input file is a valid ONNX model",
                        "Try with different compiler options"]
        )
    
    @classmethod
    def _handle_exception(cls, exception: Exception, output: str) -> DXComError:
        """Handle Python exceptions during execution."""
        if isinstance(exception, FileNotFoundError):
            return DXComError(
                category=ErrorCategory.FILE_NOT_FOUND,
                exit_code=None,
                message=str(exception),
                user_message="DXCom compiler not found",
                suggestions=[
                    "Ensure dxcom is installed on your system",
                    "Add dxcom to your system PATH",
                    "Use Help > Check DXCom Status to verify installation"
                ],
                technical_details=f"Command 'dxcom' not found in PATH"
            )
        
        elif isinstance(exception, TimeoutError):
            return DXComError(
                category=ErrorCategory.TIMEOUT,
                exit_code=None,
                message=str(exception),
                user_message="Compilation timed out",
                suggestions=[
                    "The model may be too large or complex",
                    "Try reducing optimization level",
                    "Ensure system has sufficient resources",
                    "Consider using a more powerful machine"
                ],
                technical_details=output if output else "Process timed out"
            )
        
        else:
            return DXComError(
                category=ErrorCategory.CRASH,
                exit_code=None,
                message=str(exception),
                user_message=f"Unexpected error: {type(exception).__name__}",
                suggestions=[
                    "This may be a bug in the application",
                    "Check the output log for details",
                    "Report this issue to support"
                ],
                technical_details=f"{type(exception).__name__}: {str(exception)}\n\n{output}"
            )
    
    @classmethod
    def _parse_process_failure(cls, exit_code: int, output: str) -> DXComError:
        """Parse process failure based on exit code and output."""
        output_lower = output.lower()
        
        # Try to match known error patterns
        for pattern, category, short_msg in cls.ERROR_PATTERNS:
            if re.search(pattern, output_lower, re.IGNORECASE):
                return cls._create_categorized_error(
                    category, exit_code, output, short_msg
                )
        
        # Generic process failure
        return cls._create_generic_failure(exit_code, output)
    
    @classmethod
    def _create_categorized_error(cls,
                                  category: ErrorCategory,
                                  exit_code: int,
                                  output: str,
                                  short_msg: str) -> DXComError:
        """Create error object for a categorized error."""
        suggestions = cls._get_suggestions_for_category(category)
        user_message = cls._get_user_message_for_category(category, short_msg)
        
        return DXComError(
            category=category,
            exit_code=exit_code,
            message=short_msg,
            user_message=user_message,
            suggestions=suggestions,
            technical_details=cls._extract_relevant_error_lines(output)
        )
    
    @classmethod
    def _create_generic_failure(cls, exit_code: int, output: str) -> DXComError:
        """Create error object for generic process failure."""
        # Try to extract error message from output
        error_lines = cls._extract_relevant_error_lines(output)
        
        return DXComError(
            category=ErrorCategory.PROCESS_FAILURE,
            exit_code=exit_code,
            message=f"Process exited with code {exit_code}",
            user_message=f"Compilation failed (exit code {exit_code})",
            suggestions=[
                "Check the output log for error details",
                "Verify the input ONNX model is valid",
                "Try different compiler options",
                "Ensure the output path is writable"
            ],
            technical_details=error_lines
        )
    
    @classmethod
    def _extract_relevant_error_lines(cls, output: str, max_lines: int = 20) -> str:
        """
        Extract relevant error lines from output.
        
        Looks for lines containing error keywords and returns them along
        with some context.
        """
        if not output:
            return "No output available"
        
        lines = output.split('\n')
        error_keywords = ['error', 'fail', 'exception', 'fatal', 'crash',
                         'abort', 'invalid', 'cannot', 'unable']
        
        # Find lines with error keywords
        error_indices = []
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in error_keywords):
                error_indices.append(i)
        
        if not error_indices:
            # No explicit errors found, return last N lines
            return '\n'.join(lines[-max_lines:])
        
        # Extract error lines with context (1 line before, 2 lines after)
        result_lines = []
        seen_indices = set()
        
        for idx in error_indices:
            start = max(0, idx - 1)
            end = min(len(lines), idx + 3)
            for i in range(start, end):
                if i not in seen_indices:
                    result_lines.append((i, lines[i]))
                    seen_indices.add(i)
        
        # Sort by line number and format
        result_lines.sort(key=lambda x: x[0])
        formatted = '\n'.join(line for _, line in result_lines[-max_lines:])
        
        return formatted if formatted else '\n'.join(lines[-max_lines:])
    
    @classmethod
    def _get_suggestions_for_category(cls, category: ErrorCategory) -> List[str]:
        """Get suggestions based on error category."""
        suggestions_map = {
            ErrorCategory.INPUT_ERROR: [
                "Verify the input file path is correct",
                "Ensure the file is a valid ONNX model",
                "Check file permissions",
                "Try opening the model with another ONNX tool"
            ],
            ErrorCategory.OUTPUT_ERROR: [
                "Check that the output directory exists",
                "Verify you have write permissions",
                "Ensure sufficient disk space is available",
                "Try a different output path"
            ],
            ErrorCategory.MEMORY_ERROR: [
                "The model may be too large for available memory",
                "Close other applications to free up memory",
                "Try reducing optimization level",
                "Consider using a machine with more RAM"
            ],
            ErrorCategory.UNSUPPORTED_OP: [
                "The model uses operators not supported by dxcom",
                "Check dxcom documentation for supported operators",
                "Try simplifying the model",
                "Update to the latest version of dxcom"
            ],
            ErrorCategory.CONFIG_ERROR: [
                "Verify the config file path is correct",
                "Ensure the config file is valid JSON",
                "Check that all required fields are present",
                "Try without a config file to use defaults"
            ],
            ErrorCategory.TIMEOUT: [
                "The compilation is taking too long",
                "Try with a smaller model first",
                "Reduce optimization level",
                "Ensure system is not under heavy load"
            ],
            ErrorCategory.PROCESS_FAILURE: [
                "Check the output log for details",
                "Verify all input parameters",
                "Try with default compiler options"
            ],
        }
        
        return suggestions_map.get(category, [
            "Check the output log for details",
            "Verify input files and parameters",
            "Consult dxcom documentation"
        ])
    
    @classmethod
    def _get_user_message_for_category(cls,
                                      category: ErrorCategory,
                                      short_msg: str) -> str:
        """Get user-friendly message based on category."""
        category_messages = {
            ErrorCategory.INPUT_ERROR: "Failed to read or parse input file",
            ErrorCategory.OUTPUT_ERROR: "Failed to write output file",
            ErrorCategory.MEMORY_ERROR: "Out of memory during compilation",
            ErrorCategory.UNSUPPORTED_OP: "Model contains unsupported operators",
            ErrorCategory.CONFIG_ERROR: "Configuration file error",
            ErrorCategory.TIMEOUT: "Compilation timed out",
            ErrorCategory.PROCESS_FAILURE: "Compilation failed",
        }
        
        return category_messages.get(category, short_msg)


def format_error_for_display(error: DXComError, include_technical: bool = True) -> str:
    """
    Format error for display in GUI dialog or output log.
    
    Args:
        error: DXComError object
        include_technical: Whether to include technical details
        
    Returns:
        Formatted error message
    """
    lines = []
    
    # Header
    lines.append("═" * 60)
    lines.append("COMPILATION ERROR")
    lines.append("═" * 60)
    lines.append("")
    
    # Main message
    lines.append(f"Error: {error.user_message}")
    lines.append("")
    
    # Exit code if available
    if error.exit_code is not None:
        lines.append(f"Exit Code: {error.exit_code}")
        lines.append("")
    
    # Suggestions
    if error.suggestions:
        lines.append("Suggestions:")
        for suggestion in error.suggestions:
            lines.append(f"  • {suggestion}")
        lines.append("")
    
    # Technical details
    if include_technical and error.technical_details:
        lines.append("Technical Details:")
        lines.append("-" * 60)
        lines.append(error.technical_details)
        lines.append("-" * 60)
    
    return "\n".join(lines)

