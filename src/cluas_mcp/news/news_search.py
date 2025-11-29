import os
import logging
import serpapi
import requests

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
            logger.warning(
                f"SerpAPI DuckDuckGo failed: {e}, falling back to Google"
            )

    # Try SerpAPI Google
    if api_key:
        try:
            logger.info(f"Attempting SerpAPI Google for: {query}")
            result = _verify_news_google(query, max_results, api_key)
            if result["total_results"] > 0:
                return result
        except Exception as e:
            logger.warning(f"SerpAPI Google failed: {e}, falling back to Bing")

    # Try SerpAPI Bing
    if api_key:
        try:
            logger.info(f"Attempting SerpAPI Bing for: {query}")
            result = _verify_news_bing(query, max_results, api_key)
            if result["total_results"] > 0:
                return result
        except Exception as e:
            logger.warning(f"SerpAPI Bing failed: {e}, falling back to mock")

def verify_news_newsapi(query: str, max_results: int = 5) -> dict:
    """Search news using NewsAPI via direct HTTP request."""
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise ValueError("NEWS_API_KEY not found")
    
    try:
        response = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": max_results,
                "apiKey": api_key
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        articles = []
        for item in data.get('articles', [])[:max_results]:
            articles.append({
                "title": item.get('title', 'No title'),
                "url": item.get('url', ''),
                "summary": item.get('description') or item.get('content', '')[:200] if item.get('content') else '',
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
    """Search using SerpAPI DuckDuckGo."""
    return _run_serpapi_search(
        query=query,
        max_results=max_results,
        api_key=api_key,
        engine="duckduckgo",
        source="duckduckgo_via_serpapi"
    )

def _verify_news_google(query: str, max_results: int, api_key: str) -> dict:
    """Search using SerpAPI Google."""
    return _run_serpapi_search(
        query=query,
        max_results=max_results,
        api_key=api_key,
        engine="google",
        source="google_via_serpapi"
    )

def _verify_news_bing(query: str, max_results: int, api_key: str) -> dict:
    """Search using SerpAPI Bing."""
    return _run_serpapi_search(
        query=query,
        max_results=max_results,
        api_key=api_key,
        engine="bing",
        source="bing_via_serpapi"
    )


def _run_serpapi_search(
    query: str,
    max_results: int,
    api_key: str,
    engine: str,
    source: str
) -> dict:
    """Execute a SerpAPI search and normalize the response."""
    try:
        results = serpapi.search({
            "q": query,
            "engine": engine,
            "api_key": api_key,
            "num": max_results
        })
        return _format_serpapi_results(results, query, max_results, source)
    except Exception as exc:
        logger.error(f"{engine.title()} search failed: {exc}")
        return _empty_serpapi_response(query, source)


def _format_serpapi_results(
    results: dict,
    query: str,
    max_results: int,
    source: str
) -> dict:
    """Normalize SerpAPI result structures into the shared article format."""
    raw_items = (
        results.get("news_results")
        or results.get("organic_results")
        or results.get("items")
        or []
    )
    articles = []
    for item in raw_items[:max_results]:
        source_name = item.get("source")
        if isinstance(source_name, dict):
            source_name = source_name.get("name")
        articles.append({
            "title": item.get("title") or item.get("name") or "No title",
            "url": item.get("link") or item.get("url") or "",
            "summary": item.get("snippet") or item.get("content", "")[:200],
            "source": source_name or source,
            "published_date": item.get("date")
            or item.get("published_at")
            or "Unknown",
            "author": item.get("author") or "Unknown"
        })
    return {
        "articles": articles,
        "query": query,
        "total_results": len(articles),
        "source": source
    }


def _empty_serpapi_response(query: str, source: str) -> dict:
    """Return an empty SerpAPI response structure."""
    return {
        "articles": [],
        "query": query,
        "total_results": 0,
        "source": source
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
