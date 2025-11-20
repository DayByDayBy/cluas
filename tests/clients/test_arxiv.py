import pytest
from src.cluas_mcp.academic.arxiv import ArxivClient

def test_arxiv_search_basic():
    keywords = ["corvid"]
    extra_terms = None
    max_results = 3

    results = ArxivClient.search(keywords, extra_terms=extra_terms, max_results=max_results)
    assert isinstance(results, list)
    assert len(results) <= max_results

    if not results:
        pytest.skip("No arXiv results returned; skipping article checks")

    required_keys = {"title", "abstract", "authors", "link", "paperId","source_id", "stage"}

    for paper in results:
        assert required_keys.issubset(paper.keys())
        assert isinstance(paper["authors"], list)
        assert isinstance(paper["title"], str)
        assert paper["title"] != ""
        assert paper["stage"] == "preprint"

        # Author string logic
        if len(paper["authors"]) == 0:
            author_str = "Unknown"
        elif len(paper["authors"]) == 1:
            author_str = paper["authors"][0]
        else:
            author_str = paper["authors"][0] + " et al."

        assert author_str