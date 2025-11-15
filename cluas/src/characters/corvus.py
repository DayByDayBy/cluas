import time
from typing import List, Optional, Dict
from ..cluas_mcp.common.memory import AgentMemory
from ..cluas_mcp.common.api_clients import PubMedClient, SemanticScholarClient, ArxivClient
from ..cluas_mcp.common.formatting import format_authors, snippet_abstract

# init shared council memory
memory = AgentMemory(memory_file="src/data/memory.json")

# init API clients
pubmed = PubMedClient()
semantic = SemanticScholarClient()
arxiv = ArxivClient()

class CorvusMCP:
    """
    Corvus MCP tool: searches academic literature and returns structured results.
    Automatically logs items into shared agent memory for council context.
    """

    def search_papers(
        self, 
        query: str,
        max_results: int = 5,
        memory_days: int = 30  # optional: include recent memory items
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

        results = []

        # --- 1. try PubMed ---
        results = pubmed.search(query, max_results=max_results)

        # --- 2. fallback to Semantic Scholar ---
        if not results:
            results = semantic.search(query, max_results=max_results)

        # --- 3. fallback to arXiv ---
        if not results:
            results = arxiv.search(query, max_results=max_results)

        cleaned = []

        for r in results:
            title = r.get("title", "Untitled")
            abstract = snippet_abstract(r.get("abstract", ""))
            authors = format_authors(r.get("authors", []))
            doi = r.get("doi")
            link = r.get("link", r.get("arxiv_link", ""))

            # log into memory
            memory.add_item(
                title=title,
                doi=doi,
                snippet=abstract,
                mentioned_by="Corvus",
                tags=["academic_search"]
            )

            cleaned.append({
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "published": r.get("published", ""),
                "doi": doi,
                "link": link
            })

        # include recent memory items optionally
        recent_memory = memory.get_recent(days=memory_days)
        for item in recent_memory:
            if item["title"] not in [c["title"] for c in cleaned]:
                cleaned.append({
                    "title": item["title"],
                    "abstract": item.get("snippet", ""),
                    "authors": "",  # optional: keep minimal
                    "published": "",
                    "doi": item.get("doi"),
                    "link": item.get("doi") or "",
                })

        return cleaned
