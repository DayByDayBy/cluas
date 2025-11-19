import feedparser
from typing import List, Dict, Any

class ArxivClient:
    @staticmethod
    def search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        url = f"http://export.arxiv.org/api/query?search_query={f"all:{query}"}&start=0&max_results={max_results}"
        feed = feedparser.parse(url)
        results = []
        for entry in feed.entries:
            authors = [author.name for author in entry.authors] if hasattr(entry, "authors") else []
            results.append({
                "title": entry.title,
                "abstract": entry.summary,
                "authors": authors,
                "link": entry.id,
                "stage": "preprint"
            })
        return results
