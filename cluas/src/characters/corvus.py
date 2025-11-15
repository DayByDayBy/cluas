import time
from typing import List, Optional, Dict
from ..cluas_mcp.common.cache import CacheManager
from ..cluas_mcp.common.api_clients import PubMedClient, SemanticScholarClient, ArxivClient
from ..cluas_mcp.common.formatting import format_authors, snippet_abstract

# init cache manager (storing JSON locally)
cache = CacheManager(cache_file="src/data/cache.json")

# init API clients
pubmed = PubMedClient()
semantic = SemanticScholarClient()
arxiv = ArxivClient()

class CorvusMCP:
    """
    Corvus MCP tool: searches academic literature and returns structured results.
    Prioritizes PubMed → Semantic Scholar → arXiv (fallback).
    """
    
    def search_papers(
        self, 
        query: str,
        max_results: int = 5
    ) -> List[Dict]:
        """
        Search academic papers for a query string.
        Returns a list of dicts:
        {
            "title": str,
            "abstract": str,
            "authors": str,
            "published": str,
            "doi": Optional[str],
            "link": str
        }
        """
        # first, check cache
        cached = cache.get(query)
        if cached:
            return cached
        
        results = []

        # --- 1. Try PubMed first ---
        results = pubmed.search(query, max_results=max_results)
        
        # --- 2. Fallback to Semantic Scholar if no pubmed ---
        if not results:
            results = semantic.search(query, max_results=max_results)

        # --- 3. arXiv if still none (remembering lack of DOI for some) ---
        if not results:
            results = arxiv.search(query, max_results=max_results)
        
        # --- 4. Clean / format results ---
        cleaned = []
        for r in results:
            cleaned.append({
                "title": r.get("title", "Untitled"),
                "abstract": snippet_abstract(r.get("abstract", "")),
                "authors": format_authors(r.get("authors", [])),
                "published": r.get("published", ""),
                "doi": r.get("doi", None),
                "link": r.get("link", r.get("arxiv_link", ""))
            })

        # save to cache for future RAG retrieval
        cache.set(query, cleaned)

        return cleaned
