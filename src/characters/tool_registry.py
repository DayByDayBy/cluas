"""
Tool registry that converts MCP server tool definitions to OpenAI function calling format.
Eliminates duplication of tool definitions across character classes.
"""
from typing import Dict, List, Any, Optional
import sys

# Import TOOL_HANDLERS from MCP server
# Use try/except to handle import errors gracefully
try:
    from src.cluas_mcp.server import TOOL_HANDLERS
except ImportError:
    # Fallback if MCP server not available
    TOOL_HANDLERS: Dict[str, Any] = {}
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("Could not import TOOL_HANDLERS from MCP server")


def mcp_to_openai_format(tool_name: str, tool_handler: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert MCP tool schema to OpenAI function calling format.
    
    Args:
        tool_name: Name of the tool
        tool_handler: Tool handler dict from TOOL_HANDLERS
        
    Returns:
        OpenAI function calling format dict
    """
    input_schema = tool_handler.get("inputSchema", {})
    
    # Clean up the schema - remove None defaults and ensure proper format
    properties = input_schema.get("properties", {}).copy()
    for prop_name, prop_def in properties.items():
        # Remove None defaults
        if "default" in prop_def and prop_def["default"] is None:
            prop_def = prop_def.copy()
            del prop_def["default"]
            properties[prop_name] = prop_def
    
    return {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": tool_handler.get("description", ""),
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": input_schema.get("required", [])
            }
        }
    }


def get_tools_for_character(tool_names: List[str]) -> List[Dict[str, Any]]:
    """
    Get OpenAI-formatted tool definitions for a list of tool names.
    
    Args:
        tool_names: List of tool names to include
        
    Returns:
        List of OpenAI function calling format dicts
    """
    tools = []
    for tool_name in tool_names:
        if tool_name in TOOL_HANDLERS:
            tools.append(mcp_to_openai_format(tool_name, TOOL_HANDLERS[tool_name]))
        else:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Tool '{tool_name}' not found in TOOL_HANDLERS")
    return tools


def get_all_available_tools() -> List[str]:
    """Get list of all available tool names."""
    return list(TOOL_HANDLERS.keys())

