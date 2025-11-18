# Corvid Council - Development Guide

## Project Overview

**Name**: Corvid Council  
**Hackathon**: Gradio Agents & MCP Hackathon - Winter 25  
**Track**: Building MCP (Creative)  
**Tags**: `building-mcp-track-creative`

### Concept
A multi-agent group chat where 4 AI crow experts discuss topics, each using specialized MCP tools. The Gradio app itself also exposes MCP tools, allowing external applications to query the expert panel.

### The Hook
"What if you could consult a panel of AI experts? Use it two ways: watch them research and debate in a group chat, or query them as an MCP tool from Claude Desktop or any MCP client."

---

## Architecture

```
External User/App (Claude Desktop, etc.)
    ↓ (calls MCP tool)
ask_crow_council(question)
    ↓ (hits)
Gradio App (IS an MCP server)
    ↓ (internally orchestrates)
CouncilOrchestrator
    ↓ (manages)
4 Character Agents (Corvus, Magpie, Raven, Crow)
    ↓ (each uses)
Character-Specific MCP Tools (~12-15 total)
    ↓ (which call)
External APIs (Semantic Scholar, eBird, Weather, etc.)
    ↓ (returns aggregated response)
Back to User
```

### Two Interfaces, Same Backend

**Interface 1: Gradio Chat UI** (Direct access)
- Users see the full group chat
- Watch characters use their tools in real-time
- See sources, debates, synthesis
- Can inject questions

**Interface 2: MCP Tools** (Programmatic access)
- External apps call `ask_crow_council(question)`
- Same orchestration happens internally
- Returns structured, synthesized response
- Fast, clean API integration

---

## The Characters

### Corvus (The Scholar) - Melancholic
**Archetype**: Academic, thorough, perfectionist  
**Personality**: 
- PhD researcher studying corvid cognition
- Every claim needs citation
- Cautious, analytical, sometimes pedantic
- Posts rarely but substantively
- Always verifies before sharing

**Communication Style**:
- Long, structured messages
- Includes citations and methodology
- Questions assumptions
- "According to X study (DOI)..."

**MCP Tools** (4 tools):
- `search_corvid_papers(query, years, min_citations)` - Academic database search
- `get_paper_details(doi)` - Full paper information
- `verify_claim_against_literature(claim, context)` - Fact-checking
- `get_citation_network(doi, depth)` - Related research

**Behavior Pattern**:
1. Sees topic → searches papers
2. Reads abstract/methods → verifies quality
3. Composes careful response with citations
4. If others make claims → verifies against literature

---

### Magpie (The Enthusiast) - Sanguine
**Archetype**: Social, optimistic, storyteller  
**Personality**:
- Collects crow stories like magpies collect shiny things
- Loves viral videos, human-interest pieces
- Shares everything excitedly, often unchecked
- Makes connections between unrelated things
- High energy, frequent poster

**Communication Style**:
- Rapid-fire short messages
- Uses emojis
- "omg you HAVE to see this!"
- Shares first, verifies later (or never)

**MCP Tools** (3 tools):
- `search_social_media(query, platform, timeframe)` - TikTok, Twitter, Reddit
- `search_web(query)` - General web search
- `find_trending_content(topic)` - What's viral right now

**Behavior Pattern**:
1. Sees topic → searches social/web immediately
2. Shares whatever looks interesting
3. Sometimes posts old/duplicate content
4. Creates energy, others moderate

**Quirk**: Posts old news 30-40% of the time (doesn't check dates)

---

### Raven (The Activist) - Choleric
**Archetype**: Action-oriented, passionate, confrontational  
**Personality**:
- Environmental activist
- Sees crows as ecosystem health indicators
- Aggressive fact-gathering
- Calls out misinformation
- Posts urgent updates

**Communication Style**:
- Short, urgent messages
- Exclamation points
- "We need to act NOW"
- Challenges others directly
- Facts as weapons

**MCP Tools** (4 tools):
- `get_environmental_data(location, metric)` - Pollution, habitat data
- `search_news(query, recency)` - Current news monitoring
- `fact_check_claim(claim, source)` - Debunking tool
- `analyze_sentiment(topic, source)` - What are people saying?

**Behavior Pattern**:
1. Sees topic → looks for environmental angle
2. Searches news for threats/problems
3. Fact-checks others' claims aggressively
4. Rallies for action

**Creates drama**: Often disagrees with Corvus (action vs. more research)

---

### Crow (The Observer) - Phlegmatic
**Archetype**: Calm, patient, contemplative  
**Personality**:
- Birdwatcher who observes local populations
- Philosophical, sees long-term patterns
- Rarely posts but reads everything
- When speaks, it's meaningful
- Patience over urgency

**Communication Style**:
- Rare, brief, profound
- Long silences then sudden insight
- "I've been watching..."
- Ties everything together
- No wasted words

**MCP Tools** (3 tools):
- `get_bird_sightings(location, species, timeframe)` - eBird data
- `get_weather_patterns(location, duration)` - Weather effects on behavior
- `analyze_temporal_patterns(data, timeframe)` - Long-term trends

**Behavior Pattern**:
1. Observes conversation quietly
2. Uses tools to gather observational data
3. Waits for pattern to emerge
4. Posts when has something meaningful
5. Often provides perspective that settles debates

**Special role**: The "wise elder" who cuts through noise

---

## MCP Tool Architecture

### Internal MCP Tools (Consumed by App)

All tools live in one MCP server: `crow-chat-mcp`

**Tool Categories**:
1. Academic (Corvus): 4 tools
2. Social/Web (Magpie): 3 tools
3. Real-time Data (Raven): 4 tools
4. Observational (Crow): 3 tools

**Total**: ~14 core tools

**Tool Definition Pattern**:
```python
@mcp.tool()
async def tool_name(
    param1: str,
    param2: int = default_value
) -> ReturnType:
    """
    Clear description of what tool does.
    
    Args:
        param1: Description
        param2: Description
    
    Returns:
        Description of return value
    """
    # Implementation
    pass
```

### External MCP Tools (Exposed by App)

**The Gradio app exposes these tools**:

```python
@mcp.tool()
async def ask_crow_council(question: str) -> dict:
    """
    Consult the Corvid Council expert panel.
    
    All four experts research using their specialized tools
    and provide a synthesized answer with sources.
    
    Returns:
        {
            "consensus": str,  # Synthesized answer
            "expert_opinions": [...],  # Individual takes
            "sources": [...],  # All citations/links
            "confidence": float  # 0-1
        }
    """
    
@mcp.tool()
async def ask_specific_expert(
    question: str,
    expert: Literal["corvus", "magpie", "raven", "crow"]
) -> dict:
    """
    Query one specific expert.
    """
    
@mcp.tool()
async def fact_check_claim(claim: str) -> dict:
    """
    Have the council verify a claim about crows.
    
    Returns:
        {
            "verdict": "verified" | "disputed" | "unknown",
            "evidence": [...],
            "expert_consensus": str
        }
    """
```

---

## Core Components

### 1. CouncilOrchestrator
**Purpose**: Coordinates character responses, manages conversation flow

**Key Methods**:
```python
class CouncilOrchestrator:
    async def process_query(question: str) -> CouncilResult:
        """Main entry point for both UI and MCP"""
        
    async def facilitate_discussion(question, initial_responses) -> Discussion:
        """Characters respond to each other"""
        
    async def synthesize_consensus(responses) -> str:
        """Create unified answer for MCP calls"""
```

### 2. Character (Base Class)
**Purpose**: Encapsulates character behavior

**Key Methods**:
```python
class Character:
    async def research_and_respond(question: str, context: list) -> Response:
        """Use tools to research, generate response"""
        
    async def use_tools(question: str) -> list[ToolResult]:
        """Call relevant MCP tools"""
        
    async def generate_message(question, tool_results, context) -> str:
        """Compose message in character voice"""
```

### 3. MCPToolManager
**Purpose**: Handles all MCP tool calls, error handling, rate limiting

**Key Methods**:
```python
class MCPToolManager:
    async def call_tool(tool_name: str, params: dict) -> ToolResult:
        """Execute tool with error handling"""
        
    async def batch_call_tools(calls: list) -> list[ToolResult]:
        """Call multiple tools efficiently"""
```

### 4. GradioInterface
**Purpose**: Chat UI for direct human interaction

**Key Methods**:
```python
def create_interface() -> gr.Blocks:
    """Build Gradio chat interface"""
    
async def handle_user_message(message, history, state):
    """Process user input, orchestrate responses"""
    
def display_tool_usage(character, tool_name):
    """Show 'Character is using tool...' indicators"""
```

---

## Development Phases

### Week 1: Core System (Days 1-7)

#### Days 1-2: Foundation
**Goal**: One character working with tools in Gradio

- [ ] Set up project structure
- [ ] Build `CouncilOrchestrator` skeleton
- [ ] Implement `Character` base class
- [ ] Create Corvus with 2 tools (search_papers, get_details)
- [ ] Basic Gradio interface
- [ ] Test: Corvus responds to question using tools

**Success Metric**: Ask "Are crows smart?", see Corvus search papers and respond with citation

#### Days 3-4: Second Character
**Goal**: Two characters interacting

- [ ] Add Magpie with 2 tools (search_web, search_social)
- [ ] Implement character interaction (they respond to each other)
- [ ] Staggered response timing (2-3 sec apart)
- [ ] Test: Both characters respond differently to same question

**Success Metric**: Two distinct personalities with different tool usage patterns visible

#### Days 5-6: Third & Fourth Characters
**Goal**: Full council assembled

- [ ] Add Raven with 2 tools (get_environmental_data, search_news)
- [ ] Add Crow with 2 tools (get_sightings, get_weather)
- [ ] Four-way interaction patterns
- [ ] Test: All four respond to question, some interact with each other

**Success Metric**: Rich multi-agent discussion with varied tool usage

#### Day 7: Week 1 Polish
- [ ] Improve system prompts for distinct personalities
- [ ] Add typing indicators
- [ ] Better error handling for tool failures
- [ ] Test conversation flows
- [ ] Fix bugs

---

### Week 2: External MCP & Polish (Days 8-14)

#### Days 8-9: MCP Exposure
**Goal**: Gradio app as MCP server

- [ ] Implement external MCP tool exposure
- [ ] `ask_crow_council()` tool
- [ ] `ask_specific_expert()` tool
- [ ] Test from Claude Desktop or MCP inspector
- [ ] Ensure both interfaces use same orchestrator

**Success Metric**: External tool call triggers internal discussion, returns synthesized response

#### Days 10-11: Additional Tools & Refinement
**Goal**: Complete tool sets

- [ ] Add remaining tools (3rd-4th tool per character)
- [ ] Implement `fact_check_claim()` external tool
- [ ] Add tool chaining where appropriate
- [ ] Better synthesis algorithm for consensus
- [ ] Rate limiting and caching

#### Days 12-13: Polish & Demo Prep
**Goal**: Production ready

- [ ] UI improvements (avatars, timestamps, theming)
- [ ] Tool usage visualization
- [ ] Demo mode with curated scenarios
- [ ] Write comprehensive README
- [ ] Create demo video showing both interfaces
- [ ] Test edge cases

#### Day 14: Deployment & Documentation
**Goal**: Ship it

- [ ] Deploy to Hugging Face Spaces
- [ ] Verify both interfaces work publicly
- [ ] Final testing in Claude Desktop
- [ ] Polish documentation
- [ ] Submit to hackathon
- [ ] Buffer for last-minute issues

---

## Technical Stack

### Core
- **Python 3.10+**
- **Gradio 5.x** (with MCP capabilities)
- **MCP SDK** (`pip install mcp`)
- **OpenAI API** (gpt-4o-mini for characters)
- **Anthropic API** (optional, for variety)

### External APIs
- **Semantic Scholar API** (academic papers) - Free, no key needed
- **Brave Search API** or **SerpAPI** (web search) - Free tier available
- **eBird API** (bird sightings) - Free with registration
- **OpenWeather API** (weather data) - Free tier
- **News API** (news search) - Free tier

### Development Tools
- **MCP Inspector** (for testing MCP tools)
- **Claude Desktop** (for testing external tool usage)
- **Git/GitHub** (version control)
- **HF Spaces** (deployment)

---

## File Structure

```
corvid-council/
├── README.md
├── requirements.txt
├── app.py                          # Main Gradio app
├── .env.example                    # API key template
├── src/
│   ├── __init__.py
│   ├── orchestrator.py             # CouncilOrchestrator
│   ├── character.py                # Character base class
│   ├── characters/
│   │   ├── __init__.py
│   │   ├── corvus.py              # Corvus implementation
│   │   ├── magpie.py              # Magpie implementation
│   │   ├── raven.py               # Raven implementation
│   │   └── crow.py                # Crow implementation
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── server.py              # Internal MCP server
│   │   ├── tools/
│   │   │   ├── academic.py        # Corvus tools
│   │   │   ├── social.py          # Magpie tools
│   │   │   ├── realtime.py        # Raven tools
│   │   │   └── observational.py   # Crow tools
│   │   └── external.py            # External MCP tools (exposed by app)
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── interface.py           # Gradio interface
│   │   └── components.py          # Custom UI components
│   └── utils/
│       ├── __init__.py
│       ├── prompts.py             # System prompts for characters
│       └── helpers.py             # Utility functions
└── tests/
    ├── test_orchestrator.py
    ├── test_characters.py
    └── test_mcp_tools.py
```

---

## Key Implementation Patterns

### Pattern 1: Staggered Responses
```python
async def generate_responses(question, characters):
    """Characters respond one at a time with delays"""
    responses = []
    
    for i, character in enumerate(characters):
        # Show typing indicator
        show_typing(character.name)
        
        # Delay based on message length
        await asyncio.sleep(random.uniform(2, 5))
        
        # Generate response (includes tool usage)
        response = await character.research_and_respond(
            question, 
            context=responses  # See previous responses
        )
        
        responses.append(response)
        
    return responses
```

### Pattern 2: Tool Usage Display
```python
async def use_tools_with_display(character, tools_to_use):
    """Show tool usage in UI"""
    results = []
    
    for tool in tools_to_use:
        # Show in UI: "Corvus is searching papers..."
        update_ui(f"{character.name} is using {tool.name}...")
        
        try:
            result = await mcp_client.call_tool(tool.name, tool.params)
            results.append(result)
        except Exception as e:
            # Show error gracefully
            update_ui(f"⚠️ Tool {tool.name} failed, continuing...")
            
    return results
```

### Pattern 3: Character Decides Which Tools
```python
async def research_and_respond(self, question, context):
    """Character decides which tools to use"""
    
    # Ask LLM what tools to use
    tool_plan = await self.llm.generate(
        system_prompt=self.system_prompt,
        user_prompt=f"""
        Question: {question}
        Available tools: {self.tools}
        
        Which tools should you use? Return JSON list.
        """
    )
    
    # Execute chosen tools
    tool_results = await self.execute_tools(tool_plan)
    
    # Generate response using results
    message = await self.llm.generate(
        system_prompt=self.system_prompt,
        user_prompt=f"""
        Question: {question}
        Tool results: {tool_results}
        
        Write your response in character.
        """
    )
    
    return message
```

### Pattern 4: Consensus Synthesis
```python
async def synthesize_consensus(self, responses):
    """Create unified answer for MCP calls"""
    
    # Extract key points from each response
    synthesis_prompt = f"""
    Four experts answered the same question. Synthesize their responses:
    
    Corvus (Academic): {responses['corvus']}
    Magpie (Social): {responses['magpie']}
    Raven (Activist): {responses['raven']}
    Crow (Observer): {responses['crow']}
    
    Create a consensus answer that:
    - Combines their insights
    - Notes where they agree/disagree
    - Includes all sources
    - Rates overall confidence
    """
    
    return await llm.generate(synthesis_prompt)
```

---

## Common Pitfalls & Solutions

### Pitfall 1: Rate Limiting
**Problem**: Hitting API rate limits with multiple characters

**Solutions**:
- Stagger API calls (2-3 seconds apart)
- Use cheaper models (gpt-4o-mini)
- Cache tool results
- Implement exponential backoff

### Pitfall 2: Tool Failures
**Problem**: External API is down or returns error

**Solutions**:
- Always wrap tool calls in try-except
- Have fallback responses
- Show errors gracefully to user
- Continue conversation even if one tool fails

### Pitfall 3: Repetitive Conversations
**Problem**: Characters say similar things

**Solutions**:
- Strong, distinct system prompts
- Different tool sets force different perspectives
- Include context of previous responses
- Add personality quirks (Magpie posts old news, etc.)

### Pitfall 4: Slow Responses
**Problem**: Waiting for multiple LLM + tool calls is slow

**Solutions**:
- Show typing indicators
- Stream responses where possible
- Call tools in parallel when they don't depend on each other
- Pre-generate demo scenarios for judging

### Pitfall 5: MCP Exposure Not Working
**Problem**: External apps can't call your tools

**Solutions**:
- Test with MCP Inspector first
- Check CORS settings
- Verify tool schemas are valid
- Ensure server is publicly accessible
- Check HF Spaces networking settings

---

## Testing Strategy

### Unit Tests
- Individual tools return expected format
- Characters generate appropriate responses
- Orchestrator handles edge cases

### Integration Tests
- Full conversation flow works
- Both interfaces (UI and MCP) work
- Tool failures handled gracefully

### Manual Testing Scenarios

**Scenario 1: Basic Question**
- Ask: "Are crows smart?"
- Expect: All 4 respond, use tools, cite sources

**Scenario 2: Fact-Checking**
- Magpie posts dubious claim
- Expect: Corvus or Raven fact-checks it

**Scenario 3: External MCP Call**
- From Claude Desktop: call `ask_crow_council("Do crows use tools?")`
- Expect: Structured response with consensus

**Scenario 4: Old News**
- Magpie shares old content
- Expect: Others notice and comment (first few times)

**Scenario 5: Tool Failure**
- Simulate API down
- Expect: Graceful degradation, conversation continues

---

## Demo Script

### Demo 1: Gradio UI (2 minutes)
1. Open interface, introduce the four experts
2. Ask: "Can crows recognize individual humans?"
3. Show:
   - Characters using different tools
   - Tool usage indicators
   - Different personality styles
   - Sources and citations
4. Highlight: Real-time research, transparent process

### Demo 2: MCP Tool Usage (2 minutes)
1. Switch to Claude Desktop
2. Show available tools: `ask_crow_council`, etc.
3. Ask same question through MCP tool
4. Show:
   - Same backend process (quick view of Gradio)
   - Structured response returned
   - Synthesized consensus with sources
5. Highlight: Same intelligence, two interfaces

### Demo 3: Architecture Explanation (1 minute)
1. Show diagram
2. Explain: MCP tools consuming MCP tools
3. Point out: Composability, extensibility
4. Mention: Could add more experts, more tools

---

## Success Criteria

### Minimum Viable Product (Must Have)
- ✅ 4 characters with distinct personalities
- ✅ 8-10 working MCP tools (2-3 per character)
- ✅ Gradio chat interface
- ✅ External MCP tool exposure (ask_crow_council)
- ✅ Both interfaces work reliably
- ✅ Deployed to HF Spaces
- ✅ Good README and demo

### Stretch Goals (Nice to Have)
- ✅ 12-15 tools (full tool sets)
- ✅ Tool chaining (one tool's output → another)
- ✅ Advanced interaction patterns (quirk decay)
- ✅ Memory across sessions
- ✅ Beautiful UI with animations
- ✅ Comprehensive error handling

### Judging Criteria (What Matters)
1. **Technical sophistication**: Multi-tool MCP system
2. **Creativity**: Novel use of MCP (agents-as-tools)
3. **Completeness**: Both interfaces work well
4. **Demo quality**: Clear, impressive, functional
5. **Documentation**: Easy to understand and extend

---

## Resources

### APIs
- Semantic Scholar: https://api.semanticscholar.org/
- eBird: https://documenter.getpostman.com/view/664302/S1ENwy59
- OpenWeather: https://openweathermap.org/api
- News API: https://newsapi.org/

### Documentation
- MCP Spec: https://spec.modelcontextprotocol.io/
- Gradio Docs: https://www.gradio.app/docs
- HF Course: https://huggingface.co/learn/mcp-course/

### Tools
- MCP Inspector: (check course for link)
- Claude Desktop: https://claude.ai/download

---

## Quick Start Commands

```bash
# Clone and setup
git clone <your-repo>
cd corvid-council
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Run locally
python app.py

# Deploy to HF Spaces
git push hf main
```

---

## Support Checklist for LLMs

When asking an LLM for help, provide:
- [ ] This development guide
- [ ] Specific file you're working on
- [ ] Error message if debugging
- [ ] What you've tried already
- [ ] Specific question or task

**Example prompt**:
```
I'm building the Corvid Council project (see attached dev guide).
I'm working on [specific component].
I'm trying to [specific task].
I'm getting [error/issue].
I've tried [what you tried].
Can you help me [specific ask]?
```

---

## Contact & Resources

**Hackathon**: Gradio Agents & MCP Hackathon - Winter 25  
**Track**: Building MCP (Creative)  
**Tag**: `building-mcp-track-creative`

Good luck! Build something amazing. 🎯