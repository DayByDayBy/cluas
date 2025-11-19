import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def academic_search(term: str) -> dict:
    logger.info("Starting academic search for term: %s", term)

    return {
        "pubmed": PubMedClient.pubmed_search([term]),
        "semantic_scholar": SemanticScholarClient.search(term),
        "arxiv": ArxivClient.search(term),
    }
