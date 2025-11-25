import asyncio
import json
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.cluas_mcp.academic.academic_search_entrypoint import academic_search
from src.cluas_mcp.web.web_search_entrypoint import search_web, find_trending_topics, get_quick_facts
from src.cluas_mcp.news.news_search_entrypoint import search_news, get_environmental_data, verify_claim
from src.cluas_mcp.observation.observation_entrypoint import get_bird_sightings, get_weather_patterns, analyze_temporal_patterns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = Server("cluas-academic")

@mcp.list_tools()   
async def list_tools() -> list[Tool]:    
    """listing available tools."""
    return [
        # Corvus tools
        Tool(
            name="academic_search",
            description="Search academic papers across PubMed, Semantic Scholar, and ArXiv",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "search query for academic papers.",
                    }
                },
                "required": ["query"]
            }
        ),
        # Magpie tools
        Tool(
            name="search_web",
            description="Search the web for current information",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="find_trending_topics",
            description="Find trending topics in a given category",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Category to search for trends (e.g., 'general', 'technology', 'science')",
                        "default": "general"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_quick_facts",
            description="Get quick facts about a topic",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic to get facts about"
                    }
                },
                "required": ["topic"]
            }
        ),
        # Raven tools
        Tool(
            name="search_news",
            description="Search for current news articles",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_environmental_data",
            description="Get environmental data and statistics",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location to get data for (e.g., 'global', 'US', 'Europe')",
                        "default": "global"
                    },
                    "metric": {
                        "type": "string",
                        "description": "Type of metric to retrieve (e.g., 'temperature', 'co2', 'biodiversity')",
                        "default": "temperature"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="verify_claim",
            description="Verify the truthfulness of a claim",
            inputSchema={
                "type": "object",
                "properties": {
                    "claim": {
                        "type": "string",
                        "description": "The claim to verify"
                    }
                },
                "required": ["claim"]
            }
        ),
        # Crow tools
        Tool(
            name="get_bird_sightings",
            description="Get information about bird sightings",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location to get sightings for (e.g., 'global', 'US', 'California')",
                        "default": "global"
                    },
                    "species": {
                        "type": "string",
                        "description": "Optional species filter (e.g., 'corvus', 'crow', 'raven')"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_weather_patterns",
            description="Get weather pattern data",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location to get weather for (e.g., 'global', 'US', 'California')",
                        "default": "global"
                    },
                    "timeframe": {
                        "type": "string",
                        "description": "Timeframe for data (e.g., 'recent', 'weekly', 'monthly')",
                        "default": "recent"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="analyze_temporal_patterns",
            description="Analyze patterns over time",
            inputSchema={
                "type": "object",
                "properties": {
                    "data_type": {
                        "type": "string",
                        "description": "Type of data to analyze (e.g., 'bird_sightings', 'weather', 'behavior')"
                    },
                    "location": {
                        "type": "string",
                        "description": "Location to analyze patterns for",
                        "default": "global"
                    }
                },
                "required": ["data_type"]
            }
        ),
    ]
    
@mcp.call_tool()
async def call_tool(tool_name: str, arguments: dict) -> list[TextContent]:
    """handle tool calls"""
    loop = asyncio.get_event_loop()
    
    # Corvus tools
    if tool_name == "academic_search":
        query = arguments.get("query")
        if not query:
            raise ValueError("query is required for academic_search")
        results = await loop.run_in_executor(None, academic_search, query)
        formatted = format_search_results(results)
        return [TextContent(type="text", text=formatted)]
    
    # Magpie tools
    elif tool_name == "search_web":
        query = arguments.get("query")
        if not query:
            raise ValueError("query is required for search_web")
        results = await loop.run_in_executor(None, search_web, query)
        formatted = format_web_search_results(results)
        return [TextContent(type="text", text=formatted)]
    
    elif tool_name == "find_trending_topics":
        category = arguments.get("category", "general")
        results = await loop.run_in_executor(None, find_trending_topics, category)
        formatted = format_trending_topics(results)
        return [TextContent(type="text", text=formatted)]
    
    elif tool_name == "get_quick_facts":
        topic = arguments.get("topic")
        if not topic:
            raise ValueError("topic is required for get_quick_facts")
        results = await loop.run_in_executor(None, get_quick_facts, topic)
        formatted = format_quick_facts(results)
        return [TextContent(type="text", text=formatted)]
    
    # Raven tools
    elif tool_name == "search_news":
        query = arguments.get("query")
        if not query:
            raise ValueError("query is required for search_news")
        max_results = arguments.get("max_results", 5)
        results = await loop.run_in_executor(None, search_news, query, max_results)
        formatted = format_news_results(results)
        return [TextContent(type="text", text=formatted)]
    
    elif tool_name == "get_environmental_data":
        location = arguments.get("location", "global")
        metric = arguments.get("metric", "temperature")
        results = await loop.run_in_executor(None, get_environmental_data, location, metric)
        formatted = format_environmental_data(results)
        return [TextContent(type="text", text=formatted)]
    
    elif tool_name == "verify_claim":
        claim = arguments.get("claim")
        if not claim:
            raise ValueError("claim is required for verify_claim")
        results = await loop.run_in_executor(None, verify_claim, claim)
        formatted = format_verification_results(results)
        return [TextContent(type="text", text=formatted)]
    
    # Crow tools
    elif tool_name == "get_bird_sightings":
        location = arguments.get("location", "global")
        species = arguments.get("species")
        results = await loop.run_in_executor(None, get_bird_sightings, location, species)
        formatted = format_bird_sightings(results)
        return [TextContent(type="text", text=formatted)]
    
    elif tool_name == "get_weather_patterns":
        location = arguments.get("location", "global")
        timeframe = arguments.get("timeframe", "recent")
        results = await loop.run_in_executor(None, get_weather_patterns, location, timeframe)
        formatted = format_weather_patterns(results)
        return [TextContent(type="text", text=formatted)]

    elif tool_name == "analyze_temporal_patterns":
        data_type = arguments.get("data_type")
        if not data_type:
            raise ValueError("data_type is required for analyze_temporal_patterns")
        location = arguments.get("location", "global")
        results = await loop.run_in_executor(None, analyze_temporal_patterns, data_type, location)
        formatted = format_temporal_patterns(results)
        return [TextContent(type="text", text=formatted)]
    
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


def format_search_results(results: dict) -> str:
    """format search results into readable string"""
    output = []
    
    pubmed_results = results.get("pubmed", [])
    if pubmed_results:
        output.append("=== PubMed Results ===\n")
        for i, paper in enumerate(pubmed_results[:5], 1):
            output.append(f"{i}. {paper.get('title', 'No Title')}\n")
            authors = paper.get('authors', [])
            if authors:
                output.append(f"   Authors: {', '.join(authors[:3])}")
            abstract = paper.get('abstract', 'No Abstract')
            if  abstract != 'No Abstract':
                output.append(f"   Abstract: {abstract[:200]}...\n")
            output.append("")
            
    ss_results = results.get("semantic_scholar", [])
    if ss_results:
        output.append("=== Semantic Scholar Results ===\n")
        for i, paper in enumerate(ss_results[:5], 1):
            output.append(f"{i}. {paper.get('title', 'No Title')}\n")
            authors = paper.get('authors', [])
            if authors:
                output.append(f"   Authors: {', '.join(authors[:3])}")
            abstract = paper.get('abstract', 'No Abstract')
            if abstract != 'No Abstract':
                output.append(f"   Abstract: {abstract[:200]}...\n")
            output.append("")
            
    arxiv_results = results.get("arxiv", [])
    if arxiv_results:
        output.append("=== ArXiv Results ===\n")
        for i, paper in enumerate(arxiv_results[:5], 1):
            output.append(f"{i}. {paper.get('title', 'No Title')}\n")
            authors = paper.get('authors', [])
            if authors:
                output.append(f"   Authors: {', '.join(authors[:3])}")
            abstract = paper.get('abstract', 'No Abstract')
            if abstract != 'No Abstract':
                output.append(f"   Abstract: {abstract[:200]}...\n")
            output.append("")
    
    if not output:
        return "No results found."
    
    return "\n".join(output)

def format_web_search_results(results: dict) -> str:
    """Format web search results into readable string"""
    output = []
    output.append(f"=== Web Search Results for: {results.get('query', 'N/A')} ===\n")
    
    search_results = results.get("results", [])
    if search_results:
        for i, result in enumerate(search_results, 1):
            output.append(f"{i}. {result.get('title', 'No Title')}\n")
            output.append(f"   URL: {result.get('url', 'N/A')}\n")
            output.append(f"   {result.get('snippet', 'No snippet')}\n")
            output.append("")
    else:
        output.append("No results found.\n")
    
    return "\n".join(output)

def format_trending_topics(results: dict) -> str:
    """Format trending topics into readable string"""
    output = []
    output.append(f"=== Trending Topics ({results.get('category', 'general')}) ===\n")
    
    topics = results.get("trending_topics", [])
    if topics:
        for i, topic in enumerate(topics, 1):
            output.append(f"{i}. {topic.get('topic', 'N/A')} (Score: {topic.get('trend_score', 0)})\n")
            output.append(f"   {topic.get('description', 'No description')}\n")
            output.append("")
    else:
        output.append("No trending topics found.\n")
    
    return "\n".join(output)

def format_quick_facts(results: dict) -> str:
    """Format quick facts into readable string"""
    output = []
    output.append(f"=== Quick Facts: {results.get('topic', 'N/A')} ===\n")
    
    facts = results.get("facts", [])
    if facts:
        for i, fact in enumerate(facts, 1):
            output.append(f"{i}. {fact}\n")
    else:
        output.append("No facts found.\n")
    
    return "\n".join(output)

def format_news_results(results: dict) -> str:
    """Format news search results into readable string"""
    output = []
    output.append(f"=== News Search Results for: {results.get('query', 'N/A')} ===\n")
    
    articles = results.get("articles", [])
    if articles:
        for i, article in enumerate(articles, 1):
            output.append(f"{i}. {article.get('title', 'No Title')}\n")
            output.append(f"   Source: {article.get('source', 'Unknown')}\n")
            output.append(f"   Published: {article.get('published_date', 'Unknown')}\n")
            output.append(f"   {article.get('summary', 'No summary')}\n")
            output.append(f"   URL: {article.get('url', 'N/A')}\n")
            output.append("")
    else:
        output.append("No news articles found.\n")
    
    return "\n".join(output)

def format_environmental_data(results: dict) -> str:
    """Format environmental data into readable string"""
    output = []
    data = results.get("data", {})
    output.append(f"=== Environmental Data: {results.get('metric', 'N/A')} in {results.get('location', 'N/A')} ===\n")
    output.append(f"Current Value: {data.get('current_value', 'N/A')} {data.get('unit', '')}\n")
    output.append(f"Trend: {data.get('trend', 'N/A')}\n")
    output.append(f"Last Updated: {data.get('last_updated', 'N/A')}\n")
    output.append(f"Description: {data.get('description', 'No description')}\n")
    
    return "\n".join(output)

def format_verification_results(results: dict) -> str:
    """Format claim verification results into readable string"""
    output = []
    output.append(f"=== Claim Verification ===\n")
    output.append(f"Claim: {results.get('claim', 'N/A')}\n")
    output.append(f"Status: {results.get('verification_status', 'N/A')}\n")
    output.append(f"Confidence: {results.get('confidence', 0)}\n")
    output.append(f"Explanation: {results.get('explanation', 'No explanation')}\n")
    
    return "\n".join(output)

def format_bird_sightings(results: dict) -> str:
    """Format bird sightings into readable string"""
    output = []
    output.append(f"=== Bird Sightings: {results.get('species', 'all')} in {results.get('location', 'N/A')} ===\n")
    
    sightings = results.get("sightings", [])
    if sightings:
        for i, sighting in enumerate(sightings, 1):
            output.append(f"{i}. {sighting.get('common_name', 'Unknown')} ({sighting.get('species', 'Unknown')})\n")
            output.append(f"   Date: {sighting.get('date', 'Unknown')}\n")
            output.append(f"   Location: {sighting.get('location', 'Unknown')}\n")
            output.append(f"   Notes: {sighting.get('notes', 'No notes')}\n")
            output.append("")
    else:
        output.append("No sightings found.\n")
    
    output.append(f"Total Sightings: {results.get('total_sightings', 0)}\n")
    
    return "\n".join(output)

def format_weather_patterns(results: dict) -> str:
    """Format weather patterns into readable string"""
    output = []
    patterns = results.get("patterns", {})
    output.append(f"=== Weather Patterns: {results.get('location', 'N/A')} ({results.get('timeframe', 'N/A')}) ===\n")
    output.append(f"Average Temperature: {patterns.get('average_temperature', 'N/A')} {patterns.get('temperature_unit', '')}\n")
    output.append(f"Precipitation: {patterns.get('precipitation', 'N/A')} {patterns.get('precipitation_unit', '')}\n")
    output.append(f"Humidity: {patterns.get('humidity', 'N/A')}%\n")
    output.append(f"Wind Speed: {patterns.get('wind_speed', 'N/A')} {patterns.get('wind_unit', '')}\n")
    output.append(f"Description: {patterns.get('description', 'No description')}\n")
    
    return "\n".join(output)

def format_temporal_patterns(results: dict) -> str:
    """Format temporal pattern analysis into readable string"""
    output = []
    analysis = results.get("analysis", {})
    output.append(f"=== Temporal Pattern Analysis: {results.get('data_type', 'N/A')} in {results.get('location', 'N/A')} ===\n")
    output.append(f"Time Range: {results.get('time_range', 'N/A')}\n")
    output.append(f"Trend: {analysis.get('trend', 'N/A')}\n")
    output.append(f"Seasonality: {analysis.get('seasonality', 'N/A')}\n")
    output.append(f"Peak Periods: {', '.join(analysis.get('peak_periods', []))}\n")
    output.append(f"Confidence: {analysis.get('confidence', 0)}\n")
    output.append(f"Description: {analysis.get('description', 'No description')}\n")
    
    return "\n".join(output)

async def main():
    """"run the MCP server."""
    logger.info("Starting CLUAS academic MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(
            read_stream, 
            write_stream,
            mcp.create_initialization_options()
            )
        
if __name__ == "__main__":
    asyncio.run(main())