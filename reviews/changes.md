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

---

### November 18, 2025 (Afternoon)

#### Summary of Changes

Significant progress has been made on the API clients. The `ArxivClient` has been fully implemented, and the `PubMedClient` now has a functional search method that retrieves article IDs. More planning documents were also added.

#### Detailed Changes

-   **Modified `src/cluas_mcp/common/api_clients.py`**:
    -   **`ArxivClient`**: Now contains a full implementation. It builds a query, fetches data from the arXiv API, parses the Atom feed, and returns a list of structured dictionaries containing paper details.
    -   **`PubMedClient`**: A `pubmed_search` method has been implemented to perform the `esearch` step of the API interaction. It correctly builds a complex query and uses a helper method `parse_id_list` to extract PubMed IDs from the XML response. The `efetch` step is not yet implemented.
    -   **`SemanticScholarClient`**: Remains a placeholder.
-   **New Files in `notes_etc/`**:
    -   `possible_architecture_diagram.txt`: A more detailed architecture diagram.
    -   `possible_project_structure.txt`: A proposed target file structure.
    -   `exposing_cluas_as_an_MCP.py`: A code snippet showing how the app might expose MCP tools.

#### Analysis

-   **Significant:**
    -   The implementation of the `ArxivClient` and the first half of the `PubMedClient` is the most significant change. This represents the first major piece of core feature development, moving the project from planning and bug-fixing into active implementation.

-   **Good:**
    -   This is a huge step in the right direction. The code is functional and well-structured. The `Corvus` agent now has a working data source (arXiv) and a partially working one (PubMed). This directly addresses the main blocker and builds momentum.

-   **Concerning:**
    -   There are no concerning changes. The progress is excellent. The clear next step is to complete the `PubMedClient` by adding the `efetch` logic to retrieve full article data using the IDs from `pubmed_search`.

---

### November 18, 2025 (Late Afternoon)

#### Summary of Changes

A significant refactoring has occurred. The `PubMedClient` has been moved to a new `academic` submodule, and a robust, retry-enabled HTTP fetching utility has been created in `src/cluas_mcp/common/http.py`.

#### Detailed Changes

-   **New Directory `src/cluas_mcp/academic/`**:
    -   The `PubMedClient` has been moved to `src/cluas_mcp/academic/pubmed_client.py`.
-   **New File `src/cluas_mcp/common/http.py`**:
    -   This file introduces a `fetch_with_retry` function that uses the `tenacity` library to provide exponential backoff for HTTP requests. This makes API calls more resilient.
-   **Modified `src/cluas_mcp/academic/pubmed_client.py`**:
    -   The refactored `PubMedClient` now uses the new `fetch_with_retry` utility for its API calls.
-   **Modified `pyproject.toml`**:
    -   The `tenacity` library has been added as a project dependency.
-   **Modified `src/cluas_mcp/common/api_clients.py`**:
    -   This file still contains the old `PubMedClient` code, creating duplication.

#### Analysis

-   **Significant:**
    -   The architectural refactoring is highly significant. It shows a move towards a more organized, maintainable, and robust codebase, aligning with the project's planning documents. The creation of a shared, resilient HTTP utility is a major improvement.

-   **Good:**
    -   The new `http.py` module is excellent and demonstrates best practices for consuming external APIs.
    -   The file structure is becoming cleaner and more logical.

-   **Concerning:**
    -   **Code Duplication:** The most pressing issue is the duplicated `PubMedClient` code. The old implementation in `src/cluas_mcp/common/api_clients.py` is now obsolete and should be removed to prevent confusion and future bugs. The other clients in that file should also be refactored into their own modules.
