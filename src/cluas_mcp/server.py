import FastMCP
import logging

def main():
    logging.basicConfig(level=logging.INFO)
    pass


@mcp.tool()
async def search_academic_papers(query: str) -> str:
    """Search academic papers across PubMed, Semantic Scholar, and ArXiv.
    
    Args:
        query: Search term for academic papers
        
    Returns:
        JSON string with results from all three sources
    """
    # Call the existing academic_search function
    # Format results as clean JSON string
    # Include paper titles, authors, abstracts, DOIs where available