from common.http import fetch_with_retry
import requests
import feedparser
import xml.etree.ElementTree as ET
import urllib.parse
from typing import List, Optional

class PubMedClient:

    @staticmethod
    def parse_id_list(xml: str) -> List[str]:
        """Parse XML and return a list of PubMed IDs."""
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            return []  # invalid XML or rate limit page

        id_list = root.find(".//IdList")
        if id_list is None:
            return []

        return [elem.text for elem in id_list.findall("Id") if elem.text]

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
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            f"?db=pubmed&term={term}&retmax={retmax}&retmode=xml"
        )

        try:
            response = fetch_with_retry(url)
            response.raise_for_status()
            return PubMedClient.parse_id_list(response.text)

        except requests.exceptions.RequestException:
            # log instead of print, lol
            return []
        

        

