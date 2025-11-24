from src.cluas_mcp.common.memory import AgentMemory

# scored search
memory = AgentMemory()
memory.add_item(
    title="Corvid Tool Use in Urban Environments",
    doi="10.1234/test",
    snippet="Test abstract",
    mentioned_by="Test"
)

# scoring works
results = memory.search_title_scored("corvid tool")
print(f"Found {len(results)} results")
if results:
    print(f"Best match: {results[0]['title']}")
    print(f"Score: {results[0]['relevance_score']:.2f}")