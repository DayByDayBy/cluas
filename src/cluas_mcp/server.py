import asyncio
import json
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.cluas_mcp.academic.academic_search_entrypoint import academic_search

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = Server("cluas-academic")

@mcp.list_tools()   
async def list_tools() -> str:    
    """listing available tools."""
    return [
        Tool(
            name="academic_search",
            description="Search academic papers across PubMed, Semantic Scholar, and ArXiv",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "search query for academic papers.",
                    }
                },
                "required": ["query"]
            }
        )
    ]
    
@mcp.call_tool()
async def call_tool(tool_name: str, arguments: dict) -> list[TextContent]:
    """handle tool calls"""
    if tool_name != "academic_search":
        raise ValueError(f"Unknown tool: {tool_name}")
    
    query = arguments.get("query")
    if not query:
        raise ValueError(f'unkown tool: {tool_name}')
    
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, academic_search, query)
    
    formatted = format_search_results(results)
    
    return [TextContent(type="text", text=formatted)]


def format_search_results(results: dict) ->str:
    """format search results into readable string"""
    output = []
    
    pubmed_results = results.get("pubmed", [])
    if pubmed_results:
        output.append("=== PubMed Results ===\n")
        for i, paper in enumerate(pubmed_results[:5], 1):
            output.append(f"{i}. {paper.get('title', 'No Title')}\n")
            authors = paper.get('authors', [])
            if authors:
                output.append(f"   Authors: {', '.join(authors[:3])}")
            abstract = paper.get('abstract', 'No Abstract')
            if  abstract != 'No Abstract':
                output.append(f"   Abstract: {abstract[:200]}...\n")
            output.append("")
            
    ss_results = results.get("semantic_scholar", [])
    if ss_results:
        output.append("=== Semantic Scholar Results ===\n")
        for i, paper in enumerate(ss_results[:5], 1):
            output.append(f"{i}. {paper.get('title', 'No Title')}\n")
            authors = paper.get('authors', [])
            if authors:
                output.append(f"   Authors: {', '.join(authors[:3])}")
            abstract = paper.get('abstract', 'No Abstract')
            if abstract != 'No Abstract':
                output.append(f"   Abstract: {abstract[:200]}...\n")
            output.append("")
            
            
            
    arxiv_results = results.get("arxiv", [])
    if arxiv_results:
        output.append("=== ArXiv Results ===\n")
        for i, paper in enumerate(arxiv_results[:5], 1):
            output.append(f"{i}. {paper.get('title', 'No Title')}\n")
            authors = paper.get('authors', [])
            if authors:
                output.append(f"   Authors: {', '.join(authors[:3])}")
            abstract = paper.get('abstract', 'No Abstract')
            if abstract != 'No Abstract':
                output.append(f"   Abstract: {abstract[:200]}...\n")
            output.append("")
        
    
    if not output:
        return "No results found."
    
    return "\n".join(output)

async def main():
    """"run the MCP server."""
    logger.info("Starting CLUAS academic MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(
            read_stream, 
            write_stream,
            mcp.create_initialization_options()
            )
        
if __name__ == "__main__":
    asyncio.run(main())