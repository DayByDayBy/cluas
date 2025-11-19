from cluas_mcp.academic.pubmed import PubMedClient
from cluas_mcp.academic.semantic_scholar import SemanticScholarClient
from cluas_mcp.academic.arxiv import ArxivClient


def academic_search(term: str) -> dict:
    return {
        "pubmed": PubMedClient.pubmed_search([term]),
        "semantic_scholar": SemanticScholarClient.search(term),
        "arxiv": ArxivClient.search(term),
    }