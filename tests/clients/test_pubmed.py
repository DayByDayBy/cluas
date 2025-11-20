import pytest
from src.cluas_mcp.academic.pubmed import PubMedClient

def test_pubmed_search_basic():
    # mnml query
    keywords = ["corvid"]
    extra_terms = None
    retmax = 3

    articles = PubMedClient.pubmed_search(keywords, extra_terms=extra_terms, retmax=retmax)
    assert isinstance(articles, list)
    assert len(articles) <= retmax

    if not articles: 
        pytest.skip("No PubMed IDs returned; cannot fetch articles")

    required_keys = {
        "source_id", "title", "abstract", "authors", "author_str", "doi", "link", "stage"
    }

    for art in articles:
        assert required_keys.issubset(art.keys())
        assert isinstance(art["authors"], list)
        assert isinstance(art["title"], str)
        assert art["title"] != ""
        assert art["stage"] == "peer_reviewed"

        # author-string logic
        if len(art["authors"]) == 0:
            assert art["author_str"] == "Unknown"
        elif len(art["authors"]) == 1:
            assert art["author_str"] == art["authors"][0]
        else:
            assert art["author_str"].endswith("et al.") or art["author_str"] == ", ".join(art["authors"][:2])
