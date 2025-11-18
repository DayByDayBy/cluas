from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
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
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return PubMedClient.parse_id_list(response.text)

        except requests.exceptions.RequestException:
            # log instead of print, lol
            return []



class SemanticScholarClient:
    def search(self, query, max_results=5):
        # placeholder: implement Semantic Scholar API call
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




# possible endpoint?
# https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&term=corvid+AND+memory




# from Bio import Entrez
# Entrez.email = "your.email@domain.tld"  # required by NCBI
# Entrez.api_key = "YOUR_KEY_IF_YOU_HAVE_ONE"

# KEYWORDS = ['corvid','crow','raven','corvus','jay','magpie','jackdaw','rook','chough','nutcracker']
# SECONDARY = ['memory', 'feeding']

# term = "(" + " OR ".join(KEYWORDS) + ")" + " AND (" + " OR ".join(SECONDARY) + ")"
# handle = Entrez.esearch(db="pubmed", term=term, retmax=100)  # adjust retmax
# record = Entrez.read(handle)
# ids = record["IdList"]

# for pmid in ids:
#     handle2 = Entrez.efetch(db="pubmed", id=pmid, retmode="xml")
#     rec = Entrez.read(handle2)
#     article = rec['PubmedArticle'][0]
#     # parse title
#     title = article['MedlineCitation']['Article']['ArticleTitle']
#     # parse authors
#     authors = article['MedlineCitation']['Article']['AuthorList']
#     first_author = authors[0]['LastName'] + ", " + authors[0]['ForeName']
#     author_str = first_author + (", et al" if len(authors) > 1 else "")
#     # parse abstract
#     abstract = ""
#     if 'Abstract' in article['MedlineCitation']['Article']:
#         abstract = " ".join([x for x in article['MedlineCitation']['Article']['Abstract']['AbstractText']])
#     # parse DOI
#     doi = None
#     for aid in article['PubmedData']['ArticleIdList']:
#         if aid.attributes['IdType'] == 'doi':
#             doi = str(aid)
#     # parse a “conclusion” if structured abstract includes it
#     conclusion = None
#     # one simple heuristic: look for segments labeled 'CONCLUSION' in structured abstract
#     if 'Abstract' in article['MedlineCitation']['Article']:
#         for sec in article['MedlineCitation']['Article']['Abstract']['AbstractText']:
#             if hasattr(sec, "attributes") and sec.attributes.get('Label', '').upper() == 'CONCLUSION':
#                 conclusion = str(sec)
#     # fallback: maybe take the last sentence of abstract
#     if conclusion is None and abstract:
#         conclusion = abstract.split('.')[-2] + '.'

#     # now you have doi, title, author_str, abstract, conclusion
#     print(pmid, doi, title, author_str, conclusion)





# f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={query}'
#         f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={id[0]}&retmode=xml&rettype=abstract'