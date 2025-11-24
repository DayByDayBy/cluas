## Project Overview

This project, named "Cluas" or "Corvid Council," is a multi-agent AI research tool. It features a council of four AI "corvid" characters who collaborate to answer user questions. The project is built in Python using the Gradio framework for the user interface. Each character has a unique personality and access to a specific set of tools for information gathering.

The core components of the project are:

*   **`app.py`**: The main entry point of the application, which launches the Gradio UI.
*   **`src/gradio/app.py`**: Defines the Gradio user interface and the main chat logic.
*   **`src/characters/`**: Contains the implementation for each of the four AI characters (Corvus, Magpie, Raven, and Crow). Each character has its own module defining its personality, tools, and response generation logic.
*   **`src/cluas_mcp/`**: Implements the tools used by the characters. This includes modules for academic search (PubMed, ArXiv, Semantic Scholar), news search, and web search.

The application is designed to be a "dialectic research tool" where the AI agents can debate, synthesize information, and build upon past discussions.

## Building and Running

**1. Install Dependencies:**

The project uses `uv` for package management. To install the dependencies, run:

```bash
uv sync
```

i guess you could also do 

```
uv pip install -r requirements.txt
```

**2. Set up Environment Variables:**

The application requires API keys for the services it uses (e.g., Groq). Create a `.env` file in the root of the project and add the necessary API keys:

```
GROQ_API_KEY=your_groq_api_key
```

**3. Run the Application:**

To start the Gradio application, run:

```bash
python app.py
```

This will start a local web server, and you can access the application in your browser at the URL provided in the console.

**4. Running Tests:**

The project uses `pytest` for testing. The tests are located in the `tests/` directory.

To run all tests:

```bash
pytest
```

To run only tests that make live API calls:

```bash
uv run --prerelease=allow pytest -q tests/clients
```

To run only tests that do not make live API calls:
```bash
uv run --prerelease=allow pytest -q tests/clients/non_calling
```

## Development Conventions

*   **Modular Structure:** The codebase is organized into modules with specific responsibilities. The `characters` and `cluas_mcp` directories are good examples of this.
*   **Dependency Management:** Project dependencies are managed using `uv` and are listed in the `pyproject.toml` and `requirements.txt` files.
*   **Testing:** The project has a `tests` directory with unit and integration tests. `pytest` is the testing framework of choice.
*   **Environment Variables:** API keys and other sensitive information are managed through a `.env` file.
*   **Gradio for UI:** The user interface is built with the Gradio library.
