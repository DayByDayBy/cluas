import pytest
from src.cluas_mcp.academic.semantic_scholar import SemanticScholarClient

def test_semantic_scholar_search_basic():
    results = SemanticScholarClient.search("corvid", limit=3)
    assert isinstance(results, list)
    assert len(results) <= 3

    if not results:
        pytest.skip("No Semantic Scholar results returned; skipping article checks")

    required_keys = {
        "title", "abstract", "authors", "author_str", "doi", "link",
        "paperId", "source", "year", "venue", "stage", "citation_count"
    }

    for paper in results:
        assert required_keys.issubset(paper.keys())
        assert isinstance(paper["authors"], list)
        assert isinstance(paper["title"], str)
        assert paper["title"] != ""
        assert paper["stage"] in {"peer_reviewed", "preprint"}
        assert paper["source"] == "semantic_scholar"
        
        # author-string logic
        if len(paper["authors"]) == 0:
            assert paper["author_str"] == "Unknown"
        elif len(paper["authors"]) == 1:
            assert paper["author_str"] == paper["authors"][0]
        elif len(paper["authors"]) == 2:
            assert paper["author_str"] == ", ".join(paper["authors"])
        else:
            assert paper["author_str"].endswith("et al.")
