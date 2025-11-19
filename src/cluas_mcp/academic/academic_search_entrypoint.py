import logging
from src.cluas_mcp.academic.semantic_scholar import SemanticScholarClient
from src.cluas_mcp.academic.pubmed import PubMedClient
from src.cluas_mcp.academic.arxiv import ArxivClient

logger = logging.getLogger(__name__)

def academic_search(term: str) -> dict:
    logger.info("Starting academic search for term: %s", term)
    
    try:
        pubmed = PubMedClient.pubmed_search([term])
    except Exception as e:
        logger.warning("PubMed search failed: %s", e)
        pubmed = []
    
    try:
        sem_scho = SemanticScholarClient.search(term)
    except Exception as e:
        logger.warning("Semantic Scholar search failed: %s", e)
        sem_scho = []
    try:
        arxiv = ArxivClient.search(term)
    except Exception as e:
        logger.warning("ArXiv search failed: %s", e)
        arxiv = []

    return {
        "pubmed": pubmed,
        "semantic_scholar": sem_scho,
        "arxiv": arxiv,
    }
