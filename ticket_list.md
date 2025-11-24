# Ticket List for Cluas

This document outlines suggested tasks to improve the Cluas project, aimed at a junior to mid-level engineer.

## Core Improvements

These tickets address foundational aspects of the project to improve its robustness, maintainability, and developer experience.

- **TICKET-01: Implement a Linter and Formatter**
  - **Description**: The project currently lacks automated code linting and formatting. Introduce a tool like `ruff` to enforce a consistent code style and catch potential errors.
  - **Tasks**:
    1. Add `ruff` to the project dependencies in `pyproject.toml`.
    2. Create a `ruff.toml` or `pyproject.toml` configuration file with basic rules.
    3. Run `ruff format .` and `ruff check --fix .` to format the existing codebase.
    4. Update the `README.md` with instructions on how to run the linter.

- **TICKET-02: Expand Test Coverage for Entrypoints**
  - **Description**: The `tests/integration` directory only contains tests for `academic_search_entrypoint`. Similar tests should be created for the other entrypoints to ensure they work as expected.
  - **Tasks**:
    1. Create `test_news_search_entrypoint.py` in `tests/integration/`.
    2. Create `test_observation_entrypoint.py` in `tests/integration/`.
    3. Create `test_web_search_entrypoint.py` in `tests/integration/`.
    4. Write basic integration tests for each entrypoint, mocking the external API calls.

- **TICKET-03: Add Type Hinting**
  - **Description**: While some parts of the code use type hints, many functions are missing them. Gradually adding type hints will improve code clarity and allow for static analysis.
  - **Tasks**:
    1. Start with the files in `src/cluas_mcp/common/` and add type hints to all function signatures and variables.
    2. Continue adding type hints to the entrypoint files in `src/cluas_mcp/`.

- **TICKET-04: Improve the README.md**
  - **Description**: The `README.md` provides a good overview, but it could be improved with more practical information for developers.
  - **Tasks**:
    1. Add an "Installation" section with instructions on how to set up the project and install dependencies (e.g., using `uv`).
    2. Add a "Running the Application" section that explains how to start the Gradio app.
    3. Add a "Running Tests" section that consolidates the test commands from the bottom of the file.

- **TICKET-05: Refactor or Remove `thing.py`**
  - **Description**: The file `src/cluas_mcp/academic/thing.py` seems to be a temporary or test script. It should be either removed or refactored into a meaningful module.
  - **Tasks**:
    1. Analyze the purpose of the `print` statement in `thing.py`.
    2. If it's a leftover test script, delete the file.
    3. If it serves a purpose, rename the file to something descriptive and integrate it properly.

## Further Ideas

These are suggestions for new features or major improvements that could be implemented after the core improvements are complete.

- **IDEA-01: Implement the Orchestrator**
  - **Description**: The `src/orchestrator.py` file is currently a placeholder. Implementing it would be the next major step towards the project's vision of a dialectic research tool.
  - **Tasks**:
    1. Design the `Orchestrator` class structure.
    2. Implement logic to pass user queries to the relevant characters.
    3. Develop a system for synthesizing responses from multiple characters.
    4. Integrate the orchestrator with the Gradio app.

- **IDEA-02: Create a Dockerfile**
  - **Description**: Containerizing the application with Docker would make it easier to deploy and run in a consistent environment.
  - **Tasks**:
    1. Create a `Dockerfile` that installs Python, copies the project files, and installs dependencies.
    2. Add a `docker-compose.yml` file for easier local development.

- **IDEA-03: Set Up a CI/CD Pipeline**
  - **Description**: A simple CI/CD pipeline (e.g., using GitHub Actions) could automatically run tests and linting on every push or pull request.
  - **Tasks**:
    1. Create a `.github/workflows/ci.yml` file.
    2. Define a workflow that runs `ruff check .` and `pytest`.
