from cluas_mcp.academic.arxiv import ArxivClient

def test_arxiv_basic():
    results = ArxivClient.search("all:corvid", max_results=5)
    assert isinstance(results, list)
    if results:  # don’t fail if ArXiv returns nothing
        first = results[0]
        assert "title" in first
        assert "abstract" in first
        assert "authors" in first
        assert "stage" in first and first["stage"] == "preprint"

if __name__ == "__main__":
    print(ArxivClient.search("all:corvid", max_results=2))
