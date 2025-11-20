import pytest
from unittest.mock import patch, MagicMock
from src.cluas_mcp.academic.pubmed import PubMedClient

@pytest.fixture
def mock_fetch():
    with patch('src.cluas_mcp.academic.pubmed.fetch_with_retry') as mock:
        yield mock

def test_pubmed_search_empty_keywords(mock_fetch):
    # Mock the fetch to return empty XML
    mock_fetch.return_value = MagicMock(text="<eSearchResult><IdList></IdList></eSearchResult>")
    result = PubMedClient.pubmed_search(keywords=None)
    assert result == []

def test_pubmed_search_with_keywords(mock_fetch):
    # Mock the search response with a single PMID
    mock_fetch.side_effect = [
        MagicMock(text="<eSearchResult><IdList><Id>12345</Id></IdList></eSearchResult>"),
        MagicMock(text="""
            <PubmedArticleSet>
                <PubmedArticle>
                    <MedlineCitation>
                        <PMID>12345</PMID>
                        <Article>
                            <ArticleTitle>Test Title</ArticleTitle>
                            <Abstract><AbstractText>Test Abstract</AbstractText></Abstract>
                            <AuthorList>
                                <Author><LastName>Doe</LastName><ForeName>John</ForeName></Author>
                            </AuthorList>
                            <Journal><Title>Test Journal</Title><JournalIssue><PubDate><Year>2023</Year></PubDate></JournalIssue></Journal>
                            <ELocationID EIdType="doi">10.1234/test</ELocationID>
                        </Article>
                    </MedlineCitation>
                </PubmedArticle>
            </PubmedArticleSet>
        """)
    ]
    result = PubMedClient.pubmed_search(keywords=["test"], retmax=1)
    assert len(result) == 1
    assert result[0]["title"] == "Test Title"
    assert result[0]["abstract"] == "Test Abstract"
    assert result[0]["authors"] == ["Doe"]
    assert result[0]["doi"] == "10.1234/test"
    assert result[0]["venue"] == "Test Journal"
    assert result[0]["year"] == 2023
    assert result[0]["pmid"] == "12345"
    assert result[0]["link"] == "https://pubmed.ncbi.nlm.nih.gov/12345/"

def test_pubmed_search_with_extra_terms(mock_fetch):
    # Mock the search response with a single PMID
    mock_fetch.side_effect = [
        MagicMock(text="<eSearchResult><IdList><Id>67890</Id></IdList></eSearchResult>"),
        MagicMock(text="""
            <PubmedArticleSet>
                <PubmedArticle>
                    <MedlineCitation>
                        <PMID>67890</PMID>
                        <Article>
                            <ArticleTitle>Test Title 2</ArticleTitle>
                            <Abstract><AbstractText>Test Abstract 2</AbstractText></Abstract>
                            <AuthorList>
                                <Author><LastName>Smith</LastName><ForeName>Jane</ForeName></Author>
                                <Author><LastName>Brown</LastName><ForeName>Bob</ForeName></Author>
                            </AuthorList>
                            <Journal><Title>Test Journal 2</Title><JournalIssue><PubDate><Year>2024</Year></PubDate></JournalIssue></Journal>
                            <ELocationID EIdType="doi">10.5678/test</ELocationID>
                        </Article>
                    </MedlineCitation>
                </PubmedArticle>
            </PubmedArticleSet>
        """)
    ]
    result = PubMedClient.pubmed_search(keywords=["test"], extra_terms=["extra"], retmax=1)
    assert len(result) == 1
    assert result[0]["title"] == "Test Title 2"
    assert result[0]["author_str"] == "Smith & Brown"

def test_pubmed_search_failed_fetch(mock_fetch):
    # Mock the fetch to raise an exception
    mock_fetch.side_effect = Exception("Failed to fetch")
    result = PubMedClient.pubmed_search(keywords=["test"])
    assert result == []

def test_pubmed_search_invalid_xml(mock_fetch):
    # Mock the fetch to return invalid XML
    mock_fetch.return_value = MagicMock(text="not xml")
    result = PubMedClient.pubmed_search(keywords=["test"])
    assert result == []
