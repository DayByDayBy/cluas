import xml.etree.ElementTree as ET
import urllib.parse
from typing import List, Optional

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



# # Example usage:
# ids = PubMedClient.pubmed_search(["corvid", "crow"], ["mating"])
