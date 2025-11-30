import asyncio
import json
import logging
from typing import Dict, Any, Callable, List, TypedDict
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.cluas_mcp.academic.academic_search_entrypoint import academic_search
from src.cluas_mcp.web.explore_web import explore_web
from src.cluas_mcp.web.trending import get_trends, explore_trend_angles
from src.cluas_mcp.news.news_search_entrypoint import verify_news
from src.cluas_mcp.observation.observation_entrypoint import get_bird_sightings, get_weather_patterns, analyze_temporal_patterns
from src.cluas_mcp.common.check_local_weather import check_local_weather_sync
from src.cluas_mcp.formatters import (
    format_bird_sightings, 
    format_news_results, 
    format_local_weather, 
    format_search_results, 
    format_temporal_patterns, 
    format_trend_angles, 
    format_trending_topics, 
    format_weather_patterns,
    format_web_search_results
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = Server("cluas-huginn")

# Define a type for tool handlers
class ToolHandler(TypedDict):
    handler: Callable
    formatter: Callable
    required_args: List[str]
    description: str
    inputSchema: Dict[str, Any]

# Centralized tool definitions - single source of truth
TOOL_HANDLERS: Dict[str, ToolHandler] = {
    "academic_search": {
        "handler": academic_search,
        "formatter": format_search_results,
        "required_args": ["query"],
        "description": "Search academic papers across PubMed, Semantic Scholar, and ArXiv",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for academic papers.",
                }
            },
            "required": ["query"]
        },
    },
    "explore_web": {
        "handler": explore_web,
        "formatter": format_web_search_results,
        "required_args": ["query"],
        "description": "Search the web for current information",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string",
                }
            },
            "required": ["query"]
        },
    },
    "get_trends": {
        "handler": get_trends,
        "formatter": format_trending_topics,
        "required_args": [],
        "description": "Find trending topics in a given category",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Category to search for trends (e.g., 'general', 'technology', 'science')",
                    "default": "general"
                }
            },
            "required": []
        },
    },
    "explore_trend_angles": {
        "handler": explore_trend_angles,
        "formatter": format_trend_angles,
        "required_args": ["topic"],
        "description": "Explore a trend from multiple angles: trending status, drivers, cultural narrative, local context, and criticism. Use for comprehensive trend analysis when you need to understand why something is trending and its broader implications.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Trend or topic to explore (e.g., 'AI', 'climate change', 'cryptocurrency')"
                },
                "location": {
                    "type": "string",
                    "description": "Optional location for local angle (e.g., 'United States', 'Europe', 'Asia')",
                    "default": None
                },
                "depth": {
                    "type": "string",
                    "description": "Analysis depth: 'light' (quick), 'medium' (standard), 'deep' (thorough with criticism)",
                    "enum": ["light", "medium", "deep"],
                    "default": "medium"
                }
            },
            "required": ["topic"]
        },
    },
    "verify_news": {
        "handler": verify_news,
        "formatter": format_news_results,
        "required_args": ["query"],
        "description": "Search for current news articles and reports",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Topic or question to search in news outlets"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of articles to return (default 5)",
                    "default": 5
                }
            },
            "required": ["query"]
        },
    },
    "get_bird_sightings": {
        "handler": get_bird_sightings,
        "formatter": format_bird_sightings,
        "required_args": ["location"],
        "description": "Get recent bird sightings near a location",
        "inputSchema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Location to search for bird sightings"
                },
                "species": {
                    "type": "string",
                    "description": "Optional species filter (e.g., 'crow', 'raven')",
                    "default": None
                }
            },
            "required": ["location"]
        },
    },
    "get_weather_patterns": {
        "handler": get_weather_patterns,
        "formatter": format_weather_patterns,
        "required_args": ["location"],
        "description": "Get current weather data for a location",
        "inputSchema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Location to get weather for (e.g., 'Tokyo', 'Glasgow')"
                },
                "timeframe": {
                    "type": "string",
                    "description": "Timeframe for data (e.g., 'recent', 'weekly')",
                    "default": "recent"
                }
            },
            "required": ["location"]
        },
    },
    "analyze_temporal_patterns": {
        "handler": analyze_temporal_patterns,
        "formatter": format_temporal_patterns,
        "required_args": ["data_type"],
        "description": "Analyze temporal patterns in observational data including trends, seasonality, peak periods, environmental correlations, and predictions",
        "inputSchema": {
            "type": "object",
            "properties": {
                "data_type": {
                    "type": "string",
                    "description": "Type of data to analyze (e.g., 'bird_sightings', 'weather', 'behavior', 'air_quality', 'moon_phase', 'sun_times')"
                },
                "location": {
                    "type": "string",
                    "description": "Location to analyze patterns for (e.g., 'Tokyo, Japan')",
                    "default": "global"
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days to analyze",
                    "default": 30
                }
            },
            "required": ["data_type"]
        },
    },
    "check_local_weather": {
        "handler": check_local_weather_sync,
        "formatter": format_local_weather,
        "required_args": [],
        "description": "Get current weather conditions for a location",
        "inputSchema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Location to get weather for (e.g., 'Cambridge, MA')",
                    "default": None
                }
            },
            "required": []
        },
    },
}



@mcp.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools, generated from TOOL_HANDLERS."""
    return [
        Tool(
            name=tool_name,
            description=handler["description"],
            inputSchema=handler["inputSchema"],
        )
        for tool_name, handler in TOOL_HANDLERS.items()
    ]

@mcp.call_tool()
async def call_tool(tool_name: str, arguments: dict) -> List[TextContent]:
    """Call a tool using the centralized handler pattern."""
    logger.info(f"Calling tool: {tool_name} with arguments: {arguments}")

    if tool_name not in TOOL_HANDLERS:
        raise ValueError(f"Unknown tool: {tool_name}")

    handler_info = TOOL_HANDLERS[tool_name]
    handler_func = handler_info["handler"]
    formatter_func = handler_info["formatter"]
    required_args = handler_info["required_args"]

    # Validate required arguments
    for arg in required_args:
        if arg not in arguments or arguments[arg] is None:
            raise ValueError(f"'{arg}' is required for tool '{tool_name}'")

    # Call handler with arguments
    loop = asyncio.get_event_loop()
    try:
        if asyncio.iscoroutinefunction(handler_func):
            results = await handler_func(**arguments)
        else:
            results = await loop.run_in_executor(None, lambda: handler_func(**arguments))
        logger.debug(f"Tool {tool_name} returned results: {results}")
    except Exception as e:
        logger.error(f"Error calling tool {tool_name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

    formatted = formatter_func(results)
    return [TextContent(type="text", text=formatted)]



async def main():
    """"run the MCP server."""
    logger.info("Starting cluas_huginn MCP Server, the dialectic deliberative engine")
    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(
            read_stream, 
            write_stream,
            mcp.create_initialization_options()
            )
        
if __name__ == "__main__":
    asyncio.run(main())