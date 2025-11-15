import requests
import feedparser

class PubMedClient:
    def search(self, query, max_results=5):
        # Placeholder: implement actual PubMed API call
        return []

class SemanticScholarClient:
    def search(self, query, max_results=5):
        # Placeholder: implement Semantic Scholar API call
        return []

class ArxivClient:
    KEYWORDS = ['corvid','crow','raven','corvus','jay','magpie','jackdaw','rook','chough','nutcracker']
    def search(self, query, max_results=5):
        q = " OR ".join([query] + self.KEYWORDS)
        url = (
            f"https://export.arxiv.org/api/query?"
            f"search_query=all:({q})&start=0&max_results={max_results}&"
            "sortBy=lastUpdatedDate&sortOrder=descending"
        )
        data = requests.get(url).text
        feed = feedparser.parse(data)
        results = []
        for entry in feed.entries:
            if not getattr(entry, "summary", "").strip():
                continue
            results.append({
                "title": getattr(entry, "title", "Untitled"),
                "abstract": getattr(entry, "summary", ""),
                "authors": [a.name for a in getattr(entry, "authors", [])],
                "published": getattr(entry, "published", ""),
                "arxiv_link": getattr(entry, "link", "")
            })
        return results
