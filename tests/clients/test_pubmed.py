import pytest
from src.cluas_mcp.academic.pubmed import PubMedClient

def test_pubmed_search_basic():
    # Minimal query
    keywords = ["corvid"]
    extra_terms = None
    retmax = 3

    ids = PubMedClient.pubmed_search(keywords, extra_terms=extra_terms, retmax=retmax)
    assert isinstance(ids, list)
    assert len(ids) <= retmax

    if not ids:
        pytest.skip("No PubMed IDs returned; cannot fetch articles")

    articles = PubMedClient.fetch_articles(ids)
    assert isinstance(articles, list)

    required_keys = {
        "pmid", "title", "abstract", "authors", "author_str", "doi", "pubmed_link", "stage"
    }

    for art in articles:
        assert required_keys.issubset(art.keys())
        assert isinstance(art["authors"], list)
        assert isinstance(art["title"], str)
        assert art["title"] != ""
        assert art["stage"] == "peer_reviewed"

        # Author string logic
        if len(art["authors"]) == 0:
            assert art["author_str"] == "Unknown"
        elif len(art["authors"]) == 1:
            assert art["author_str"] == art["authors"][0]
        else:
            assert art["author_str"].endswith("et al.") or art["author_str"] == ", ".join(art["authors"][:2])
