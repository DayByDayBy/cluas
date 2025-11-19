from src.cluas_mcp.academic.semantic_scholar import SemanticScholarClient


def test_semantic_scholar_search():
    results = SemanticScholarClient.search("corvid", limit=3)
    assert isinstance(results, list)
    assert len(results) <= 3

    required_keys = {"title", "abstract", "authors", "author_str", "doi", "link", "year", "venue", "stage"}
    for paper in results:
        assert required_keys.issubset(paper.keys())
        assert isinstance(paper["authors"], list)
        assert isinstance(paper["title"], str)
        assert isinstance(paper["stage"], str)
        if len(paper["authors"]) == 2:
            assert paper["author_str"] == ", ".join(paper["authors"])
