# Change Log

**Date:** 2025-11-15

This document tracks notable changes in the "Corvid Council" repository.

---

### November 15, 2025

#### Summary of Changes

A code snippet related to a potential PubMed API implementation was added as comments to `src/cluas_mcp/common/api_clients.py`. No other functional or structural changes were observed in the repository. The core logic, file structure, and administrative files (`README.md`, `.gitignore`, `requirements.txt`) remain the same as the last review.

#### Detailed Changes

-   **Modified `src/cluas_mcp/common/api_clients.py`**:
    -   A block of commented-out Python code was added. This code demonstrates how to use the `Bio.Entrez` library to search PubMed for articles related to corvids, parse the results, and extract details like title, authors, abstract, and DOI.

#### Analysis

-   **Significant:**
    -   The change itself is minor (it's only comments), but it's significant in what it signals: active exploration of how to implement the `PubMedClient`. This is a direct move towards fulfilling one of the key requirements for making the `Corvus` character fully functional.

-   **Good:**
    -   This is a positive step. It shows that the next phase of development is being actively researched. The example code is relevant and provides a clear path for the real implementation.
    -   Using a well-known library like `BioPython` is a good choice for interacting with NCBI services.

-   **Concerning:**
    -   There are no concerns with this change. It's a healthy sign of a project in the early stages of development. The only minor point is that the code is commented out in the main source file rather than being in a separate experimental script, but this is a trivial issue at this stage.

---

### November 18, 2025

#### Summary of Changes

A new `notes_etc/` directory was added, containing detailed development guides and an architecture diagram. Crucially, the previously empty `src/cluas_mcp/common/formatting.py` file was implemented, fixing a critical import error.

#### Detailed Changes

-   **New Directory `notes_etc/`**:
    -   `development_guide_01.md`: A comprehensive guide detailing the project's concept, architecture, characters, MCP tools, development phases, and technical stack.
    -   `development_guide_02.txt`: A more concise version of the guide.
    -   `possible_lightweight_architecture_diagram.txt`: A text-based visualization of the system architecture.
-   **Modified `src/cluas_mcp/common/formatting.py`**:
    -   Implemented the `snippet_abstract` function to truncate text intelligently.
    -   Implemented the `format_authors` function to format author lists.

#### Analysis

-   **Significant:**
    -   The implementation of the functions in `formatting.py` is the most significant change, as it directly unblocks the `Corvus` agent and makes a core piece of the application runnable for the first time.
    -   The addition of the development guides provides invaluable context and a clear roadmap for the project's future.

-   **Good:**
    -   These changes are overwhelmingly positive. The bug fix is a major step forward, and the planning documents demonstrate a clear and well-thought-out vision for the project. The architecture is sound, and the character-based agent design is creative and well-defined.

-   **Concerning:**
    -   There are no concerning changes. The project is progressing logically and is now in a much better state than before. The next logical step is to implement the placeholder API clients.
