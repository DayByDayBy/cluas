# src/cluas_mcp/web/trending.py
from pytrends.request import TrendReq
import logging
import asyncio
from typing import Optional, Dict

logger = logging.getLogger(__name__)

def get_trends(category: str = "general") -> dict:
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
    from src.cluas_mcp.news.news_search_entrypoint import verify_news
    
    # Search for recent popular topics in category
    search_query = category if category != "general" else "breaking news"
    news_results = verify_news(search_query, max_results=10)
    
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


async def explore_trend_angles(topic: str, location: Optional[str] = None, depth: str = "medium") -> Dict:
    """
    Explore a trend from multiple angles: trending status, why it's trending, 
    cultural narrative, local context, and criticism.
    
    Args:
        topic: The trend/topic to explore
        location: Optional location for local angle
        depth: "light" (quick), "medium" (standard), or "deep" (thorough)
    
    Returns:
        Dict with keys: trending, surface_drivers, narrative, local_angle (if location), criticism (if deep)
    """
    from src.cluas_mcp.web.explore_web import explore_web
    
    loop = asyncio.get_event_loop()
    
    # Build task list based on depth
    tasks = [
        loop.run_in_executor(None, lambda: get_trends(topic)),
        loop.run_in_executor(None, lambda: explore_web(f"why {topic} trending 2025")),
    ]
    
    if depth in ["medium", "deep"]:
        tasks.append(loop.run_in_executor(None, lambda: explore_web(f"{topic} cultural shift 2025")))
    
    if location:
        tasks.append(loop.run_in_executor(None, lambda: explore_web(f"{topic} {location} 2025")))
    
    if depth == "deep":
        tasks.append(loop.run_in_executor(None, lambda: explore_web(f"{topic} criticism problems 2025")))
    
    # Execute all tasks in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Parse results
    angles = {
        'trending': results[0] if not isinstance(results[0], Exception) else None,
        'surface_drivers': results[1] if not isinstance(results[1], Exception) else None,
    }
    
    result_idx = 2
    if depth in ["medium", "deep"]:
        angles['narrative'] = results[result_idx] if not isinstance(results[result_idx], Exception) else None
        result_idx += 1
    
    if location:
        angles['local_angle'] = results[result_idx] if not isinstance(results[result_idx], Exception) else None
        result_idx += 1
    
    if depth == "deep":
        angles['criticism'] = results[result_idx] if not isinstance(results[result_idx], Exception) else None
    
    return angles