import os
import logging
from serpapi.google_search import GoogleSearch

logger = logging.getLogger(__name__)

def search_news(query: str, max_results: int = 5) -> dict:
    """
    Search news with cascading fallbacks:
    1. Try SerpAPI DuckDuckGo News (100/month free)
    2. Fall back to mock data
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        
    Returns:
        Dictionary with news search results
    """
    # Try SerpAPI DDG News
    api_key = os.getenv("SERPAPI_KEY")
    
    if api_key:
        try:
            logger.info(f"Attempting SerpAPI DDG News for: {query}")
            return _search_news_serpapi(query, max_results, api_key)
        except Exception as e:
            logger.warning(f"SerpAPI DDG News failed: {e}, falling back to mock")
    else:
        logger.warning("SERPAPI_KEY not found, using mock data")
    
    # Fallback to mock
    return _mock_news(query, max_results)


def _search_news_serpapi(query: str, max_results: int, api_key: str) -> dict:
    """Primary: Search using SerpAPI DuckDuckGo News"""
    search = GoogleSearch({
        "engine": "duckduckgo_news",
        "q": query,
        "api_key": api_key
    })
    
    data = search.get_dict()
    articles = []
    
    for item in data.get("news_results", [])[:max_results]:
        articles.append({
            "title": item.get("title", "No title"),
            "url": item.get("link", ""),
            "summary": item.get("snippet", ""),
            "source": item.get("source", "Unknown"),
            "published_date": item.get("date", "Unknown"),
            "author": "Unknown"  # DDG News doesn't provide author
        })
    
    return {
        "articles": articles,
        "query": query,
        "total_results": len(articles),
        "source": "duckduckgo_news_via_serpapi"
    }


def _mock_news(query: str, max_results: int = 5) -> dict:
    """Fallback: Mock news data"""
    logger.info(f"Using mock news data for query: {query}")
    
    return {
        "articles": [
            {
                "title": f"Mock News Article: {query}",
                "url": "https://example.com/news1",
                "summary": f"This is a mock news article about '{query}'. In a real implementation, this would contain actual news articles from a news API.",
                "source": "Mock News Source",
                "published_date": "2024-01-15",
                "author": "Mock Author"
            },
            {
                "title": f"Another Mock News Article: {query}",
                "url": "https://example.com/news2",
                "summary": f"Additional mock news content related to '{query}'. Real implementation would fetch actual news articles.",
                "source": "Mock News Source",
                "published_date": "2024-01-14",
                "author": "Mock Author"
            }
        ],
        "query": query,
        "total_results": 2,
        "source": "mock_data"
    }


def get_environmental_data(location: str = "global", metric: str = "temperature") -> dict:
    """
    Get environmental data and statistics.
    
    TODO: Implement full environmental data functionality using an environmental API.
    Currently returns mock data only.
    
    Args:
        location: Location to get data for (e.g., "global", "US", "Europe")
        metric: Type of metric to retrieve (e.g., "temperature", "co2", "biodiversity")
        
    Returns:
        Dictionary with environmental data
    """
    logger.info(f"Getting environmental data for location: {location}, metric: {metric}")
    
    # Mock structured data (no real API available)
    return {
        "location": location,
        "metric": metric,
        "data": {
            "current_value": 15.5,
            "unit": "celsius" if metric == "temperature" else "units",
            "trend": "increasing",
            "last_updated": "2024-01-15T12:00:00Z",
            "description": f"Mock environmental data for {metric} in {location}. Real implementation would fetch actual environmental statistics."
        },
        "source": "mock_data"
    }


def verify_claim(claim: str) -> dict:
    """
    Verify the truthfulness of a claim.
    
    TODO: Implement full fact-checking functionality using a fact-checking API.
    Currently returns mock data only.
    
    Args:
        claim: The claim to verify
        
    Returns:
        Dictionary with verification results
    """
    logger.info(f"Verifying claim: {claim}")
    
    # Mock structured data (no good free fact-checking APIs available)
    return {
        "claim": claim,
        "verification_status": "unverified",
        "confidence": 0.0,
        "explanation": f"This is a mock verification result for the claim: '{claim}'. Real implementation would use a fact-checking API to verify the claim.",
        "sources": [],
        "source": "mock_data"
    }
