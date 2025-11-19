import xml.etree.ElementTree as ET
import urllib.parse
from typing import List, Optional, Dict, Any

from cluas_mcp.common.http import fetch_with_retry

class PubMedClient:
    """Lightweight PubMed search client (ID only)."""

    @staticmethod
    def parse_id_list(xml: str) -> List[str]:
        """Parse PubMed ESearch XML and return a list of IDs."""
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            return []

        id_list = root.find(".//IdList")
        if id_list is None:
            return []

        return [elem.text for elem in id_list.findall("Id") if elem.text]

    @staticmethod
    def pubmed_search(
        keywords: List[str],
        extra_terms: Optional[List[str]] = None,
        retmax: int = 20,
        email: Optional[str] = None,  # add an email later - sort the forwarding first
        tool: str = "cluas_mcp",
    ) -> List[str]:
        """Search PubMed for (keywords OR ...) AND (extra_terms OR ...)."""

        # 1. build query
        base = f"({' OR '.join(keywords)})"
        if extra_terms:
            base += f" AND ({' OR '.join(extra_terms)})"

        term = urllib.parse.quote(base)

        # 2. build URL
        url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            f"?db=pubmed&term={term}&retmax={retmax}&retmode=xml"
            f"&tool={tool}"
        )
        if email:
            url += f"&email={urllib.parse.quote(email)}"

        # 3. fetch + parse
        try:
            response = fetch_with_retry(url)
            return PubMedClient.parse_id_list(response.text)
        except Exception:
            # shift to logging soon
            return []
        
    @staticmethod
    def fetch_articles(pmids: List[str]) -> List[Dict[str, Any]]:
        """Fetch full article details for a list of PubMed IDs."""
        if not pmids:
            return []

        ids = ",".join(pmids)
        url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            f"?db=pubmed&id={ids}&retmode=xml&rettype=abstract"
        )

        try:
            response = fetch_with_retry(url)
            root = ET.fromstring(response.text)
        except Exception as e:
            print(f"Failed to fetch articles: {e}")
            return []

        articles = []
        for article_elem in root.findall(".//PubmedArticle"):
            try:
                medline = article_elem.find(".//MedlineCitation/Article")
                pmid_elem = article_elem.find(".//MedlineCitation/PMID")
                title_elem = medline.find("ArticleTitle") if medline is not None else None
                abstract_elem = medline.find("Abstract/AbstractText") if medline is not None else None
                authors, author_str = parse_authors(medline)
                
                articles.append({
                    "pmid": pmid_elem.text if pmid_elem is not None else None,
                    "title": title_elem.text if title_elem is not None else "Untitled",
                    "abstract": abstract_elem.text if abstract_elem is not None else "",
                    "authors": authors,
                    "author_str": author_str
                })
            except Exception:
                continue

        return articles
    
    @staticmethod    
    def parse_authors(article_elem: ET.Element) -> tuple[list[str], str]:
        authors = []
        author_list = article_elem.find(".//AuthorList")
        if author_list is not None:
            for author in author_list.findall("Author"):
                last = author.find("LastName")
                fore = author.find("ForeName")
                if last is not None:
                    name = last.text
                    if fore is not None:
                        name = f"{last.text}, {fore.text}"
                    authors.append(name)
        author_str = authors[0] if authors else "Unknown"
        if len(authors) > 1:
            author_str += " et al."
        return authors, author_str



# # Example usage:
# ids = PubMedClient.pubmed_search(["corvid", "crow"], ["mating"])
