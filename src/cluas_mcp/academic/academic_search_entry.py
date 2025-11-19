import logging
from src.cluas_mcp.academic.semantic_scholar import SemanticScholarClient
from src.cluas_mcp.academic.pubmed import PubMedClient
from src.cluas_mcp.academic.arxiv import ArxivClient

logger = logging.getLogger(__name__)

def academic_search(term: str) -> dict:
    logger.info("Starting academic search for term: %s", term)

    return {
        "pubmed": PubMedClient.pubmed_search([term]),
        "semantic_scholar": SemanticScholarClient.search(term),
        "arxiv": ArxivClient.search(term),
    }
