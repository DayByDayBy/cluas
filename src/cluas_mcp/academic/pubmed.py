#  a little more verbose than eg semantic scholar, due to how the pubmed API is set up
#  'works the same' tho, in the sense that it outputs the same shape of dict

import logging
import xml.etree.ElementTree as ET
import urllib.parse
from typing import List, Optional, Dict, Any

from cluas_mcp.common.http import fetch_with_retry
from cluas_mcp.domain.keywords import CORVID_KEYWORDS

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


        # -------------------------
        # helpers: full abstract extraction tool
        # ---------------
        @staticmethod
        def _extract_abstract(article_data: ET.Element) -> str:
            if article_data is None:
                return ""
            
            abstract_elem = article_data.find("Abstract")
            if abstract_elem is None:
                return ""
            
            parts = []
            for text_elem in abstract_elem.findall("AbstractText"):
                if text_elem.text:
                    parts.append(text_elem.text)
            
            return " ".join(parts)


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

        # Extract core elements safely
        medline = article_elem.find(".//MedlineCitation")
        article_data = medline.find("Article") if medline is not None else None
        pmid_elem = medline.find("PMID") if medline is not None else None

        pmid = pmid_elem.text if pmid_elem is not None else None

        # Title / abstract
        title = (
            (article_data.find("ArticleTitle").text if article_data is not None else None)
            or "Untitled"
        )

        abstract_elem = (
            article_data.find("Abstract/AbstractText") if article_data is not None else None
        )
        abstract = PubMedClient._extract_abstract(article_data)

        # Authors
        authors = PubMedClient._extract_authors(article_data)
        author_str = PubMedClient._make_author_str(authors)

        # DOI
        doi_elem = article_data.find(".//ELocationID[@EIdType='doi']") if article_data is not None else None
        doi = doi_elem.text if doi_elem is not None else None

        # Journal / venue
        journal_elem = article_data.find("Journal/Title") if article_data else None
        venue = journal_elem.text if journal_elem is not None else None

        # Year
        year_elem = article_data.find("Journal/JournalIssue/PubDate/Year") if article_data else None
        year = int(year_elem.text) if (year_elem is not None and year_elem.text.isdigit()) else None

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
            "venue": venue,
            "stage": "peer_reviewed",

            "citation_count": None,  # PubMed does not provide this
        }

    # -------------------------
    # Author utilities
    # -------------------------
    @staticmethod
    def _extract_authors(article_data: ET.Element) -> List[str]:
        if article_data is None:
            return []

        authors = []
        author_list = article_data.find(".//AuthorList")
        if author_list is None:
            return []

        for author in author_list.findall("Author"):
            last = author.find("LastName")
            fore = author.find("ForeName")

            if last is None:
                continue
            else:
                authors.append(last.text)

        return authors

    @staticmethod
    def _make_author_str(authors: List[str]) -> str:
        if not authors:
            return "Unknown"
        if len(authors) == 1:
            return authors[0]
        if len(authors) == 2:
            return " & ".join(authors) 
        return authors[0] + " et al."   