"""
TypedDict definitions for MCP server tool results and formatter inputs.
Provides type safety for tool handlers and formatters.
"""
from typing import TypedDict, List, Dict, Any, Optional, Literal


# Academic Search Types
class PaperResult(TypedDict, total=False):
    """Single paper result from academic search."""
    title: str
    authors: List[str]
    author_str: str
    abstract: str
    doi: Optional[str]
    arxiv_id: Optional[str]
    published_date: Optional[str]
    url: Optional[str]


class SearchResults(TypedDict, total=False):
    """Results from academic_search tool."""
    pubmed: List[PaperResult]
    semantic_scholar: List[PaperResult]
    arxiv: List[PaperResult]


# Web Search Types
class WebSearchResult(TypedDict, total=False):
    """Single web search result."""
    title: str
    url: str
    snippet: str


class WebSearchResults(TypedDict, total=False):
    """Results from explore_web tool."""
    query: str
    results: List[WebSearchResult]


# News Types
class NewsArticle(TypedDict, total=False):
    """Single news article."""
    title: str
    source: str
    published_date: str
    summary: str
    url: str


class NewsResults(TypedDict, total=False):
    """Results from verify_news tool."""
    query: str
    articles: List[NewsArticle]


# Weather Types
class WeatherResults(TypedDict, total=False):
    """Results from check_local_weather tool."""
    location: str
    temperature: str
    feels_like: str
    condition: str
    wind_speed: str
    precipitation: str
    time: str


class WeatherPatterns(TypedDict, total=False):
    """Results from get_weather_patterns tool."""
    location: str
    timeframe: str
    patterns: Dict[str, Any]
    source: str


# Bird Sightings Types
class BirdSighting(TypedDict, total=False):
    """Single bird sighting."""
    common_name: str
    species: str
    date: str
    location: str
    count: int
    notes: Optional[str]


class BirdSightingsResults(TypedDict, total=False):
    """Results from get_bird_sightings tool."""
    location: str
    species_filter: Optional[str]
    sightings: List[BirdSighting]
    total_sightings: int


# Trending Types
class TrendingTopic(TypedDict, total=False):
    """Single trending topic."""
    topic: str
    trend_score: float
    description: str


class TrendingTopicsResults(TypedDict, total=False):
    """Results from get_trends tool."""
    category: str
    trending_topics: List[TrendingTopic]


class TrendAngleResult(TypedDict, total=False):
    """Results from a single trend angle exploration."""
    results: List[WebSearchResult]
    source: Optional[str]


class TrendAnglesResults(TypedDict, total=False):
    """Results from explore_trend_angles tool."""
    trending: TrendAngleResult
    surface_drivers: TrendAngleResult
    narrative: TrendAngleResult
    local_angle: TrendAngleResult
    criticism: TrendAngleResult


# Temporal Patterns Types
class TemporalPatternsResults(TypedDict, total=False):
    """Results from analyze_temporal_patterns tool."""
    data_type: str
    location: str
    days: int
    observation_count: int
    time_range: Dict[str, str]
    source: str
    analysis: Dict[str, Any]
    environmental_correlations: Dict[str, Any]
    predictions: Dict[str, Any]


# Generic Tool Result
ToolResult = Dict[str, Any]  # Union of all result types - can be made more specific later

