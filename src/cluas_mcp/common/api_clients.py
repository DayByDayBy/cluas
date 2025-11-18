import requests
import feedparser
import urllib.parse
import xml.etree.ElementTree as ET



class PubMedClient:        
    
    def parse_id_list(xml: str) -> list[str]:
        root = ET.fromstring(xml)
        id_list = root.find('IdList')
        ids = [id_elem.text for id_elem in id_list.findall('Id')]
        return ids
    
    
    def pubmed_search(keywords: list[str], extra_terms: list[str] = None) -> list[str]:
        # OR-groups must be wrapped for logical correctness
        base = "(" + " OR ".join(keywords) + ")"

        if extra_terms:
            extras = "(" + " OR ".join(extra_terms) + ")"
            base = f"{base} AND {extras}"

        url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            f"?db=pubmed&term={urllib.parse.quote(base)}&retmax=20"
        )

        xml = requests.get(url).text
        return parse_id_list(xml)

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