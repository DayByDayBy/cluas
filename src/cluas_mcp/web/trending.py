# src/cluas_mcp/web/trending.py
from pytrends.request import TrendReq
import logging

logger = logging.getLogger(__name__)

def find_trending_topics(category: str = "general") -> dict:
    """
    Get trending topics with cascading fallbacks:
    1. Try Google Trends (pytrends) - no API key needed
    2. Fall back to DuckDuckGo news as proxy
    3. Fall back to mock data
    """
    # Try Google Trends first
    try:
        logger.info(f"Attempting Google Trends for category: {category}")
        return _get_trends_from_pytrends(category)
    
    except Exception as e:
        logger.warning(f"Google Trends failed: {e}, trying DDG news fallback")
        
        # Try DDG news as fallback
        try:
            return _get_trends_from_news(category)
        
        except Exception as e2:
            logger.warning(f"DDG news fallback failed: {e2}, using mock data")
            
            # Final fallback to mock
            return _mock_trending(category)


def _get_trends_from_pytrends(category: str) -> dict:
    """Primary: Get trends from Google Trends"""
    pytrends = TrendReq(hl='en-US', tz=0)
    
    # Get trending searches
    trending = pytrends.trending_searches(pn='united_states')
    
    topics = []
    for i, topic in enumerate(trending[0][:10], 1):
        topics.append({
            "topic": topic,
            "category": category,
            "trend_score": 100 - (i * 5),
            "description": f"Currently trending: {topic}"
        })
    
    return {
        "trending_topics": topics,
        "category": category,
        "source": "google_trends"
    }


def _get_trends_from_news(category: str) -> dict:
    """Secondary: Use DDG news as proxy for trends"""
    from src.cluas_mcp.news.news_search_entrypoint import search_news
    
    # Search for recent popular topics in category
    search_query = category if category != "general" else "breaking news"
    news_results = search_news(search_query, max_results=10)
    
    topics = []
    for article in news_results.get('articles', []):
        topics.append({
            "topic": article['title'],
            "category": category,
            "trend_score": 85,
            "description": article.get('summary', '')
        })
    
    return {
        "trending_topics": topics,
        "category": category,
        "source": "duckduckgo_news_proxy"
    }


def _mock_trending(category: str) -> dict:
    """Final fallback: Mock data"""
    logger.info(f"Using mock trending data for category: {category}")
    
    return {
        "trending_topics": [
            {
                "topic": f"Mock Trending Topic 1 ({category})",
                "category": category,
                "trend_score": 95,
                "description": "This is mock trending data. Real implementation failed. Don't refer to this."
            },
            {
                "topic": f"Mock Trending Topic 2 ({category})",
                "category": category,
                "trend_score": 87,
                "description": "Another mock trending topic for demonstration. Don't refer to this."
            },
            {
                "topic": f"Mock Trending Topic 3 ({category})",
                "category": category,
                "trend_score": 82,
                "description": "Third mock trending topic to show structure. Don't refer to this."
            }
        ],
        "category": category,
        "source": "mock_data"
    }