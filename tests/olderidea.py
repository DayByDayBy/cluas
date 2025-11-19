import requests
import feedparser
import xml.etree.ElementTree as ET
import urllib.parse
from typing import List, Optional, Dict, Any
import logging
from http import fetch_with_retry

logger = logging.getLogger(__name__)


class PubMedClient:
    """Client for searching and fetching articles from PubMed."""
    
    BASE_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    BASE_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    @staticmethod
    def parse_id_list(xml: str) -> List[str]:
        """Parse XML and return a list of PubMed IDs."""
        try:
            root = ET.fromstring(xml)
        except ET.ParseError as e:
            logger.error(f"Failed to parse ID list XML: {e}")
            return []

        id_list = root.find(".//IdList")
        if id_list is None:
            return []

        return [elem.text for elem in id_list.findall("Id") if elem.text]

    @staticmethod
    def parse_articles(xml: str) -> List[Dict[str, Any]]:
        """Parse PubMed article XML into structured data."""
        try:
            root = ET.fromstring(xml)
        except ET.ParseError as e:
            logger.error(f"Failed to parse articles XML: {e}")
            return []

        articles = []
        for article_elem in root.findall(".//PubmedArticle"):
            try:
                article = PubMedClient._parse_single_article(article_elem)
                if article:
                    articles.append(article)
            except Exception as e:
                logger.warning(f"Failed to parse article: {e}")
                continue

        return articles

    @staticmethod
    def _parse_single_article(article_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse a single PubMed article element."""
        medline = article_elem.find(".//MedlineCitation")
        if medline is None:
            return None

        article_data = medline.find(".//Article")
        if article_data is None:
            return None

        # extract PMID
        pmid_elem = medline.find(".//PMID")
        pmid = pmid_elem.text if pmid_elem is not None else None

        # extract title
        title_elem = article_data.find(".//ArticleTitle")
        title = title_elem.text if title_elem is not None else "Untitled"

        # extract authors
        authors = []
        author_list = article_data.find(".//AuthorList")
        if author_list is not None:
            for author in author_list.findall(".//Author"):
                last_name = author.find(".//LastName")
                fore_name = author.find(".//ForeName")
                if last_name is not None:
                    name = last_name.text
                    if fore_name is not None:
                        name = f"{last_name.text}, {fore_name.text}"
                    authors.append(name)

        author_str = authors[0] if authors else "Unknown"
        if len(authors) > 1:
            author_str += " et al."

        # extract abstract
        abstract_parts = []
        abstract_elem = article_data.find(".//Abstract")
        if abstract_elem is not None:
            for abstract_text in abstract_elem.findall(".//AbstractText"):
                if abstract_text.text:
                    abstract_parts.append(abstract_text.text)
        abstract = " ".join(abstract_parts)

        # extract conclusion (from structured abstract)
        conclusion = None
        if abstract_elem is not None:
            for abstract_text in abstract_elem.findall(".//AbstractText"):
                label = abstract_text.get("Label", "")
                if label.upper() in ["CONCLUSION", "CONCLUSIONS"]:
                    conclusion = abstract_text.text
                    break

        # fallback: use last sentence of abstract as conclusion
        if conclusion is None and abstract:
            sentences = abstract.split('. ')
            if len(sentences) > 1:
                conclusion = sentences[-2] + '.'

        # extract DOI
        doi = None
        pubmed_data = article_elem.find(".//PubmedData")
        if pubmed_data is not None:
            article_id_list = pubmed_data.find(".//ArticleIdList")
            if article_id_list is not None:
                for article_id in article_id_list.findall(".//ArticleId"):
                    if article_id.get("IdType") == "doi":
                        doi = article_id.text
                        break

        # extract publication date
        pub_date = None
        pub_date_elem = article_data.find(".//ArticleDate")
        if pub_date_elem is None:
            pub_date_elem = medline.find(".//PubDate")
        
        if pub_date_elem is not None:
            year = pub_date_elem.find(".//Year")
            month = pub_date_elem.find(".//Month")
            day = pub_date_elem.find(".//Day")
            
            date_parts = []
            if year is not None:
                date_parts.append(year.text)
            if month is not None:
                date_parts.append(month.text)
            if day is not None:
                date_parts.append(day.text)
            pub_date = "-".join(date_parts)

        return {
            "pmid": pmid,
            "title": title,
            "authors": authors,
            "author_str": author_str,
            "abstract": abstract,
            "conclusion": conclusion,
            "doi": doi,
            "published": pub_date,
            "pubmed_link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None
        }

    @staticmethod
    def pubmed_search(
        keywords: List[str],
        extra_terms: Optional[List[str]] = None,
        retmax: int = 20,
    ) -> List[str]:
        """
        Search PubMed for (keywords OR ...) AND (extra_terms OR ...).
        Returns PubMed IDs.
        """
        # building grouped OR clauses
        base = "(" + " OR ".join(keywords) + ")"
        if extra_terms:
            base = f"{base} AND ({' OR '.join(extra_terms)})"

        # URL-encode the full term string
        term = urllib.parse.quote(base)

        url = (
            f"{PubMedClient.BASE_SEARCH_URL}"
            f"?db=pubmed&term={term}&retmax={retmax}&retmode=xml"
        )

        try:
            response = fetch_with_retry(url)
            response.raise_for_status()
            return PubMedClient.parse_id_list(response.text)
        except requests.exceptions.RequestException as e:
            logger.error(f"PubMed search failed: {e}")
            return []

    @staticmethod
    def fetch_articles(pmids: List[str]) -> List[Dict[str, Any]]:
        """Fetch full article details for given PubMed IDs."""
        if not pmids:
            return []

        ids = ",".join(pmids)
        url = (
            f"{PubMedClient.BASE_FETCH_URL}"
            f"?db=pubmed&id={ids}&retmode=xml&rettype=abstract"
        )

        try:
            response = fetch_with_retry(url)
            response.raise_for_status()
            return PubMedClient.parse_articles(response.text)
        except requests.exceptions.RequestException as e:
            logger.error(f"PubMed fetch failed: {e}")
            return []

    @staticmethod
    def search_and_fetch(
        keywords: List[str],
        extra_terms: Optional[List[str]] = None,
        retmax: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Convenience method to search and fetch articles in one call.
        """
        pmids = PubMedClient.pubmed_search(keywords, extra_terms, retmax)
        if not pmids:
            logger.info("No PubMed IDs found for search")
            return []
        
        return PubMedClient.fetch_articles(pmids)


class SemanticScholarClient:
    """Client for searching Semantic Scholar API."""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.headers = {}
        if api_key:
            self.headers["x-api-key"] = api_key

    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search Semantic Scholar for papers.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of paper dictionaries with title, abstract, authors, etc.
        """
        url = f"{self.BASE_URL}/paper/search"
        params = {
            "query": query,
            "limit": max_results,
            "fields": "title,abstract,authors,year,publicationDate,citationCount,url,externalIds"
        }

        try:
            response = requests.get(
                url, 
                params=params, 
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for paper in data.get("data", []):
                results.append({
                    "title": paper.get("title", "Untitled"),
                    "abstract": paper.get("abstract", ""),
                    "authors": [author.get("name", "") for author in paper.get("authors", [])],
                    "year": paper.get("year"),
                    "published": paper.get("publicationDate", ""),
                    "citation_count": paper.get("citationCount", 0),
                    "url": paper.get("url", ""),
                    "doi": paper.get("externalIds", {}).get("DOI"),
                    "arxiv_id": paper.get("externalIds", {}).get("ArXiv"),
                    "pmid": paper.get("externalIds", {}).get("PubMed")
                })

            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"Semantic Scholar search failed: {e}")
            return []


class ArxivClient:
    """Client for searching arXiv papers."""
    
    DEFAULT_KEYWORDS = [
        'corvid', 'crow', 'raven', 'corvus', 'jay',
        'magpie', 'jackdaw', 'rook', 'chough', 'nutcracker'
    ]
    
    def __init__(self, default_keywords: Optional[List[str]] = None):
        """
        Initialize ArxivClient.
        
        Args:
            default_keywords: List of keywords to include in searches.
                            If None, uses DEFAULT_KEYWORDS.
        """
        self.default_keywords = default_keywords or self.DEFAULT_KEYWORDS

    def search(
        self, 
        query: str, 
        additional_keywords: Optional[List[str]] = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search arXiv for papers.
        
        Args:
            query: Main search query
            additional_keywords: Keywords to OR with query. If None, uses default_keywords.
            max_results: Maximum number of results to return
            
        Returns:
            List of paper dictionaries with title, abstract, authors, etc.
        """
        keywords = additional_keywords if additional_keywords is not None else self.default_keywords
        
        # build query: query OR keyword1 OR keyword2 ...
        q_parts = [query] + keywords
        q = " OR ".join(q_parts)
        
        url = (
            f"https://export.arxiv.org/api/query?"
            f"search_query=all:({q})&start=0&max_results={max_results}&"
            "sortBy=lastUpdatedDate&sortOrder=descending"
        )

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            feed = feedparser.parse(response.text)

            results = []
            for entry in feed.entries:
                # Skip entries without abstracts
                if not getattr(entry, "summary", "").strip():
                    continue

                results.append({
                    "title": getattr(entry, "title", "Untitled"),
                    "abstract": getattr(entry, "summary", ""),
                    "authors": [a.name for a in getattr(entry, "authors", [])],
                    "published": getattr(entry, "published", ""),
                    "updated": getattr(entry, "updated", ""),
                    "arxiv_link": getattr(entry, "link", ""),
                    "arxiv_id": getattr(entry, "id", "").split("/abs/")[-1] if hasattr(entry, "id") else None,
                    "categories": [tag.term for tag in getattr(entry, "tags", [])]
                })

            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"arXiv search failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing arXiv feed: {e}")
            return []


# example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # pubMed example
    print("=== PubMed Search ===")
    keywords = ['corvid', 'crow', 'raven']
    extra = ['memory', 'cognition']
    articles = PubMedClient.search_and_fetch(keywords, extra, retmax=5)
    for article in articles:
        print(f"\nTitle: {article['title']}")
        print(f"Authors: {article['author_str']}")
        print(f"DOI: {article.get('doi', 'N/A')}")
    
    # arXiv example
    print("\n\n=== arXiv Search ===")
    arxiv = ArxivClient()
    papers = arxiv.search("intelligence", max_results=3)
    for paper in papers:
        print(f"\nTitle: {paper['title']}")
        print(f"Authors: {', '.join(paper['authors'][:3])}")
        print(f"Link: {paper['arxiv_link']}")
    
    # semantic Scholar example
    print("\n\n=== Semantic Scholar Search ===")
    ss = SemanticScholarClient()
    papers = ss.search("corvid cognition", max_results=3)
    for paper in papers:
        print(f"\nTitle: {paper['title']}")
        print(f"Citations: {paper['citation_count']}")
        print(f"Year: {paper['year']}")