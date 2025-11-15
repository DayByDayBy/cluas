def search_academic_papers(
    query: str,
    topic: str = "corvid",
    year_range: tuple[int, int] | None = None,
    sort_by: str = "relevance",
    max_results: int = 5
) -> list[dict] | None:
    """
    Search academic papers on a given topic using arXiv and fallback APIs.

    Args:
        query: Search terms (e.g., "tool use in crows").
        topic: Domain of interest (e.g., "corvid", "conservation").
        year_range: Optional (start_year, end_year) filter.
        sort_by: Sort results by "relevance" or "date".
        max_results: Maximum number of results to return.

    Returns:
        List of paper metadata (dicts) or None if no results.
    """