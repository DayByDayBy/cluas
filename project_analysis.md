# Project Analysis: Cluas

## Overview

**Cluas** is a Python-based multi-agent AI research tool designed for dialectic deliberation. The name "Cluas" is Gaelic for "ear," reflecting its purpose as a listening and information-gathering system. The project uses a "Corvid Council" of four AI agents (Corvus, Magpie, Raven, and Crow), each with a distinct persona and a specialized set of tools for research. The system facilitates a conversational research process where these agents can collaborate, debate, and build upon shared knowledge over time.

The primary interface is a web application built with Gradio, allowing users to interact with the council in two modes: a "Collaborative Mode" for synthesized answers and an "Active Mode" for direct participation in the discussion.

## Key Components

### 1. Application Core

- **`app.py`**: The main entry point for the Gradio web application.
- **`src/gradio/app.py`**: Contains the UI and logic for the Gradio chat interface. It manages the interaction between the user and the AI characters.
- **`src/orchestrator.py`**: This file is intended to be the central coordinator for the AI agents' interactions, managing the dialectic process, and handling shared memory. It is currently a placeholder, with the Gradio app handling basic orchestration.
- **`src/characters/`**: This directory defines the different AI agent personas:
    - `corvus.py`: The scholar, focused on academic research.
    - `magpie.py`: The enthusiast, skilled at finding trends and quick facts.
    - `raven.py`: The activist, focused on news and fact-checking.
    - `crow.py`: The observer, specializing in environmental and temporal patterns.

### 2. Tooling and Integrations (MCP - Multi-Component Platform)

- **`src/cluas_mcp/server.py`**: An MCP server that exposes the various research tools to the AI agents. This allows the agents to perform actions like searching academic papers, news, and the web.
- **`src/cluas_mcp/`**: This directory is organized by domain, with entry points for different types of searches:
    - **`academic/`**: Integrates with ArXiv, PubMed, and Semantic Scholar.
    - **`news/`**: Provides news search and claim verification.
    - **`web/`**: For general web searches and trending topics.
    - **`observation/`**: Connects to eBird for bird sighting data.
- **`src/cluas_mcp/common/`**: Contains shared utilities for API clients, caching, and data formatting.

### 3. Dependencies

- **`pyproject.toml` & `requirements.txt`**: Define the project dependencies. Key libraries include:
    - `gradio`: For the web UI.
    - `fastmcp` & `mcp`: For the multi-agent communication and tool-serving framework.
    - `groq`: Likely for interacting with a large language model API.
    - `feedparser`, `requests`, `tenacity`: For fetching data from external APIs and web sources.
    - `pytest`: For testing.

### 4. Testing

- **`tests/`**: The project has a testing suite with `pytest`.
    - **`clients/`**: Contains tests for the various API clients (ArXiv, PubMed, etc.), with both live and mocked tests.
    - **`integration/`**: Includes integration tests for the search entry points.

## Analysis Summary

The project is well-structured, with a clear separation of concerns between the UI (Gradio), the agent personas (characters), and the tool implementations (MCP). The use of a multi-agent system is a sophisticated approach to research, allowing for a more robust and nuanced exploration of topics.

The `orchestrator.py` file indicates a plan for a more advanced system that can manage complex interactions and a persistent shared memory, which is the core of the "dialectic" process described in the README.

The file `src/cluas_mcp/academic/thing.py` appears to be a temporary or test file and should be reviewed.

Overall, Cluas is an ambitious and interesting project with a solid foundation. The immediate next steps would likely involve implementing the `orchestrator.py` to realize the full vision of a dialectic research tool.
