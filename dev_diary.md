# Development Diary

## 2024-01-XX - MVP Character Skeletons and Gradio Group Chat

### Goal
Create working skeletons for the three missing characters (Magpie, Raven, Crow) with placeholder tools, expand the MCP server to handle all tools, and build a Gradio group chat interface for the hackathon demo.

### Implementation

**Character Skeletons Created:**
- **Magpie** (Sanguine temperament): Enthusiastic trend-spotter with tools: `search_web`, `find_trending_topics`, `get_quick_facts`
- **Raven** (Choleric temperament): Passionate activist with tools: `search_news`, `get_environmental_data`, `verify_claim`
- **Crow** (Phlegmatic temperament): Calm observer with tools: `get_bird_sightings`, `get_weather_patterns`, `analyze_temporal_patterns`

All characters follow the Corvus pattern with Groq client setup, system prompts matching their temperaments, and stub `respond()` methods returning mock messages for MVP.

**Tool Entrypoints:**
Created three new entrypoint modules grouped by tool type:
- `src/cluas_mcp/web/web_search_entrypoint.py` - 3 functions
- `src/cluas_mcp/news/news_search_entrypoint.py` - 3 functions  
- `src/cluas_mcp/observation/observation_entrypoint.py` - 3 functions

All return structured mock data matching expected real response formats, with TODO comments for future full implementation.

**MCP Server Expansion:**
Updated `src/cluas_mcp/server.py` to:
- List all 10 tools (9 new + academic_search) in `list_tools()`
- Route all tool calls to appropriate entrypoints in `call_tool()`
- Added formatting functions for all tool result types

**Gradio Interface:**
Built `src/gradio/app.py` with:
- Sequential responses from all 4 characters
- Character names and emojis displayed
- Conversation history maintained
- Simple, MVP-focused implementation (no async handling yet)

### Issues Encountered and Resolved

1. **Circular Import Issue**: `src/gradio/__init__.py` was causing circular imports. **Resolution**: Deleted the file entirely as it wasn't needed. Updated root `app.py` to import directly from `src.gradio.app`.

2. **Import Path Inconsistencies**: Several files had incorrect import paths (missing `src.` prefix):
   - `src/gradio/app.py` - character imports
   - `src/cluas_mcp/academic/semantic_scholar.py`
   - `src/cluas_mcp/academic/pubmed.py`
   - `src/cluas_mcp/academic/arxiv.py`
   - `src/cluas_mcp/academic/thing.py`
   
   **Resolution**: Fixed all imports to use consistent `src.` prefix pattern.

3. **Gradio API Compatibility**: `theme=gr.themes.Soft()` parameter not supported in this Gradio version. **Resolution**: Removed the theme parameter.

4. **Gradio 6.x Migration**: The initial implementation used Gradio 5.x tuple format for chat history. **Resolution**: Migrated to Gradio 6.x messages format with structured content blocks:
   - Changed from `List[Tuple[str, str]]` to `List[dict]` with `{"role": "user/assistant", "content": [{"type": "text", "text": "..."}]}`
   - Updated `get_character_response()` to parse Gradio 6.x format and extract text from content blocks
   - Updated `chat_fn()` to return messages in the new structured format
   - Verified compatibility with Gradio 6.0.0-dev.4

### Testing
- All characters instantiate successfully
- Character responses work (stub implementations)
- Gradio app imports and initializes correctly
- All imports resolve properly
- No linter errors

### Status
MVP complete and working. All placeholder tools return structured mock data. Ready for hackathon demo. Future enhancements: full tool implementations, async responses, memory functionality, tool usage indicators.

### Commits
- `71f5dac` - Added character skeletons (Magpie, Raven, Crow) with placeholder tools, MCP server routes, and Gradio group chat interface
- `1868ae1` - Fixed import paths: removed gradio __init__.py, fixed all src. imports, removed theme parameter
- `1f44947` - Added documentation: steps_taken.md and dev_diary.md for character skeletons implementation
- `8696667` - Migrated chat_fn to Gradio 6.x messages format with structured content blocks

