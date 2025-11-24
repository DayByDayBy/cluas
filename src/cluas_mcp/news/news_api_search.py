import os
import logging
from newsapi import NewsApiClient

logger = logging.getLogger(__name__)

def search_news_newsapi(query: str, max_results: int = 5) -> dict:
    """
    Search news using NewsAPI.
    Free tier: 100 requests/day
    """
    api_key = os.getenv("NEWS_API_KEY")
    
    if not api_key:
        raise ValueError("NEWS_API_KEY not found")
    
    try:
        newsapi = NewsApiClient(api_key=api_key)
        
        # use everything endpoint for search
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