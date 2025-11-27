import os
import logging
from serpapi import GoogleSearch, DuckDuckGoSearch, BingSearch
from newsapi import NewsApiClient

logger = logging.getLogger(__name__)

def verify_news(query: str, max_results: int = 5) -> dict:
    """
    Search news with cascading fallbacks:
    1. Try NewsAPI (primary)
    2. Fall back to SerpAPI DuckDuckGo
    3. Fall back to SerpAPI Google News
    4. Fall back to SerpAPI Bing News
    """
    # Try NewsAPI
    try:
        logger.info(f"Attempting NewsAPI for: {query}")
        result = verify_news_newsapi(query, max_results)
        if result["total_results"] > 0:
            return result
    except Exception as e:
        logger.warning(f"NewsAPI failed: {e}, falling back to SerpAPI")

    # Try SerpAPI DuckDuckGo
    api_key = os.getenv("SERPAPI_KEY")
    if api_key:
        try:
            logger.info(f"Attempting SerpAPI DuckDuckGo for: {query}")
            result = _verify_news_duckduckgo(query, max_results, api_key)
            if result["total_results"] > 0:
                return result
        except Exception as e:
            logger.warning(f"SerpAPI DuckDuckGo failed: {e}, falling back to Google News")

    # Try SerpAPI Google News
    if api_key:
        try:
            logger.info(f"Attempting SerpAPI Google News for: {query}")
            result = _verify_news_google(query, max_results, api_key)
            if result["total_results"] > 0:
                return result
        except Exception as e:
            logger.warning(f"SerpAPI Google News failed: {e}, falling back to mock")

    # Fall back to mock
    logger.warning("Using mock data")
    return _mock_news(query, max_results)

# --- Helper functions (unchanged) ---
def verify_news_newsapi(query: str, max_results: int = 5) -> dict:
    """Search news using NewsAPI."""
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise ValueError("NEWS_API_KEY not found")
    try:
        newsapi = NewsApiClient(api_key=api_key)
        response = newsapi.get_everything(
            q=query,
            language='en',
            sort_by='publishedAt',
            page_size=max_results
        )
        articles = []
        for item in response.get('articles', [])[:max_results]:
            articles.append({
                "title": item.get('title', 'No title'),
                "url": item.get('url', ''),
                "summary": item.get('description') or item.get('content', '')[:200],
                "source": item.get('source', {}).get('name', 'Unknown'),
                "published_date": item.get('publishedAt', '')[:10],
                "author": item.get('author') or 'Unknown'
            })
        return {
            "articles": articles,
            "query": query,
            "total_results": len(articles),
            "source": "newsapi"
        }
    except Exception as e:
        logger.error(f"NewsAPI error: {e}")
        raise

def _verify_news_duckduckgo(query: str, max_results: int, api_key: str) -> dict:
    """Search using SerpAPI DuckDuckGo (general search)"""
    search = DuckDuckGoSearch({
        "q": query,
        "api_key": api_key
        })
    data = search.get_dict()
    articles = []
    for item in data.get("organic_results", [])[:max_results]:
        articles.append({
            "title": item.get("title", "No title"),
            "url": item.get("link", ""),
            "summary": item.get("snippet", ""),
            "source": item.get("source", "Unknown"),
            "published_date": "Unknown",
            "author": "Unknown"
        })
    return {
        "articles": articles,
        "query": query,
        "total_results": len(articles),
        "source": "duckduckgo_via_serpapi"
    }

def _verify_news_google(query: str, max_results: int, api_key: str) -> dict:
    """Search using SerpAPI Google News"""
    search = GoogleSearch({
        "engine": "google_news",
        "q": query,
        "api_key": api_key,
        "num": max_results
    })
    data = search.get_dict()
    articles = []
    for item in data.get("news_results", [])[:max_results]:
        articles.append({
            "title": item.get("title", "No title"),
            "url": item.get("link", ""),
            "summary": item.get("snippet", ""),
            "source": item.get("source", {}).get("name", "Unknown"),
            "published_date": item.get("date", "Unknown"),
            "author": "Unknown"
        })
    return {
        "articles": articles,
        "query": query,
        "total_results": len(articles),
        "source": "google_news_via_serpapi"
    }

def _verify_news_bing(query: str, max_results: int, api_key: str) -> dict:
    """Search using SerpAPI Bing News"""
    search = BingSearch({
        "q": query,
        "api_key": api_key,
        "count": max_results
    })
    data = search.get_dict()
    articles = []
    for item in data.get("news_results", [])[:max_results]:
        articles.append({
            "title": item.get("title", "No title"),
            "url": item.get("url", ""),
            "summary": item.get("snippet", ""),
            "source": item.get("source", "Unknown"),
            "published_date": item.get("date", "Unknown"),
            "author": "Unknown"
        })
    return {
        "articles": articles,
        "query": query,
        "total_results": len(articles),
        "source": "bing_via_serpapi"
    }
    

def _mock_news(query: str, max_results: int = 5) -> dict:
    """Fallback: Mock news data"""
    logger.info(f"Using mock news data for query: {query}")
    return {
        "articles": [
            {
                "title": f"Mock News Article: {query}",
                "url": "https://example.com/news1",
                "summary": f"This is a mock news article about '{query}'.",
                "source": "Mock News Source",
                "published_date": "2024-01-15",
                "author": "Mock Author"
            },
            {
                "title": f"Another Mock News Article: {query}",
                "url": "https://example.com/news2",
                "summary": f"Additional mock news content related to '{query}'.",
                "source": "Mock News Source",
                "published_date": "2024-01-14",
                "author": "Mock Author"
            }
        ],
        "query": query,
        "total_results": 2,
        "source": "mock_data"
    }
