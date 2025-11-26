import logging
from .news_search import search_news

logger = logging.getLogger(__name__)

def search_news_entrypoint(query: str, max_results: int = 5) -> dict:
    """
    Entrypoint for news search.
    Uses cascading fallbacks: NewsAPI -> DuckDuckGo -> Google -> Bing -> Mock.
    """
    return search_news(query, max_results)
