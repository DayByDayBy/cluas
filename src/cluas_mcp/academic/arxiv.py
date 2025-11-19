import logging
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
import feedparser

from cluas_mcp.domain.keywords import CORVID_KEYWORDS


logger = logging.getLogger(__name__)
class ArxivClient:
    """
    Minimal, robust arXiv client for searching with:
        (anyof(keywords)) AND (anyof(extra_terms))
    """

    BASE = "http://export.arxiv.org/api/query"

    @staticmethod
    def _join_or_group(items: List[str]) -> str:
        """
        Turn ['a', 'b c'] -> 'a OR "b c"' where phrases with spaces are quoted.
        We prefer quoting multi-word phrases so arXiv treats them as phrases.
        """
        parts = []
        for it in items:
            it = it.strip()
            if not it:
                continue
            # if it's multi-word, wrap in quotes so it's treated as a phrase
            if " " in it:
                # replace inner double quotes if any (simple sanitisation)
                safe = it.replace('"', "'")
                parts.append(f'"{safe}"')
            else:
                parts.append(it)
        return " OR ".join(parts) if parts else ""

    @staticmethod
    def _build_query(
        keywords: List[str], extra_terms: Optional[List[str]] = None
    ) -> str:
        """
        Build an arXiv search_query value, for example:
        all:(corvid OR crow OR "tool use") AND (calls OR "vocalization")
        """
        if not keywords:
            raise ValueError("keywords list must not be empty")

        kw_group = ArxivClient._join_or_group(keywords)
        query = f"all:({kw_group})"

        if extra_terms:
            extra_group = ArxivClient._join_or_group(extra_terms)
            if extra_group:
                query = f"{query} AND ({extra_group})"

        return query

    @staticmethod
    def _encode_query(query: str) -> str:
        # arXiv expects an URL-encoded query string
        return quote_plus(query)

    @staticmethod
    def _parse_entry(entry) -> Dict[str, Any]:
        authors = [a.name for a in getattr(entry, "authors", [])] if hasattr(entry, "authors") else []
        # arXiv id is usually in entry.id like "http://arxiv.org/abs/1234.56789v1"
        arxiv_id = None
        link = getattr(entry, "id", None)
        if link:
            arxiv_id = link.split("/")[-1]

        return {
            "title": getattr(entry, "title", ""),
            "abstract": getattr(entry, "summary", ""),
            "authors": authors,
            "link": link,
            "arxiv_id": arxiv_id,
            "stage": "preprint",
        }

    @classmethod
    def search(
        cls,
        keywords: List[str],
        extra_terms: Optional[List[str]] = None,
        max_results: int = 5,
        start: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Search arXiv using the pattern:
            (anyof(keywords)) AND (anyof(extra_terms))

        Example:
            ArxivClient.search(["corvid","crow"], extra_terms=["calls","vocalization"])
        """
        if not keywords:
            return []

        try:
            raw_query = cls._build_query(keywords, extra_terms)
        except ValueError:
            return []

        encoded = cls._encode_query(raw_query)
        url = f"{cls.BASE}?search_query={encoded}&start={start}&max_results={max_results}"

        logger.debug("arXiv query URL: %s", url)
        feed = feedparser.parse(url)

        # if arXiv returns feed with a single "Error" entry, treat as empty
        if getattr(feed, "entries", None) and len(feed.entries) == 1:
            first_title = getattr(feed.entries[0], "title", "")
            if first_title and first_title.lower().strip().startswith("error"):
                logger.warning("arXiv returned error for query: %s", raw_query)
                return []

        results = []
        skipped = 0
        for entry in getattr(feed, "entries", []):
            try:
                parsed = cls._parse_entry(entry)
                results.append(parsed)
            except Exception as e:
                skipped += 1
                logger.debug("Failed to parse arXiv entry: %s", e)
        logger.info("arXiv search returned %d results, skipped %d", len(results), skipped)

        return results
