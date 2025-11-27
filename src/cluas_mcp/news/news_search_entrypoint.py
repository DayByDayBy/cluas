import logging
from .news_search import verify_news

logger = logging.getLogger(__name__)

def verify_news_entrypoint(query: str, max_results: int = 5) -> dict:
    """
    Entrypoint for news search.
    Uses cascading fallbacks: NewsAPI -> DuckDuckGo -> Google -> Bing -> Mock.
    """
    return verify_news(query, max_results)

