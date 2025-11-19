import pytest
from unittest.mock import patch

from src.cluas_mcp.academic.academic_search_entrypoint import academic_search

@patch("src.cluas_mcp.academic.academic_search_entrypoint.PubMedClient.pubmed_search")
@patch("src.cluas_mcp.academic.academic_search_entrypoint.SemanticScholarClient.search")
@patch("src.cluas_mcp.academic.academic_search_entrypoint.ArxivClient.search")
def test_academic_search_returns_expected_dict(
    mock_arxiv,
    mock_ss,
    mock_pubmed,
):
    mock_pubmed.return_value = ["pmid1", "pmid2"]
    mock_ss.return_value = [{"title": "Paper A"}]
    mock_arxiv.return_value = [{"title": "Arxiv Paper"}]

    result = academic_search("corvid")

    assert isinstance(result, dict)
    assert set(result.keys()) == {"pubmed", "semantic_scholar", "arxiv"}

    assert result["pubmed"] == ["pmid1", "pmid2"]
    assert result["semantic_scholar"] == [{"title": "Paper A"}]
    assert result["arxiv"] == [{"title": "Arxiv Paper"}]

    mock_pubmed.assert_called_once_with(["corvid"])
    mock_ss.assert_called_once_with("corvid")
    mock_arxiv.assert_called_once_with("corvid")

@patch("src.cluas_mcp.academic.academic_search_entrypoint.PubMedClient.pubmed_search")
@patch("src.cluas_mcp.academic.academic_search_entrypoint.SemanticScholarClient.search")
@patch("src.cluas_mcp.academic.academic_search_entrypoint.ArxivClient.search")
def test_academic_search_handles_client_failure(
    mock_arxiv,
    mock_ss,
    mock_pubmed,
):
    mock_pubmed.return_value = ["pmid1"]
    mock_ss.side_effect = Exception("Semantic Scholar down")
    mock_arxiv.return_value = ["arxiv1"]

    result = academic_search("corvid")

    assert result["pubmed"] == ["pmid1"]
    assert result["arxiv"] == ["arxiv1"]

    # should return an empty list (not throw)
    assert result["semantic_scholar"] == []