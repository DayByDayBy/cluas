#  a little more verbose than eg semantic scholar, due to how the pubmed API is set up
#  'works the same' tho, in the sense that it outputs the same shape of dict


import logging
import xml.etree.ElementTree as ET
import urllib.parse
from typing import List, Optional, Dict, Any, Tuple

from src.cluas_mcp.common.http import fetch_with_retry
from src.cluas_mcp.domain import CORVID_KEYWORDS

logger = logging.getLogger(__name__)


class PubMedClient:
    SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    # -------------------------
    # public entry point
    # -------------------------
    @staticmethod
    def pubmed_search(
        keywords: List[str] = None,
        extra_terms: Optional[List[str]] = None,
        retmax: int = 20,
        email: Optional[str] = None,
        tool: str = "cluas_mcp",
    ) -> List[dict]:
        """
        Returns fully normalized PubMed article dicts (matching Semantic Scholar format).
        """
        pmids = PubMedClient._search_ids(keywords, extra_terms, retmax, email, tool)
        if not pmids:
            return []

        raw_articles = PubMedClient._fetch_articles(pmids)
        return [PubMedClient._normalize_article(a) for a in raw_articles]

    # -------------------------
    # helpers: search
    # -------------------------
    @staticmethod
    def _search_ids(
        keywords: List[str],
        extra_terms: Optional[List[str]],
        retmax: int,
        email: Optional[str],
        tool: str,
    ) -> List[str]:

        if keywords is None:
            keywords = CORVID_KEYWORDS

        query = f"({' OR '.join(keywords)})"
        if extra_terms:
            query += f" AND ({' OR '.join(extra_terms)})"

        encoded_query = urllib.parse.quote(query)

        url = (
            f"{PubMedClient.SEARCH_URL}?db=pubmed&term={encoded_query}"
            f"&retmax={retmax}&retmode=xml&tool={tool}"
        )
        if email:
            url += f"&email={urllib.parse.quote(email)}"

        try:
            response = fetch_with_retry(url)
            return PubMedClient._parse_id_list(response.text)
        except Exception as e:
            logger.warning("PubMed search failed: %s", e)
            return []

    @staticmethod
    def _parse_id_list(xml_text: str) -> List[str]:
        try:
            root = ET.fromstring(xml_text)
            id_list = root.find(".//IdList")
            if id_list is None:
                return []
            return [elem.text for elem in id_list.findall("Id") if elem.text]
        except ET.ParseError:
            return []

    # -------------------------
    # Helpers: Fetch details
    # -------------------------
    @staticmethod
    def _fetch_articles(pmids: List[str]) -> List[ET.Element]:
        """
        Returns a list of <PubmedArticle> XML elements.
        """
        if not pmids:
            return []

        ids = ",".join(pmids)
        url = (
            f"{PubMedClient.FETCH_URL}?db=pubmed&id={ids}"
            "&retmode=xml&rettype=abstract"
        )

        try:
            response = fetch_with_retry(url)
            root = ET.fromstring(response.text)
            return root.findall(".//PubmedArticle")
        except Exception as e:
            logger.warning("PubMed fetch failed: %s", e)
            return []

    # -------------------------
    # Normalization (main work)
    # -------------------------
    @staticmethod
    def _normalize_article(article_elem: ET.Element) -> Dict[str, Any]:
        """
        Transform PubMed XML into normalized dict matching Semantic Scholar format.
        """
        # Extract core elements safely
        medline = article_elem.find(".//MedlineCitation")
        article_data = medline.find("Article") if medline is not None else None
        pmid_elem = medline.find("PMID") if medline is not None else None

        pmid = pmid_elem.text if pmid_elem is not None else None

        # Extract all components using helper methods
        title = PubMedClient._extract_title(article_data)
        abstract = PubMedClient._extract_abstract(article_data)
        authors = PubMedClient._extract_authors(article_data)
        author_str = PubMedClient._make_author_str(authors)
        doi = PubMedClient._extract_doi(article_elem, article_data)
        venue = PubMedClient._extract_venue(article_data)
        year, pub_date = PubMedClient._extract_pub_date(article_data)
        mesh_terms = PubMedClient._extract_mesh_terms(medline)

        return {
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "author_str": author_str,

            "doi": doi,
            "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
            "paperId": pmid,  # normalized name
            "source_id": pmid,
            "source": "pubmed",

            "year": year,
            "published": pub_date,
            "venue": venue,
            "stage": "peer_reviewed",

            "citation_count": None,  # PubMed does not provide this
            "mesh_terms": mesh_terms,  # PubMed-specific feature
        }

    # -------------------------
    # Extraction utilities
    # -------------------------
    @staticmethod
    def _extract_title(article_data: Optional[ET.Element]) -> str:
        """Extract article title safely."""
        if article_data is None:
            return "Untitled"
        
        title_elem = article_data.find("ArticleTitle")
        if title_elem is not None and title_elem.text:
            return title_elem.text
        
        return "Untitled"

    @staticmethod
    def _extract_abstract(article_data: Optional[ET.Element]) -> str:
        """
        Extract abstract, handling both simple and structured abstracts.
        Structured abstracts have multiple AbstractText elements with labels.
        """
        if article_data is None:
            return ""
        
        abstract_elem = article_data.find("Abstract")
        if abstract_elem is None:
            return ""
        
        # Collect all AbstractText elements
        parts = []
        for text_elem in abstract_elem.findall("AbstractText"):
            if text_elem.text:
                parts.append(text_elem.text)
        
        return " ".join(parts)

    @staticmethod
    def _extract_doi(
        article_elem: ET.Element, 
        article_data: Optional[ET.Element]
    ) -> Optional[str]:
        """
        Extract DOI from multiple possible locations.
        PubMed stores DOIs in ELocationID or ArticleIdList.
        """
        # Try ELocationID first (common location)
        if article_data is not None:
            doi_elem = article_data.find(".//ELocationID[@EIdType='doi']")
            if doi_elem is not None and doi_elem.text:
                return doi_elem.text
        
        # Try ArticleIdList in PubmedData (alternative location)
        pubmed_data = article_elem.find(".//PubmedData")
        if pubmed_data is not None:
            for article_id in pubmed_data.findall(".//ArticleId"):
                if article_id.get("IdType") == "doi" and article_id.text:
                    return article_id.text
        
        return None

    @staticmethod
    def _extract_venue(article_data: Optional[ET.Element]) -> Optional[str]:
        """Extract journal name."""
        if article_data is None:
            return None
        
        journal_elem = article_data.find("Journal/Title")
        if journal_elem is not None and journal_elem.text:
            return journal_elem.text
        
        return None

    @staticmethod
    def _extract_pub_date(
        article_data: Optional[ET.Element]
    ) -> Tuple[Optional[int], Optional[str]]:
        """
        Extract publication date information.
        Returns (year, full_date_string).
        """
        if article_data is None:
            return None, None
        
        pub_date = article_data.find("Journal/JournalIssue/PubDate")
        if pub_date is None:
            return None, None
        
        # Extract year
        year_elem = pub_date.find("Year")
        year = None
        if year_elem is not None and year_elem.text and year_elem.text.isdigit():
            year = int(year_elem.text)
        
        # Build full date string (YYYY-MM-DD or YYYY-MM or YYYY)
        month_elem = pub_date.find("Month")
        day_elem = pub_date.find("Day")
        
        date_parts = []
        if year_elem is not None and year_elem.text:
            date_parts.append(year_elem.text)
        if month_elem is not None and month_elem.text:
            date_parts.append(month_elem.text)
        if day_elem is not None and day_elem.text:
            date_parts.append(day_elem.text)
        
        date_str = "-".join(date_parts) if date_parts else None
        
        return year, date_str

    @staticmethod
    def _extract_mesh_terms(medline: Optional[ET.Element]) -> List[str]:
        """
        Extract MeSH (Medical Subject Headings) terms.
        These are controlled vocabulary terms assigned by NCBI indexers.
        Very useful for research to filter by topics like:
        - "Memory", "Learning", "Cognition"
        - "Social Behavior", "Animal Communication"
        - "Tool Use", "Problem Solving"
        """
        if medline is None:
            return []
        
        mesh_list = medline.find(".//MeshHeadingList")
        if mesh_list is None:
            return []
        
        terms = []
        for mesh in mesh_list.findall(".//MeshHeading"):
            descriptor = mesh.find("DescriptorName")
            if descriptor is not None and descriptor.text:
                terms.append(descriptor.text)
        
        return terms

    # -------------------------
    # Author utilities
    # -------------------------
    @staticmethod
    def _extract_authors(article_data: Optional[ET.Element]) -> List[str]:
        """Extract author last names."""
        if article_data is None:
            return []

        author_list = article_data.find(".//AuthorList")
        if author_list is None:
            return []

        authors = []
        for author in author_list.findall("Author"):
            last = author.find("LastName")
            if last is not None and last.text:
                authors.append(last.text)

        return authors

    @staticmethod
    def _make_author_str(authors: List[str]) -> str:
        """Format author list for display."""
        if not authors:
            return "Unknown"
        if len(authors) == 1:
            return authors[0]
        if len(authors) == 2:
            return " & ".join(authors)
        return authors[0] + " et al."