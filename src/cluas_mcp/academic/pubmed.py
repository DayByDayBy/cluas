import logging
import xml.etree.ElementTree as ET
import urllib.parse
from typing import List, Optional, Dict, Any
from cluas_mcp.domain.keywords import CORVID_KEYWORDS
from cluas_mcp.common.http import fetch_with_retry

logger = logging.getLogger(__name__)

class PubMedClient:
    """Lightweight PubMed search client (ID only)."""
      
    @staticmethod
    def fetch_articles(pmids: List[str]) -> List[Dict[str, Any]]:
        """Fetch full article details for a list of PubMed IDs."""
        if not pmids:
            logger.info("No PMIDs provided, returning empty list")
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
            logger.warning("Skipping article due to parse error: %s", e)
            return []
        
        articles = []
        skipped = 0
        for article_elem in root.findall(".//PubmedArticle"):
            try:
                medline = article_elem.find(".//MedlineCitation")
                if medline is None:
                    skipped += 1
                    continue
                article_data = medline.find("Article")
                pmid_elem = medline.find("PMID")
                title_elem = article_data.find("ArticleTitle") if article_data is not None else None
                abstract_elem = article_data.find("Abstract/AbstractText") if article_data is not None else None
                authors, author_str = PubMedClient.parse_authors(article_data)
                doi_elem = article_data.find(".//ELocationID[@EIdType='doi']") if article_data is not None else None
                pubmed_link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid_elem.text}/" if pmid_elem is not None else None
                
                articles.append({
                    "pmid": pmid_elem.text if pmid_elem is not None else None,
                    "title": title_elem.text if title_elem is not None else "Untitled",
                    "abstract": abstract_elem.text if abstract_elem is not None else "",
                    "authors": authors,
                    "author_str": author_str,
                    "doi": doi_elem.text if doi_elem is not None else None,
                    "pubmed_link": pubmed_link,
                    "stage": "peer_reviewed"
                })
            except Exception as e:
                skipped += 1
                logger.warning(f"Skipping article due to parse error: {e}")
                continue
            
        if skipped:
            logger.info(f"Skipped {skipped} articles due to parse errors")
        return articles    

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
        keywords: List[str] = None,
        extra_terms: Optional[List[str]] = None,
        retmax: int = 20,
        email: Optional[str] = None,  # add an email later - sort the forwarding first
        tool: str = "cluas_mcp",
    ) -> List[str]:
        """Search PubMed for (keywords OR ...) AND (extra_terms OR ...)."""
        if keywords is None:
            keywords = CORVID_KEYWORDS
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
