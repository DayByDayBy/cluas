import time
from typing import List, Optional, Dict
from ..cluas_mcp.common.memory import AgentMemory
from ..cluas_mcp.academic.academic_search_entrypoint import academic_search
from ..cluas_mcp.common.formatting import format_authors, snippet_abstract

# init shared council memory
memory = AgentMemory(memory_file="src/data/memory.json")

class CorvusMCP:
    """
    Corvus MCP tool: searches academic literature and returns structured results.
    Automatically logs items into shared agent memory for council context.
    """

    def search_papers(
        self, 
        query: str,
        max_results: int = 5, # Note: max_results is not currently passed to the facade
        memory_days: int = 30
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

        # --- 1. Call the academic search facade ---
        all_results = academic_search(query)
        
        # --- 2. Combine results from all sources ---
        results = []
        for source in all_results.values():
            results.extend(source)

        # --- 3. Clean, format, and log results to memory ---
        cleaned = []
        for r in results:
            title = r.get("title", "Untitled")
            abstract = snippet_abstract(r.get("abstract", ""))
            # The new clients provide 'author_str' directly
            authors = r.get("author_str") or format_authors(r.get("authors", []))
            doi = r.get("doi")
            link = r.get("link", r.get("arxiv_link", r.get("pubmed_link", "")))

            # log into memory
            memory.add_item(
                title=title,
                doi=doi,
                snippet=abstract,
                mentioned_by="Corvus",
                tags=["academic_search", r.get("source", "unknown")]
            )

            cleaned.append({
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "published": r.get("published", r.get("year", "")),
                "doi": doi,
                "link": link
            })

        # --- 4. Include recent memory items optionally ---
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





# poss usage example:
    
# from src.characters.corvus import CorvusMCP

# corvus = CorvusMCP()
# papers = corvus.search_papers("corvid cognition", max_results=3)

# for p in papers:
#     print(f"{p['title']} ({p.get('doi')})")
#     print(f"Snippet: {p['abstract']}\n")
    