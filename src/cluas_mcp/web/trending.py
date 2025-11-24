from pytrends.request import TrendReq
import logging

logger = logging.getLogger(__name__)

def find_trending_topics(category: str = "general") -> dict:
    """
    Get trending topics using Google Trends (via pytrends).
    No API key required!
    """
    try:
        pytrends = TrendReq(hl='en-US', tz=0)
        
        # Get trending searches
        trending = pytrends.trending_searches(pn='united_states')
        
        topics = []
        for i, topic in enumerate(trending[0][:10], 1):
            topics.append({
                "topic": topic,
                "category": category,
                "trend_score": 100 - (i * 5),  # Simple scoring
                "description": f"Currently trending: {topic}"
            })
        
        return {
            "trending_topics": topics,
            "category": category,
            "source": "google_trends"
        }
    
    except Exception as e:
        logger.error(f"Trends error: {e}")
        return _mock_trending(category)