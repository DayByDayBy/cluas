# some thoughts re:formatting
#  havent set up API calls properly yet tho 


def snippet_abstract(abstract: str, max_length: int = 200) -> str:
    """Truncate abstract to first N chars, end at sentence."""
    if len(abstract) <= max_length:
        return abstract
    
    truncated = abstract[:max_length]
    last_period = truncated.rfind('.')
    if last_period > 0:
        return truncated[:last_period + 1]
    return truncated + "..."

def format_authors(authors: list) -> str:
    """Format author list as 'First, Second, et al.'"""
    if not authors:
        return "Unknown authors"
    if len(authors) <= 2:
        return ", ".join(authors)
    return f"{authors[0]}, {authors[1]}, et al."