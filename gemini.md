# Gemini Context: Corvid Council Project
    2 
    3 ## Project Overview
    4 - **Name**: Corvid Council (formerly "Cluas")
    5 - **Concept**: A multi-agent group chat where four AI crow
      experts (Corvus, Magpie, Raven, Crow) discuss topics using
      specialized MCP tools. The application has two interfaces: a
      Gradio chat UI for observing the discussion and an external
      MCP tool endpoint for programmatic queries.
    6 - **Goal**: To build this system for the Gradio Agents & MCP
      Hackathon.
    7 
    8 ## Current State & Key Components
    9 The project is in the very early stages of development,
      aligning with "Week 1: Days 1-2" of the development guide.
   10 
   11 - **`Corvus` Character**: A skeleton implementation exists in
      `src/characters/corvus.py`. It includes logic for searching
      academic papers with a fallback mechanism and integrates with
      the `AgentMemory` system.
   12 - **`AgentMemory`**: A foundational component (
      `src/cluas_mcp/common/memory.py`) has been created to act as
      a shared, persistent knowledge base for the agents. It
      replaces the earlier, simpler `CacheManager`.
   13 - **Supporting Files**: The repository includes a detailed
      `README.md` (acting as the development guide), a
      `requirements.txt` file, and a `.gitignore` file. A
      boilerplate `src/gradio/app.py` has also been added.
   14 
   15 ## Identified Issues & Blockers
   16 1.  **Broken `corvus.py` Import**: The file
      `src/cluas_mcp/common/formatting.py` is empty, which means
      the `format_authors` and `snippet_abstract` functions
      imported by `corvus.py` do not exist. This prevents the
      `Corvus` character from running.
   17 2.  **Missing Core Architecture**: Key components from the
      development guide are not yet implemented:
   18     -   `CouncilOrchestrator` class to manage the
      conversation.
   19     -   A `Character` base class.
   20     -   Integration between the Gradio UI and the agent
      logic.
   21 3.  **Incomplete File Structure**: The current file structure
      does not yet match the target structure outlined in the
      development guide (e.g., separation of tools into their own
      modules).
   22 4.  **Placeholder API Clients**: The `PubMedClient` and
      `SemanticScholarClient` are still stubs.
   23 
   24 ## Session State
   25 - **File System Access Lost**: The project's root directory
      was moved from `/Users/gboa/MCP-course-hf` to
      `/Users/gboa/cluas`. My environment is sandboxed to the
      original path, so I can no longer read from or write to any
      project files.