# figure something a bit like this


@mcp.tool()
async def ask_crow_council(question: str) -> dict:
    """Consult all 4 characters; return synthesized response with sources."""

@mcp.tool()
async def ask_specific_expert(question: str, expert: Literal["corvus", "magpie", "raven", "crow"]) -> dict:
    """Query a single character."""

@mcp.tool()
async def fact_check_claim(claim: str) -> dict:
    """Have the council verify a claim using AgentMemory and tools."""