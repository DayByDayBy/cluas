import pytest
from unittest.mock import patch, MagicMock
from src.cluas_mcp.academic.semantic_scholar import SemanticScholarClient

def test_semantic_scholar_search_mock():
    fake_response = {
        "data": [
            {
                "title": "A Study on Corvids",
                "abstract": "Abstract here...",
                "authors": [{"name": "Jane Doe"}, {"name": "John Smith"}],
                "doi": "10.1234/abcd",
                "paperId": "123456",
                "venue": "Journal of Birds",
                "year": 2023,
                "citationCount": 5,
            }
        ]
    }

    with patch("src.cluas_mcp.academic.semantic_scholar.fetch_with_retry") as mock_fetch:
        mock_fetch.return_value.json = MagicMock(return_value=fake_response)
        results = SemanticScholarClient.search("corvid", limit=1)
    
    assert len(results) == 1
    paper = results[0]
    assert paper["title"] == "A Study on Corvids"
    assert paper["author_str"] == "Jane Doe, John Smith"
    assert paper["stage"] == "peer_reviewed"
