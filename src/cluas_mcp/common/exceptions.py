"""
Standardized exception types for MCP tool handlers.
"""
from typing import Optional


class ToolExecutionError(Exception):
    """Base exception for tool execution errors."""
    def __init__(self, tool_name: str, message: str, original_error: Optional[Exception] = None):
        self.tool_name = tool_name
        self.original_error = original_error
        super().__init__(f"Tool '{tool_name}' failed: {message}")


class ToolValidationError(Exception):
    """Exception for tool argument validation errors."""
    def __init__(self, tool_name: str, missing_args: list[str]):
        self.tool_name = tool_name
        self.missing_args = missing_args
        super().__init__(f"Tool '{tool_name}' missing required arguments: {', '.join(missing_args)}")


class ToolNotFoundError(Exception):
    """Exception for when a tool is not found in registry."""
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' not found in registry")

