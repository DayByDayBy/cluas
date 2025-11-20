import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_search():
    server_params = StdioServerParameters(
        command="python3",
        args=["-m", "src.cluas_mcp.server"],
        env={"PYTHONPATH": "src"}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # list available tools
            tools = await session.list_tools()
            print("Available tools:", tools)
            
            # call search tool
            result = await session.call_tool("academic_search", {"query": "corvid intelligence"})
            print("\nSearch results:")
            print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(test_search())