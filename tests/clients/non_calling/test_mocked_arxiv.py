import pytest
from unittest.mock import patch, MagicMock
from src.cluas_mcp.academic.arxiv import ArxivClient
from feedparser import FeedParserDict

def test_arxiv_search_mock():
    # Mock authors as a list of dicts with "name" keys
    fake_authors = [{"name": "Jane Doe"}, {"name": "John Smith"}]

    fake_entry = MagicMock()
    fake_entry.title = "Corvid Tool Use in AI"
    fake_entry.summary = "This paper discusses corvid tool use in AI."
    fake_entry.authors = fake_authors  # List of dicts, not MagicMocks
    fake_entry.id = "http://arxiv.org/abs/1234.5678v1"
    fake_entry.link = "http://arxiv.org/abs/1234.5678v1"
    fake_entry.published = "2023-01-01"  # Required for year extraction

    fake_feed = FeedParserDict(entries=[fake_entry])

    with patch("src.cluas_mcp.academic.arxiv.feedparser.parse", return_value=fake_feed):
        results = ArxivClient.search(["corvid"], max_results=1)
        print("Results:", results)  # Debug output
        assert len(results) == 1
        paper = results[0]
        assert paper["title"] == "Corvid Tool Use in AI"
        assert paper["authors"] == ["Jane Doe", "John Smith"]
        assert paper["author_str"] == "Jane Doe, John Smith"
        assert paper["paperId"] == "1234.5678v1"
        assert paper["stage"] == "preprint"
