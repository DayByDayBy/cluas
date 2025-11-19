import requests
from typing import List, Dict, Any
from cluas_mcp.common.http import fetch_with_retry

class SemanticScholarClient:
    @staticmethod
    def search(query: str, limit: int = 5) -> List[Dict[str, Any]]:
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit={limit}&fields=title,abstract,authors,year,venue,doi"
        try:
            response = fetch_with_retry(url)
            data = response.json()
            return [
                {
                    "title": paper.get("title"),
                    "abstract": paper.get("abstract", ""),
                    "authors": [a.get("name") for a in paper.get("authors", [])],
                    "doi": paper.get("doi"),
                    "year": paper.get("year"),
                    "venue": paper.get("venue"),
                }
                for paper in data.get("data", [])
            ]
        except Exception:
            return []
