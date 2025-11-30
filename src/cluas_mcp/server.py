import asyncio
import json
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.cluas_mcp.academic.academic_search_entrypoint import academic_search
from src.cluas_mcp.web.explore_web import explore_web
from src.cluas_mcp.web.trending import get_trends, explore_trend_angles
from src.cluas_mcp.news.news_search_entrypoint import verify_news
from src.cluas_mcp.observation.observation_entrypoint import get_bird_sightings, get_weather_patterns, analyze_temporal_patterns
from src.cluas_mcp.common.check_local_weather import check_local_weather_sync


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = Server("cluas-huginn")

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
            name="explore_web",
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
            name="get_trends",
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
            name="explore_trend_angles",
            description="Explore a trend from multiple angles: trending status, drivers, cultural narrative, local context, and criticism. "
                       "Use for comprehensive trend analysis when you need to understand why something is trending "
                       "and its broader implications. Specify topic (required), optionally location and depth.",
            inputSchema={
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
            }
        ),
        # Raven tools
        Tool(
            name="verify_news",
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
            description="Analyze temporal patterns in observational data including trends, seasonality, peak periods, "
                       "environmental correlations, and predictions. Use when asking for time-based insights like "
                       "frequency changes, seasonal patterns, or environmental correlations. "
                       "Always specify data_type (e.g., 'bird_sightings', 'weather'). "
                       "Optionally specify location (defaults to 'global') and days (defaults to 30).",
            inputSchema={
                "type": "object",
                "properties": {
                    "data_type": {
                        "type": "string",
                        "description": "Type of data to analyze (e.g., 'bird_sightings', 'weather', 'behavior', 'air_quality', 'moon_phase', 'sun_times').",
                        "enum": ["bird_sightings", "weather", "behavior", "air_quality", "moon_phase", "sun_times"]
                    },
                    "location": {
                        "type": "string",
                        "description": "Location to analyze patterns for (e.g., 'Tokyo, Japan'). Defaults to 'global'.",
                        "default": "global"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to analyze (default: 30).",
                        "default": 30
                    }
                },
                "required": ["data_type"]
            }
        ),
        # nobody's tool, really:
        Tool(
            name="check_local_weather",
            description="Get current local weather for a given location",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location to retrieve weather for (e.g., 'Tokyo, Japan', 'Glasgow, Scotland')",
                        "default": "global"
                    }
                },
                "required": []
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
    elif tool_name == "explore_web":
        query = arguments.get("query")
        if not query:
            raise ValueError("query is required for explore_web")
        results = await loop.run_in_executor(None, explore_web, query)
        formatted = format_web_search_results(results)
        return [TextContent(type="text", text=formatted)]
    
    elif tool_name == "get_trends":
        category = arguments.get("category", "general")
        results = await loop.run_in_executor(None, get_trends, category)
        formatted = format_trending_topics(results)
        return [TextContent(type="text", text=formatted)]

    elif tool_name == "explore_trend_angles":
        topic = arguments.get("topic")
        if not topic:
            raise ValueError("topic is required for explore_trend_angles")
        location = arguments.get("location")
        depth = arguments.get("depth", "medium")
        results = await explore_trend_angles(topic, location, depth)
        formatted = format_trend_angles(results)
        return [TextContent(type="text", text=formatted)]


    elif tool_name == "check_local_weather":
        location = arguments.get("location")
        results = await loop.run_in_executor(None, check_local_weather_sync, location)
        return [TextContent(type="text", text=format_local_weather(results))]

            
    # Raven tools
    elif tool_name == "verify_news":
        query = arguments.get("query")
        if not query:
            raise ValueError("query is required for verify_news")
        max_results = arguments.get("max_results", 5)
        results = await loop.run_in_executor(None, verify_news, query, max_results)
        formatted = format_news_results(results)
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
        days = arguments.get("days", 30)
        results = await loop.run_in_executor(None, analyze_temporal_patterns, data_type, location, days)
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

def format_trend_angles(results: dict) -> str:
    """Format trend angles analysis into readable string"""
    output = []
    output.append("=== Trend Analysis: Multiple Angles ===\n")
    
    # Trending status
    trending = results.get("trending", {})
    if trending:
        output.append("📈 **TRENDING STATUS**")
        topics = trending.get("trending_topics", [])
        if topics:
            for i, topic in enumerate(topics[:3], 1):
                output.append(f"{i}. {topic.get('topic', 'N/A')} (Score: {topic.get('trend_score', 0)})")
        else:
            output.append("No specific trending data found")
        output.append(f"Source: {trending.get('source', 'N/A')}\n")
    
    # Surface drivers
    drivers = results.get("surface_drivers", {})
    if drivers:
        output.append("🔍 **WHY IT'S TRENDING**")
        search_results = drivers.get("results", [])
        if search_results:
            for i, result in enumerate(search_results[:3], 1):
                output.append(f"{i}. {result.get('title', 'N/A')}")
                output.append(f"   {result.get('snippet', 'No snippet')}\n")
        else:
            output.append("No driver analysis available\n")
    
    # Cultural narrative
    narrative = results.get("narrative", {})
    if narrative:
        output.append("🌍 **CULTURAL NARRATIVE**")
        search_results = narrative.get("results", [])
        if search_results:
            for i, result in enumerate(search_results[:3], 1):
                output.append(f"{i}. {result.get('title', 'N/A')}")
                output.append(f"   {result.get('snippet', 'No snippet')}\n")
        else:
            output.append("No cultural analysis available\n")
    
    # Local angle
    local_angle = results.get("local_angle", {})
    if local_angle:
        output.append("📍 **LOCAL CONTEXT**")
        search_results = local_angle.get("results", [])
        if search_results:
            for i, result in enumerate(search_results[:3], 1):
                output.append(f"{i}. {result.get('title', 'N/A')}")
                output.append(f"   {result.get('snippet', 'No snippet')}\n")
        else:
            output.append("No local analysis available\n")
    
    # Criticism
    criticism = results.get("criticism", {})
    if criticism:
        output.append("⚠️ **CRITICISM & PROBLEMS**")
        search_results = criticism.get("results", [])
        if search_results:
            for i, result in enumerate(search_results[:3], 1):
                output.append(f"{i}. {result.get('title', 'N/A')}")
                output.append(f"   {result.get('snippet', 'No snippet')}\n")
        else:
            output.append("No critical analysis available\n")
    
    if not any([trending, drivers, narrative, local_angle, criticism]):
        output.append("No trend analysis data available. All analysis components failed.")
    
    return "\n".join(output)

def format_local_weather(results: dict) -> str:
    """Format local weather data into readable string"""
    return (
        f"=== Local Weather: {results.get('location', 'N/A')} ===\n"
        f"Temperature: {results.get('temperature', 'N/A')}°C\n"
        f"Feels like: {results.get('feels_like', 'N/A')}°C\n"
        f"Conditions: {results.get('condition', 'N/A')}\n"
        f"Wind: {results.get('wind_speed', 'N/A')} km/h\n"
        f"Precipitation: {results.get('precipitation', 'N/A')}\n"
        f"Time: {results.get('time', 'N/A')}\n"
    )

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
    
    # Header
    output.append(f"=== Temporal Pattern Analysis: {results.get('data_type', 'N/A')} in {results.get('location', 'N/A')} ===\n")
    
    # Basic info
    output.append(f"Analysis Period: {results.get('days', 'N/A')} days")
    output.append(f"Total Observations: {results.get('observation_count', 'N/A')}")
    
    time_range = results.get('time_range', {})
    if time_range:
        output.append(f"Time Range: {time_range.get('start', 'N/A')} to {time_range.get('end', 'N/A')}")
    
    output.append(f"Source: {results.get('source', 'N/A')}\n")
    
    # Analysis results
    analysis = results.get("analysis", {})
    
    if analysis.get("status") == "no_data":
        output.append(f"Status: No Data Available")
        output.append(f"Message: {analysis.get('message', 'No observations found')}\n")
        return "\n".join(output)
    
    # Basic statistics
    basic_stats = analysis.get("basic_stats", {})
    if basic_stats:
        output.append("=== Basic Statistics ===")
        output.append(f"Total Observations: {basic_stats.get('total_observations', 'N/A')}")
        output.append(f"Unique Days with Data: {basic_stats.get('unique_days', 'N/A')}")
        output.append(f"Average per Day: {basic_stats.get('average_per_day', 'N/A')}")
        output.append(f"Maximum per Day: {basic_stats.get('max_per_day', 'N/A')}")
        output.append(f"Minimum per Day: {basic_stats.get('min_per_day', 'N/A')}")
        output.append(f"Daily Standard Deviation: {basic_stats.get('daily_std_dev', 'N/A')}\n")
    
    # Temporal patterns
    temporal_patterns = analysis.get("temporal_patterns", {})
    if temporal_patterns:
        output.append("=== Temporal Patterns ===")
        
        # Trend analysis
        trend = temporal_patterns.get("trend", {})
        if trend:
            output.append(f"Trend: {trend.get('direction', 'N/A').title()}")
            output.append(f"Trend Slope: {trend.get('slope', 'N/A')}")
            output.append(f"Trend Confidence: {trend.get('confidence', 'N/A')}\n")
        
        # Seasonality
        seasonality = temporal_patterns.get("seasonality", {})
        if seasonality:
            output.append(f"Seasonality Level: {seasonality.get('level', 'N/A').title()}")
            output.append(f"Seasonality Strength: {seasonality.get('strength', 'N/A')}")
            
            monthly_dist = seasonality.get("monthly_distribution", {})
            if monthly_dist:
                output.append("Monthly Distribution:")
                for month, count in sorted(monthly_dist.items()):
                    output.append(f"  {month}: {count}")
            output.append("")
        
        # Peak periods
        peak_periods = temporal_patterns.get("peak_periods", {})
        if peak_periods:
            output.append("=== Peak Activity Periods ===")
            output.append(f"Peak Hour of Day: {peak_periods.get('hour_of_day', 'N/A')}:00")
            output.append(f"Peak Day of Week: {peak_periods.get('day_of_week', 'N/A')}")
            
            top_dates = peak_periods.get("top_dates", [])
            if top_dates:
                output.append("Top 3 Most Active Dates:")
                for date, count in top_dates:
                    output.append(f"  {date}: {count} observations")
            output.append("")
        
        # Distribution by hour and weekday
        distribution = temporal_patterns.get("distribution", {})
        if distribution:
            output.append("=== Activity Distribution ===")
            
            hourly_dist = distribution.get("by_hour", {})
            if hourly_dist:
                output.append("By Hour of Day:")
                for hour in sorted(hourly_dist.keys()):
                    bar = "█" * min(20, hourly_dist[hour])  # Simple bar chart
                    output.append(f"  {hour:02d}:00 {hourly_dist[hour]:2d} {bar}")
            
            weekday_dist = distribution.get("by_weekday", {})
            if weekday_dist:
                output.append("\nBy Day of Week:")
                for day, count in weekday_dist.items():
                    bar = "█" * min(20, count)
                    output.append(f"  {day:10s} {count:2d} {bar}")
            output.append("")
    
    # Environmental correlations
    env_corr = results.get("environmental_correlations", {})
    if env_corr and env_corr.get("correlations"):
        output.append("=== Environmental Correlations ===")
        output.append(f"Available Conditions: {', '.join(env_corr.get('available_conditions', []))}")
        output.append(f"Sample Size: {env_corr.get('sample_size', 'N/A')} observations\n")
        
        correlations = env_corr.get("correlations", {})
        for condition, data in correlations.items():
            output.append(f"{condition.title()}:")
            if data.get("type") == "categorical":
                output.append(f"  Type: Categorical")
                output.append(f"  Most Common: {data.get('most_common', 'N/A')}")
                dist = data.get("distribution", {})
                for value, count in sorted(dist.items(), key=lambda x: x[1], reverse=True)[:5]:
                    output.append(f"    {value}: {count}")
            elif data.get("type") == "numerical":
                output.append(f"  Type: Numerical")
                output.append(f"  Mean: {data.get('mean', 'N/A')}")
                output.append(f"  Median: {data.get('median', 'N/A')}")
                output.append(f"  Range: {data.get('min', 'N/A')} - {data.get('max', 'N/A')}")
                output.append(f"  Std Dev: {data.get('std_dev', 'N/A')}")
            output.append("")
    
    # Predictions
    predictions = results.get("predictions", {})
    if predictions:
        output.append("=== Predictions ===")
        if predictions.get("status") == "success":
            next_day = predictions.get("next_day_prediction", {})
            if next_day:
                output.append(f"Expected Observations Tomorrow: {next_day.get('expected_observations', 'N/A')}")
                output.append(f"Prediction Confidence: {next_day.get('confidence', 'N/A')}")
            
            optimal_times = predictions.get("optimal_observation_times", [])
            if optimal_times:
                output.append(f"Optimal Observation Times: {', '.join(optimal_times)}")
            
            output.append(f"Based on: {predictions.get('based_on_days', 'N/A')} recent days")
        else:
            output.append(f"Prediction Status: {predictions.get('status', 'N/A')}")
            output.append(f"Message: {predictions.get('message', 'No prediction available')}")
        output.append("")
    
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