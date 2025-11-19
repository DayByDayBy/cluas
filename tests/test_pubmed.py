from src.cluas_mcp.academic.pubmed import PubMedClient

def test_pubmed_search(keywords, extra_terms=None, retmax=5):
    """
    Lightweight test harness for PubMed.
    Prints the first `retmax` articles found for keywords + extra_terms.
    """
    print(f"Searching PubMed for: {keywords} {'+' + str(extra_terms) if extra_terms else ''}\n")

    # 1. search
    ids = PubMedClient.pubmed_search(keywords, extra_terms=extra_terms, retmax=retmax)
    if not ids:
        print("No PubMed IDs found.\n")
        return

    print(f"Found {len(ids)} IDs: {ids}\nFetching articles...\n")

    # 2. fetch
    articles = PubMedClient.fetch_articles(ids)

    if not articles:
        print("No articles could be fetched.\n")
        return

    # 3. print concise summaries
    for i, art in enumerate(articles, 1):
        print(f"--- Article {i} ---")
        print(f"Title: {art['title']}")
        print(f"Authors: {art['author_str']}")
        abstract_snippet = art['abstract'][:200].replace('\n', ' ') + ('...' if len(art['abstract']) > 200 else '')
        print(f"Abstract: {abstract_snippet}")
        print(f"DOI: {art.get('doi', 'N/A')}")
        print(f"PubMed link: {art.get('pubmed_link', 'N/A')}\n")


if __name__ == "__main__":
    # Example queries
    test_pubmed_search(["corvid", "crow"], extra_terms=["cognition"])
    test_pubmed_search(["raven"], extra_terms=["tool use"])
