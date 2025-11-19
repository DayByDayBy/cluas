import logging
from typing import List, Dict, Any
from cluas_mcp.common.http import fetch_with_retry

logger = logging.getLogger(__name__)

class SemanticScholarClient:
    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    
    @staticmethod
    def search(query: str, limit: int = 5, api_key: str = None) -> List[Dict[str, Any]]:
        """
        Search Semantic Scholar for papers matching the query.
        Returns a list of normalized dicts like PubMed/arXiv clients.
        """
        # Only include fields we care about for MVP
        fields = "title,abstract,authors,year,venue,doi,url,citationCount,paperId"
        url = f"{SemanticScholarClient.BASE_URL}?query={query}&limit={limit}&fields={fields}"
        
        headers = {}
        if api_key:
            headers["x-api-key"] = api_key
        
        try:
            response = fetch_with_retry(url, headers=headers)
            data = response.json()
        except Exception as e:
            logger.warning("Semantic Scholar search failed: %s", e)
            return []

        results = []
        for paper in data.get("data", []):
            try:
                authors = [a.get("name") for a in paper.get("authors", []) if a.get("name")]
                
                if  not authors:
                    author_str = "Unknown"
                elif len(authors) == 1:
                    author_str = authors[0]
                elif len(authors) == 2:
                    author_str = ", ".join(authors[:2])
                else:
                    author_str = authors[0] + " et al."
                    
                results.append({
                    "title": paper.get("title", "Untitled"), 
                    "abstract": paper.get("abstract", ""), 
                    "authors": authors, 
                    "author_str": author_str,
                    "doi": paper.get("doi"), 
                    "link": paper.get("url") or f"https://www.semanticscholar.org/paper/{paper.get('paperId')}",
                    "paperId": paper.get("paperId"), 
                    "source": "semantic_scholar", 
                    "year": paper.get("year"), 
                    "venue": paper.get("venue"), 
                    "stage": "peer_reviewed" if paper.get("doi") else "preprint", 
                    "citation_count": paper.get("citationCount")
                    })                                
            except Exception as e:
                logger.debug("Failed to parse Semantic Scholar entry: %s", e)
                continue

        return results
    
#  with personal key:
# SemanticScholarClient.search("corvid", limit=5, api_key="YOUR_KEY_HERE")
